"""Additional descriptive analysis for the LaTeX report; no model refitting."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper'; (OUT/'figures').mkdir(parents=True,exist_ok=True); (OUT/'tables').mkdir(exist_ok=True)
FP=FontProperties(fname='/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
plt.rcParams.update({'font.family':FP.get_name(),'font.size':10,'axes.spines.top':False,
 'axes.spines.right':False,'axes.edgecolor':'#929b91','axes.labelcolor':'#243e34',
 'xtick.color':'#576259','ytick.color':'#576259','pdf.fonttype':42,
 'axes.unicode_minus':False,'savefig.bbox':'tight'})
GREEN='#315642'; BROWN='#b0774f';GRAY='#9da89a';BLUE='#5f7d91'
NAMES={'jinan':'济南','shijiazhuang':'石家庄','zhengzhou':'郑州'}
PN={'calendar':'定额日历','sensor':'墒情阈值','persistence':'昨日值','ai':'AI点预测','upper':'AI上界'}
POL=['calendar','sensor','persistence','ai','upper']
s=json.loads((ROOT/'results/summary.json').read_text())
p=pd.read_csv(ROOT/'results/predictions.csv',parse_dates=['date'])
w=pd.read_csv(ROOT/'results/weather_daily.csv',parse_dates=['date'])
sim=pd.read_csv(ROOT/'results/simulation_scenarios.csv')
daily=pd.read_csv(ROOT/'results/simulation_daily.csv',parse_dates=['date'])
p['error']=p.ai-p.et0;p['abs_error']=p.error.abs();p['baseline_abs']=(p.persistence-p.et0).abs()
p['covered']=p.et0.between(p.lower,p.upper);p['width']=p.upper-p.lower
p['month']=p.date.dt.month;p['year']=p.date.dt.year

def table(name,headers,rows,align=None):
    if align is None:align='l'+'r'*(len(headers)-1)
    content=[r'\begin{tabular}{'+align+'}',r'\toprule',' & '.join(headers)+r' \\',r'\midrule']
    content += [' & '.join(map(str,row))+r' \\' for row in rows]
    content += [r'\bottomrule',r'\end{tabular}']
    (OUT/'tables'/f'{name}.tex').write_text('\n'.join(content))

def save(name):
    plt.savefig(OUT/'figures'/f'{name}.pdf');plt.savefig(OUT/'figures'/f'{name}.png',dpi=150);plt.close()

monthly=p.groupby('month').agg(n=('et0','size'),mae=('abs_error','mean'),baseline_mae=('baseline_abs','mean'),bias=('error','mean'),coverage=('covered','mean'),width=('width','mean'))
monthly.to_csv(ROOT/'results/report_monthly.csv')
table('monthly',['月份','$n$','模型MAE','昨日值MAE','偏差','覆盖率'],[[m,int(r.n),f'{r.mae:.3f}',f'{r.baseline_mae:.3f}',f'{r.bias:.3f}',f'{100*r.coverage:.2f}\\%'] for m,r in monthly.iterrows()])
sy=p.groupby(['site','year']).agg(n=('et0','size'),mae=('abs_error','mean'),baseline_mae=('baseline_abs','mean'),bias=('error','mean'),coverage=('covered','mean'))
sy.to_csv(ROOT/'results/report_site_year.csv')
table('site_year',['地区','年份','$n$','模型MAE','昨日值MAE','覆盖率'],[[NAMES[k[0]],k[1],int(r.n),f'{r.mae:.3f}',f'{r.baseline_mae:.3f}',f'{100*r.coverage:.2f}\\%'] for k,r in sy.iterrows()],align='llrrrr')
worst=p.nlargest(8,'abs_error');worst[['site','date','et0','ai','persistence','error','lower','upper']].to_csv(ROOT/'results/report_worst.csv',index=False)
table('worst',['地区','日期','参考值','预测值','昨日值','误差'],[[NAMES[r.site],r.date.strftime('%Y-%m-%d'),f'{r.et0:.2f}',f'{r.ai:.2f}',f'{r.persistence:.2f}',f'{r.error:+.2f}'] for r in worst.itertuples()],align='llrrrr')
table('overall',['方法','MAE','RMSE','$R^2$'],[[{'ai':'完整模型','persistence':'昨日值','climatology':'地区月均值','calendar_only':'日期与位置','no_et_history':'去除历史蒸散'}[k],f'{v["mae"]:.4f}',f'{v["rmse"]:.4f}',f'{v["r2"]:.4f}'] for k,v in s['metrics'].items()])
table('transfer',['留出地区','模型MAE','昨日值MAE','覆盖率'],[[NAMES[k],f'{v["mae"]:.4f}',f'{v["persistence_mae"]:.4f}',f'{v["coverage"]*100:.2f}\\%'] for k,v in s['transfer'].items()])
table('central',['策略','灌溉量/mm','风险日/日','排水量/mm'],[[PN[k],f'{v["irrigation_mm"]:.2f}',f'{v["stress_days"]:.2f}',f'{v["drainage_mm"]:.2f}'] for k in POL for v in [s['simulation']['central'][k]]])
sens=sim.groupby(['taw','eta','policy'])[['irrigation_mm','stress_days','drainage_mm','unmet_mm']].mean()
sens.to_csv(ROOT/'results/report_sensitivity.csv')
table('sensitivity',['TAW',r'$\eta$','策略','灌溉量/mm','风险日/日'],[[k[0],f'{k[1]:.2f}',PN[k[2]],f'{r.irrigation_mm:.2f}',f'{r.stress_days:.2f}'] for k,r in sens.iterrows()],align='rrlrr')
ct=sim[(sim.taw==120)&(sim.eta==.85)]
table('six_seasons',['地区','年份','点预测用水','上界用水','点预测风险','上界风险'],[[NAMES[site],year,*[f'{g.set_index("policy").loc[k,col]:.2f}' for col in ['irrigation_mm','stress_days'] for k in ['ai','upper']]] for (site,year),g in ct.groupby(['site','year'])],align='llrrrr')
paired=sim.pivot(index=['site','year','taw','eta'],columns='policy',values=['irrigation_mm','stress_days'])
comparison={}
for ref in ['sensor','persistence','ai']:
    dw=paired['irrigation_mm']['upper']-paired['irrigation_mm'][ref]
    ds=paired['stress_days']['upper']-paired['stress_days'][ref]
    comparison[ref]={'n':len(dw),'water_difference_mean':float(dw.mean()),'risk_difference_mean':float(ds.mean()),'risk_lower_count':int((ds<0).sum()),'risk_equal_count':int((ds==0).sum()),'risk_higher_count':int((ds>0).sum())}
table('paired',['上界减参照','平均水差/mm','平均风险差/日','风险减少/相同/增加'],[[PN[k],f'{v["water_difference_mean"]:+.2f}',f'{v["risk_difference_mean"]:+.2f}',f'{v["risk_lower_count"]}/{v["risk_equal_count"]}/{v["risk_higher_count"]}'] for k,v in comparison.items()],align='lrrl')

fig,axs=plt.subplots(2,1,figsize=(9,5.4),sharex=True)
for site,d in w.groupby('site'):
    m=d.groupby(d.date.dt.month).agg(et0=('et0','mean'),rain=('rain','mean'))
    axs[0].plot(m.index,m.et0,marker='o',ms=3,label=NAMES[site]);axs[1].plot(m.index,m.rain,marker='o',ms=3)
axs[0].set_ylabel('参考ET₀ / mm·日⁻¹');axs[1].set_ylabel('日均降雨 / mm');axs[1].set_xlabel('月份');axs[1].set_xticks(range(1,13));axs[0].legend(ncol=3,frameon=False);fig.tight_layout();save('climate')
fig,axs=plt.subplots(1,2,figsize=(9,3.9))
axs[0].scatter(p.et0,p.ai,s=6,alpha=.28,color=GREEN,rasterized=True);axs[0].plot([0,11],[0,11],c=BROWN,lw=1);axs[0].set(xlabel='参考ET₀ / mm·日⁻¹',ylabel='预测ET₀ / mm·日⁻¹',xlim=(0,11),ylim=(0,11))
axs[1].hist(p.error,bins=38,color=GREEN,alpha=.85);axs[1].axvline(0,c=BROWN,lw=1);axs[1].set(xlabel='预测减参考 / mm·日⁻¹',ylabel='样本数');fig.tight_layout();save('residual')
fig,axs=plt.subplots(2,1,figsize=(9,5.3),sharex=True)
axs[0].plot(monthly.index,monthly.mae,'o-',color=GREEN,label='完整模型');axs[0].plot(monthly.index,monthly.baseline_mae,'o--',color=GRAY,label='昨日值');axs[0].set_ylabel('MAE / mm·日⁻¹');axs[0].legend(ncol=2,frameon=False)
axs[1].bar(monthly.index,monthly.coverage*100,color=[BROWN if v<.9 else GRAY for v in monthly.coverage]);axs[1].axhline(90,c=GREEN,ls='--',lw=1);axs[1].set(ylabel='经验覆盖率 / %',xlabel='月份',ylim=(65,102));axs[1].set_xticks(range(1,13));fig.tight_layout();save('seasonality')
fig,ax=plt.subplots(figsize=(9,3.2))
mat=p.groupby(['site','month']).covered.mean().unstack().loc[list(NAMES)]*100
im=ax.imshow(mat,cmap='YlGn',vmin=65,vmax=100,aspect='auto');ax.set_xticks(range(12),range(1,13));ax.set_yticks(range(3),[NAMES[k] for k in mat.index]);ax.set_xlabel('月份')
for i in range(3):
 for j in range(12):ax.text(j,i,f'{mat.iloc[i,j]:.0f}',ha='center',va='center',fontsize=9,color='white' if mat.iloc[i,j]>87 else '#243c31')
fig.colorbar(im,ax=ax,label='覆盖率 / %');fig.tight_layout();save('coverage_heatmap')
fig,axs=plt.subplots(2,1,figsize=(9,5.1),sharex=True)
case=p[(p.site=='zhengzhou')&p.date.between('2024-06-08','2024-06-23')]
axs[0].fill_between(case.date,case.lower,case.upper,color='#dce7d7',label='名义90%区间');axs[0].plot(case.date,case.ai,color=GREEN,label='模型预测');axs[0].plot(case.date,case.et0,color=BROWN,marker='o',ms=3,label='参考值');axs[0].set_ylabel('ET₀ / mm·日⁻¹');axs[0].legend(ncol=3,frameon=False)
axs[1].bar(case.date,case.rain,color=BLUE);axs[1].set_ylabel('实际降水 / mm');axs[1].set_xlabel('2024年6月（降水仅作事后解释）');fig.autofmt_xdate();fig.tight_layout();save('failure_case')
fig,ax=plt.subplots(figsize=(9,4.1))
for k,col in zip(POL,[GRAY,BROWN,BLUE,GREEN,'#172d22']):
 d=sim[sim.policy==k];ax.scatter(d.irrigation_mm,d.stress_days,s=22,c=col,alpha=.55,label=PN[k])
ax.set(xlabel='单季毛灌溉量 / mm',ylabel='单季风险日 / 日');ax.legend(ncol=3,frameon=False);fig.tight_layout();save('tradeoff_all')
fig,axs=plt.subplots(1,2,figsize=(9,4))
for k,c in zip(POL,[GRAY,BROWN,BLUE,GREEN,'#172d22']):
 vals=sens.xs(.85,level='eta').xs(k,level='policy');axs[0].plot(vals.index,vals.irrigation_mm,'o-',color=c,label=PN[k]);axs[1].plot(vals.index,vals.stress_days,'o-',color=c)
axs[0].set(ylabel='季均毛灌溉量 / mm',xlabel='TAW / mm');axs[1].set(ylabel='季均风险日 / 日',xlabel='TAW / mm');axs[0].legend(frameon=False,fontsize=8);fig.tight_layout();save('soil_sensitivity')
fig,axs=plt.subplots(2,1,figsize=(9,5.3),sharex=True)
d=daily[(daily.site=='zhengzhou')&(daily.year==2024)&(daily.taw==120)&(daily.eta==.85)]
for k,c in [('sensor',BROWN),('ai',GREEN),('upper',BLUE)]:
 q=d[d.policy==k];axs[0].plot(q.date,q.end_deficit,color=c,lw=1,label=PN[k]);axs[1].plot(q.date,q.gross_mm.cumsum(),color=c,label=PN[k])
axs[0].axhline(60,ls='--',c=GRAY,lw=1);axs[0].set_ylabel('日末亏缺 / mm');axs[0].legend(ncol=3,frameon=False);axs[1].set_ylabel('累计毛灌溉 / mm');fig.autofmt_xdate();fig.tight_layout();save('season_trace')
fig,ax=plt.subplots(figsize=(9,3.7))
annual=w.groupby([w.date.dt.year,'site']).et0.mean().unstack()
for site in annual:ax.plot(annual.index,annual[site],marker='o',ms=4,label=NAMES[site])
ax.axvspan(2022.5,2023.5,color='#e8e6da',label='校准年');ax.axvspan(2023.5,2025.5,color='#dce7d7',label='测试年');ax.set(xlabel='年份',ylabel='全年日均参考ET₀ / mm·日⁻¹',xlim=(2017.8,2025.5));ax.legend(ncol=5,fontsize=8,frameon=False);fig.tight_layout();save('annual')


rows=(OUT/'tables/sensitivity.tex').read_text().splitlines()[4:-2]
longtable=r'''\begin{longtable}{rrlrr}
\caption{全部容量与效率组合的六季平均结果}\label{tab:allsensitivity}\\\toprule
TAW/mm & $\eta$ & 策略 & 毛用水/mm & 风险日/日\\\midrule\endfirsthead
\toprule TAW/mm & $\eta$ & 策略 & 毛用水/mm & 风险日/日\\\midrule\endhead
'''+ '\n'.join(rows) + '\n'+r'''\bottomrule
\end{longtable}
'''
(OUT/'tables/sensitivity_longtable.tex').write_text(longtable)

stats={'global_bias':float(p.error.mean()),'absolute_error_quantiles':p.abs_error.quantile([.5,.9,.95,.99]).to_dict(),
       'model_beats_persistence_fraction':float((p.abs_error<p.baseline_abs).mean()),
       'below_interval':int((p.et0<p.lower).sum()),'above_interval':int((p.et0>p.upper).sum()),
       'paired_policy_comparison':comparison,'analysis_scope':'Post-hoc descriptive diagnostics; no tuning or retraining.'}
(ROOT/'results/report_analysis.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
print(json.dumps(stats,ensure_ascii=False,indent=2))
