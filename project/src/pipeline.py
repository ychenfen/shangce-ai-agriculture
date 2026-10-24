"""Deterministic chronological backtest. Run from root: python -m src.pipeline."""
from pathlib import Path
import json, time, platform
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.agro import reference_et, recommend, bucket_step, crop_coefficient

ROOT=Path(__file__).resolve().parents[1]
SITES={'shijiazhuang':('石家庄',38.04,114.51),'zhengzhou':('郑州',34.75,113.62),'jinan':('济南',36.65,117.12)}
PARAMS=['tmean','tmax','tmin','rh','wind10','rain','solar','pressure']

def load_weather():
    frames=[]; audits=[]
    for site,(name,lat,lon) in SITES.items():
        raw=json.loads((ROOT/f'inputs/weather/{site}.json').read_text())
        rename=dict(zip(['temperature_2m_mean','temperature_2m_max','temperature_2m_min','relative_humidity_2m_mean','wind_speed_10m_mean','precipitation_sum','shortwave_radiation_sum','surface_pressure_mean','et0_fao_evapotranspiration'],PARAMS+['et0']))
        d=pd.DataFrame(raw['daily']).rename(columns=rename).set_index('time')
        d.index=pd.to_datetime(d.index); d.index.name='date'
        # Missing observations are removed only after lag construction; no backward fill.
        d=d.reindex(pd.date_range('2018-01-01','2025-12-31'))
        d=d.mask(d<=-900)
        if not (d.tmax>=d.tmin).all(): raise ValueError('temperature order')
        if not (d.rh.between(0,100)&d.wind10.ge(0)&d.rain.ge(0)&d.et0.ge(0)).all(): raise ValueError('invalid weather')
        assert raw['daily_units']['shortwave_radiation_sum']=='MJ/m²'
        assert raw['daily_units']['surface_pressure_mean']=='hPa'
        assert raw['daily_units']['wind_speed_10m_mean']=='m/s'
        d['site']=site; d['lat']=lat; d['lon']=lon
        d['date']=d.index; d.index.name=None
        frames.append(d.reset_index(drop=True))
        audits.append(dict(site=site,rows=len(d),missing_cells=int(d[PARAMS+['et0']].isna().sum().sum()),requested_lat=lat,requested_lon=lon,returned_lat=raw['latitude'],returned_lon=raw['longitude'],elevation=raw['elevation'],units=raw['daily_units'],source='Open-Meteo ERA5; provider-calculated FAO ET0'))
    return pd.concat(frames,ignore_index=True),audits

def features(weather):
    all_frames=[]
    for site,d in weather.groupby('site',sort=True):
        d=d.sort_values('date').copy()
        d['sin']=np.sin(2*np.pi*d.date.dt.dayofyear/365.25); d['cos']=np.cos(2*np.pi*d.date.dt.dayofyear/365.25)
        # 每行日期为预测目标日，只使用该日之前的历史数据
        for col in PARAMS+['et0']:
            for lag in [1,2,3,7]: d[f'{col}_lag{lag}']=d[col].shift(lag)
            d[f'{col}_mean7']=d[col].shift(1).rolling(7,min_periods=7).mean()
        d['latest_input_date']=d.date-pd.Timedelta(days=1)
        all_frames.append(d)
    result=pd.concat(all_frames,ignore_index=True)
    cols=['sin','cos','lat','lon']+[c for c in result if '_lag' in c or '_mean7' in c]
    return result.dropna(subset=cols+['et0']).reset_index(drop=True),cols

def new_model(seed=42):
    return HistGradientBoostingRegressor(max_iter=180,learning_rate=.055,max_leaf_nodes=15,l2_regularization=8,min_samples_leaf=25,early_stopping=False,random_state=seed)

def metrics(y,pred):
    return dict(n=len(y),mae=float(mean_absolute_error(y,pred)),rmse=float(np.sqrt(mean_squared_error(y,pred))),r2=float(r2_score(y,pred)))

def conformal_q(errors,coverage=.9):
    rank=min(len(errors),int(np.ceil((len(errors)+1)*coverage)))
    return float(np.sort(errors)[rank-1])

def run():
    started=time.perf_counter()
    weather,audits=load_weather(); data,cols=features(weather)
    train=data[data.date<'2023-01-01']; cal=data[data.date.between('2023-01-01','2023-12-31')]; test=data[data.date>='2024-01-01'].copy()
    assert train.date.max()<cal.date.min()<cal.date.max()<test.date.min()
    model=new_model(); model.fit(train[cols],train.et0)
    pred_cal=np.maximum(0,model.predict(cal[cols])); test['ai']=np.maximum(0,model.predict(test[cols]))
    # Calibration only, pooled across sites. No test-set tuning.
    q=conformal_q(abs(cal.et0.to_numpy()-pred_cal))
    test['lower']=np.maximum(0,test.ai-q);test['upper']=test.ai+q
    climatology=train.groupby(['site',train.date.dt.month]).et0.mean().to_dict()
    test['climatology']=[climatology[(s,m)] for s,m in zip(test.site,test.date.dt.month)]
    test['persistence']=test.et0_lag1
    seasonal_cols=['sin','cos','lat','lon']
    seasonal=new_model().fit(train[seasonal_cols],train.et0)
    test['calendar_only']=np.maximum(0,seasonal.predict(test[seasonal_cols]))
    raw_cols=[c for c in cols if not c.startswith('et0_')]
    ablated=new_model().fit(train[raw_cols],train.et0)
    test['no_et_history']=np.maximum(0,ablated.predict(test[raw_cols]))
    scores={k:metrics(test.et0,test[k]) for k in ['climatology','persistence','calendar_only','no_et_history','ai']}
    site_scores={s:{k:metrics(d.et0,d[k]) for k in scores} for s,d in test.groupby('site')}
    # 14-day blocks preserving cross-site dependence; exploratory bootstrap, 1000 reps.
    diff=test.assign(diff=abs(test.et0-test.persistence)-abs(test.et0-test.ai)).groupby('date')['diff'].mean().to_numpy()
    blocks=[diff[i:i+14] for i in range(0,len(diff),14)]; rng=np.random.default_rng(42)
    means=[float(np.concatenate([blocks[j] for j in rng.integers(0,len(blocks),len(blocks))]).mean()) for _ in range(1000)]
    ci=np.quantile(means,[.025,.975]).tolist()
    # Leave one location out, no held-location rows in training or calibration.
    transfer={}
    for site in SITES:
        tr=train[train.site!=site]; ca=cal[cal.site!=site]; te=test[test.site==site]
        tm=new_model().fit(tr[cols],tr.et0); cp=np.maximum(0,tm.predict(ca[cols])); tp=np.maximum(0,tm.predict(te[cols])); tq=conformal_q(abs(ca.et0.to_numpy()-cp))
        transfer[site]={**metrics(te.et0,tp),'coverage':float(np.mean((te.et0>=np.maximum(0,tp-tq))&(te.et0<=tp+tq))),'persistence_mae':metrics(te.et0,te.persistence)['mae']}
    intervals={s:dict(coverage=float(((d.et0>=d.lower)&(d.et0<=d.upper)).mean()),width=float((d.upper-d.lower).mean())) for s,d in test.groupby('site')}
    intervals['all']=dict(coverage=float(((test.et0>=test.lower)&(test.et0<=test.upper)).mean()),width=float((test.upper-test.lower).mean()))
    benchmark=[]
    for _ in range(50):
        t=time.perf_counter();model.predict(test[cols].iloc[:1]); benchmark.append((time.perf_counter()-t)*1000)
    bundle=dict(model=model,features=cols,q=q,train_end='2022-12-31',calibration_end='2023-12-31')
    joblib.dump(bundle,ROOT/'models/shangce.joblib')
    weather.to_csv(ROOT/'results/weather_daily.csv',index=False,float_format='%.8f')
    test.to_csv(ROOT/'results/predictions.csv',index=False,float_format='%.8f')
    sim=simulate(test)
    summary=dict(title='墒策：可信需水预测与灌溉决策',splits={'train':len(train),'calibration':len(cal),'test':len(test)},data_audit=audits,metrics=scores,sites=site_scores,transfer=transfer,interval=intervals,q90=q,mae_improvement_pct=100*(1-scores['ai']['mae']/scores['persistence']['mae']),paired_mae_difference_ci95=ci,inference_median_ms=float(np.median(benchmark)),simulation=sim,elapsed_s=time.perf_counter()-started,environment={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__})
    (ROOT/'results/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k not in ['data_audit','sites','simulation']},ensure_ascii=False,indent=2))

def simulate(test):
    daily=[];scenarios=[]
    for (site,year),d in test.groupby(['site',test.date.dt.year]):
        d=d[d.date.dt.month.between(5,9)]
        for taw in [80,120,160]:
            for eta in [.7,.85]:
                for policy in ['calendar','sensor','persistence','ai','upper']:
                    deficit=taw*.35; rows=[]
                    for i,r in enumerate(d.itertuples()):
                        kc=crop_coefficient(r.date.month,r.date.day)
                        if policy=='calendar':gross=25 if i%7==0 else 0
                        elif policy=='sensor':gross=min(40,max(0,deficit-taw*.25)/eta) if deficit>taw*.5 else 0
                        else:gross=recommend(deficit,taw,eta,40,getattr(r,policy),kc)['gross_mm']
                        end=bucket_step(deficit,kc*r.et0,r.rain,gross,eta,taw)
                        row=dict(site=site,year=year,taw=taw,eta=eta,policy=policy,date=str(r.date.date()),initial_deficit=deficit,gross_mm=gross,et_mm=kc*r.et0,rain_mm=r.rain,end_deficit=end['deficit'],stress=int(end['deficit']>taw*.5),drainage=end['drainage'],unmet=end['unmet'])
                        rows.append(row); deficit=end['deficit']
                    daily+=rows
                    scenarios.append(dict(site=site,year=year,taw=taw,eta=eta,policy=policy,irrigation_mm=sum(x['gross_mm'] for x in rows),stress_days=sum(x['stress'] for x in rows),drainage_mm=sum(x['drainage'] for x in rows),unmet_mm=sum(x['unmet'] for x in rows)))
    df=pd.DataFrame(scenarios);df.to_csv(ROOT/'results/simulation_scenarios.csv',index=False)
    pd.DataFrame(daily).to_csv(ROOT/'results/simulation_daily.csv',index=False,float_format='%.6f')
    central=df[(df.taw==120)&(df.eta==.85)].groupby('policy')[['irrigation_mm','stress_days','drainage_mm','unmet_mm']].mean().round(4).to_dict('index')
    return dict(central=central,scenario_count=len(df),assumptions={'season':'May-Sep','taw_mm':[80,120,160],'eta':[.7,.85],'raw_fraction':.5,'refill_target_fraction':.25,'rain_effective_fraction':.8,'cap_mm_day':40,'initial_deficit_fraction':.35},warning='简化土壤水桶仿真；没有田间产量、土壤传感器或实测节水证据。')

if __name__=='__main__':run()
