"""Local historical replay, model inference and explainable decision service."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pandas as pd
import joblib
from src.agro import recommend,crop_coefficient

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'app'),**kw)
    def send_json(self,obj,status=200):
        b=json.dumps(obj,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
    def do_GET(self):
        route=urlparse(self.path)
        if route.path=='/api/summary':return self.send_json(SUMMARY)
        if route.path=='/api/forecast':
            try:
                args=parse_qs(route.query);site=args.get('site',['shijiazhuang'])[0];date=args.get('date',['2025-07-15'])[0]
                d=DATA[(DATA.site==site)&(DATA.date==date)]
                if len(d)!=1:raise ValueError('仅支持三地 2024—2025 年历史回放')
                row=d.iloc[0]; pred=max(0,float(BUNDLE['model'].predict(d[BUNDLE['features']])[0]));q=BUNDLE['q']
                hist=DATA[(DATA.site==site)&(DATA.date<=date)].tail(90)
                return self.send_json(dict(site=site,date=date,input_end=str(row.latest_input_date)[:10],prediction=pred,lower=max(0,pred-q),upper=pred+q,reference=float(row.et0),persistence=float(row.persistence),kc=crop_coefficient(int(date[5:7]),int(date[8:10])),history=hist[['date','et0','ai','lower','upper']].to_dict('records'),mode='历史回放；目标日参考值仅用于事后评价'))
            except (ValueError,KeyError) as e:return self.send_json({'error':str(e)},400)
        if route.path.startswith('/api/'):return self.send_json({'error':'接口不存在'},404)
        return super().do_GET()
    def do_POST(self):
        if self.path!='/api/recommend':return self.send_json({'error':'接口不存在'},404)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>10000:raise ValueError('请求过大')
            p=json.loads(self.rfile.read(n)); site=p['site'];date=p['date']
            row=DATA[(DATA.site==site)&(DATA.date==date)]
            if len(row)!=1:raise ValueError('日期或地区超出历史回放范围')
            mean=max(0,float(BUNDLE['model'].predict(row[BUNDLE['features']])[0]));upper=mean+BUNDLE['q']
            mode=p.get('mode','upper')
            if mode not in ['mean','upper']:raise ValueError('策略无效')
            chosen=upper if mode=='upper' else mean
            args={k:float(p[k]) for k in ['deficit','taw','eta','cap','kc']}
            result=recommend(**args,et=chosen)
            return self.send_json(dict(**result,site=site,date=date,mode=mode,et0_mm=chosen,mean_et0_mm=mean,upper_et0_mm=upper,inputs=args,model_train_end=BUNDLE['train_end'],calibration_end=BUNDLE['calibration_end'],note='田间参数由使用者输入；建议未扣除当日降雨，执行前请人工确认。'))
        except (ValueError,KeyError,TypeError) as e:return self.send_json({'error':str(e)},400)

if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('--port',type=int,default=8765);opts=args.parse_args()
    BUNDLE=joblib.load(ROOT/'models/shangce.joblib');DATA=pd.read_csv(ROOT/'results/predictions.csv');SUMMARY=json.loads((ROOT/'results/summary.json').read_text())
    server=ThreadingHTTPServer(('127.0.0.1',opts.port),Handler)
    print(f'墒策历史回放 http://127.0.0.1:{opts.port}',flush=True);server.serve_forever()
