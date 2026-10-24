"""FAO-56 inspired daily reference ET and an explicitly simplified root bucket."""
import math
import numpy as np

def reference_et(tmean, tmax, tmin, rh, wind, solar_mj, pressure_kpa, latitude, doy, elevation):
    """Daily FAO-56 PM, G=0, RHmean approximation (Eq 19), measured Rs.

    Rs and Ra in MJ/m²/day, temperature °C, wind m/s at 2 m, pressure kPa.
    Returns a calculated reference index, never a field measurement.
    """
    tmean,tmax,tmin,rh,wind,solar_mj,pressure_kpa,doy = map(np.asarray,(tmean,tmax,tmin,rh,wind,solar_mj,pressure_kpa,doy))
    phi=np.deg2rad(latitude)
    dr=1+0.033*np.cos(2*np.pi*doy/365)
    decl=0.409*np.sin(2*np.pi*doy/365-1.39)
    ws=np.arccos(np.clip(-np.tan(phi)*np.tan(decl),-1,1))
    ra=24*60/np.pi*0.0820*dr*(ws*np.sin(phi)*np.sin(decl)+np.cos(phi)*np.cos(decl)*np.sin(ws))
    rso=(0.75+2e-5*elevation)*ra
    es=(0.6108*np.exp(17.27*tmax/(tmax+237.3))+0.6108*np.exp(17.27*tmin/(tmin+237.3)))/2
    ea=es*rh/100
    rnl=4.903e-9*((tmax+273.16)**4+(tmin+273.16)**4)/2*(0.34-0.14*np.sqrt(ea))*(1.35*np.clip(solar_mj/rso,0.3,1)-0.35)
    rn=0.77*solar_mj-rnl
    delta=4098*(0.6108*np.exp(17.27*tmean/(tmean+237.3)))/(tmean+237.3)**2
    gamma=0.000665*pressure_kpa
    return np.maximum(0,(0.408*delta*rn+gamma*900/(tmean+273)*wind*(es-ea))/(delta+gamma*(1+0.34*wind)))

def crop_coefficient(month,day):
    # Illustrative maize May-Sep season, uncalibrated local phenology.
    k={5:0.45,6:0.8,7:1.15,8:1.15,9:0.7}
    return k.get(int(month),0.45)

def recommend(deficit, taw, eta, cap, et, kc=1.0, p=0.5, target_fraction=0.25):
    values=[deficit,taw,eta,cap,et,kc,p,target_fraction]
    if not all(math.isfinite(float(v)) for v in values): raise ValueError('所有输入必须是有限数值')
    if not (40<=taw<=240 and 0<=deficit<=taw and 0.4<=eta<=1 and 0<=cap<=100 and 0<=et<=30 and 0.1<=kc<=1.5 and 0.2<=p<=0.8 and 0<=target_fraction<p):
        raise ValueError('参数超出支持范围，请复核土壤、效率和供水上限')
    projected=deficit+et*kc
    required=max(0,projected-taw*target_fraction)/eta if projected>taw*p else 0
    gross=min(cap,required)
    after=projected-eta*gross
    return dict(gross_mm=round(gross,4),net_mm=round(gross*eta,4),projected_deficit_mm=round(after,4),raw_mm=taw*p,capacity_limited=required>cap+1e-9,triggered=projected>taw*p)

def bucket_step(deficit, et, rain, gross, eta, taw):
    # Rain infiltration fraction 0.8; no measured runoff or yield model.
    balance=deficit+et-0.8*rain-eta*gross
    return dict(deficit=min(taw,max(0,balance)), drainage=max(0,-balance),unmet=max(0,balance-taw))
