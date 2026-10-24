import math
import numpy as np
import pandas as pd
import pytest
from src.agro import reference_et,recommend,bucket_step
from src.pipeline import features,conformal_q,load_weather

def test_reference_et_known_arithmetic():
    # Independent scalar evaluation of the same specified equation and units.
    t,hi,lo,rh,u,rs,p,lat,j,z=20.,25.,15.,60.,2.,20.,100.,35.,180,100.
    phi=math.radians(lat);dec=.409*math.sin(2*math.pi*j/365-1.39)
    ws=math.acos(-math.tan(phi)*math.tan(dec))
    ra=1440/math.pi*.082*(1+.033*math.cos(2*math.pi*j/365))*(ws*math.sin(phi)*math.sin(dec)+math.cos(phi)*math.cos(dec)*math.sin(ws))
    es=sum(.6108*math.exp(17.27*x/(x+237.3)) for x in [hi,lo])/2;ea=.6*es
    rnl=4.903e-9*((hi+273.16)**4+(lo+273.16)**4)/2*(.34-.14*math.sqrt(ea))*(1.35*min(1,max(.3,rs/((.75+2e-5*z)*ra)))-.35)
    d=4098*.6108*math.exp(17.27*t/(t+237.3))/(t+237.3)**2;g=.000665*p
    expected=(.408*d*(.77*rs-rnl)+g*900/(t+273)*u*(es-ea))/(d+g*(1+.34*u))
    assert float(reference_et(t,hi,lo,rh,u,rs,p,lat,j,z))==pytest.approx(expected,abs=1e-10)
    assert 3<expected<6

def test_no_future_leakage():
    weather,_=load_weather(); a,cols=features(weather)
    cutoff=pd.Timestamp('2024-07-01')
    altered=weather.copy()
    mask=altered.date>=cutoff
    for c in ['tmean','tmax','tmin','rh','wind10','rain','solar','pressure','et0']:
        altered.loc[mask,c]+=999
    b,_=features(altered)
    pd.testing.assert_frame_equal(a[a.date==cutoff][cols],b[b.date==cutoff][cols])

def test_water_balance():
    r=bucket_step(30,5,10,20,.8,120)
    assert r['deficit']==11
    assert r['drainage']==0
    r=bucket_step(0,5,100,0,.8,120)
    assert r['drainage']==75 and r['deficit']==0
    r=bucket_step(119,6,0,0,.8,120)
    assert r['unmet']==5 and r['deficit']==120

def test_policy_boundary_and_capacity():
    assert recommend(55,120,.85,40,5)['gross_mm']==0
    assert recommend(56,120,.85,40,5)['gross_mm']>0
    r=recommend(100,120,.85,5,5)
    assert r['gross_mm']==5 and r['capacity_limited']
    assert recommend(20,120,.85,40,5)['gross_mm']==0

@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-1,200])
def test_bad_deficit_rejected(bad):
    with pytest.raises(ValueError):recommend(bad,120,.85,40,5)

def test_conformal_order_statistic():
    assert conformal_q(np.arange(10))==9
