# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 14:21:27 2022

Aggregate economic and environmental data to 3-digit zipcodes and store as 
    a Pandas dataframe.

@author: Barbara
"""

import pandas as pd
import requests
import io
import re
from netCDF4 import Dataset
import numpy as np
import zarr
import pickle
import time
import glob

from scipy import stats
from statsmodels.tsa.seasonal import STL, seasonal_decompose
import datetime

#%%
# Load file with HPI trends computed before
hpi = pd.read_pickle('HPI_trends_lat_long.pkl')

# Load file with geographic information about each 3-digit zcta code
zcta = pd.read_csv('2021_Gaz_zcta_national.txt',sep='\s+',
dtype={'GEOID':str})
for i in range(len(zcta)):
    zcta.loc[i,'Zipcode']=zcta.loc[i,'GEOID'][0:3]
    
#get latitude and longtitude of each 3-digit zcta code
df_lat_lon = zcta.groupby(by=['Zipcode'])['INTPTLAT','INTPTLONG'].mean()
df_lat_lon.reset_index()

#get total area of each zipcode (water+land area)
df1 = zcta.groupby(by=['Zipcode'])['ALAND_SQMI','AWATER_SQMI'].sum()
df1['TOT_AREA']=df1['ALAND_SQMI']+df1['AWATER_SQMI']
df1.reset_index()
hpi2=pd.merge(hpi,df1,how='left',left_on='Zipcode',right_on='Zipcode')
hpi_area = pd.merge(hpi2,df_lat_lon,how='left',left_on='Zipcode',right_on='Zipcode')

# approximate radius of each zipcode, approximating each zipcode as a circle
hpi_area['Radius'] = np.sqrt(hpi_area['TOT_AREA']/(1.6**2)/np.pi)
hpi_area.to_pickle('HPI_lat_long_area.pkl')

#%% Load and open precipitation data

hpi_area['Precip_Monthly_AVG']=np.nan
hpi_area['Precip_AnnualTrend']=np.nan
hpi_area['Precip_Min_dist'] = 0.

precip = pd.read_pickle('precip_data.pkl')
precip_clean = precip.copy()
precip_clean.dropna(inplace=True)
precip_clean=precip_clean.reset_index(drop=True)

#%% Tabulate precipitation data to 3-digit zipcode level
# first convert latitude and longitude to miles
# then find all grid cells that are within the radius from the center of each 3-digit zipcode
#   and average over all those cells

for j in range(len(hpi_area)):
    lat1 = hpi_area['INTPTLAT'][j]
    lon1 = hpi_area['INTPTLONG'][j]
    precip_clean['dist']= np.sqrt(((precip_clean['Lat']-lat1)*111.)**2
                                           +(111*(precip_clean['Lon']-lon1))**2)
    
    df2 = precip_clean[precip_clean['dist']<=hpi_area.loc[j,'Radius']]
    df2.dropna(inplace=True)
    if len(df2)>0:
        hpi_area.loc[j,['Precip_Monthly_AVG']]=df2['Montly_Mean'].mean()
        hpi_area.loc[j,['Precip_AnnualTrend']]=df2['Annual_Trend'].mean()
    else:
        ind_min = precip_clean['dist'].idxmin()
        hpi_area.loc[j,['Precip_Monthly_AVG']]=precip_clean['Montly_Mean'][ind_min]
        hpi_area.loc[j,['Precip_AnnualTrend']]=precip_clean['Annual_Trend'][ind_min]
        hpi_area.loc[j,'Precip_Min_dist'] = precip_clean['dist'][ind_min]
        

#%% Tabulate MODIS data (temperature, vegetation coverage) to 3-digit zipcode level
# first convert latitude and longitude to miles
# then find all grid cells that are within the radius from the center of each 3-digit zipcode
#   and average over all those cells

data = np.load('modis_temp_data.npz')
lat_modis = data['lat_modis']
lon_modis = data['lon_modis']
mean_temp = data['mean_temp']
temp_trend = data['temp_trend']
ind_nan = data['ind_nan']
lat_v = data['lat_v']
lon_v = data['lon_v']

data = np.load('modis_vegind.npz')
vi_trend = data['vi_trend']
mean_vi = data['mean_vi']

hpi_area['LandTemp_Monthly_AVG']=np.nan
hpi_area['LandTemp_AnnualTrend']=np.nan

for j in range(len(hpi_area)):
    lat1 = hpi_area['INTPTLAT'][j]
    lon1 = hpi_area['INTPTLONG'][j]
    dist = np.sqrt(((lat_v-lat1)*111.)**2+(111*(lon_v-lon1))**2)
    
    ind1 = np.where(dist<=hpi_area.loc[j,'Radius'])
    if len(ind1[0])>0:
        hpi_area.loc[j,'LandTemp_Monthly_AVG']=np.nanmean(mean_temp[ind1[0],
                                                                    ind1[1]])
        hpi_area.loc[j,'LandTemp_AnnualTrend']=np.nanmean(temp_trend[ind1[0],
                                                                     ind1[1]])
    else:
        ii = np.where(dist==np.nanmin(dist))
        hpi_area.loc[j,'LandTemp_Monthly_AVG']=mean_temp[ii[0],ii[1]]
        hpi_area.loc[j,'LandTemp_AnnualTrend']=temp_trend[ii[0],ii[1]]
        

hpi_area['VegInd_Monthly_AVG']=np.nan
hpi_area['VegInd_AnnualTrend']=np.nan

for j in range(len(hpi_area)):
    lat1 = hpi_area['INTPTLAT'][j]
    lon1 = hpi_area['INTPTLONG'][j]
    dist = np.sqrt(((lat_v-lat1)*111.)**2+(111*(lon_v-lon1))**2)
    
    ind1 = np.where(dist<=hpi_area.loc[j,'Radius'])
    if len(ind1[0])>0:
        hpi_area.loc[j,'VegInd_Monthly_AVG']=np.nanmean(mean_vi[ind1[0],
                                                                    ind1[1]])
        hpi_area.loc[j,'VegInd_AnnualTrend']=np.nanmean(vi_trend[ind1[0],
                                                                     ind1[1]])
    else:
        ii = np.where(dist==np.nanmin(dist))
        hpi_area.loc[j,'VegInd_Monthly_AVG']=mean_vi[ii[0],ii[1]]
        hpi_area.loc[j,'VegInd_AnnualTrend']=vi_trend[ii[0],ii[1]]
        
#%% Tabulate NO_2 data to 3-digit zipcode level
# first convert latitude and longitude to miles
# then find all grid cells that are within the radius from the center of each 3-digit zipcode
#   and average over all those cells


data = np.load('NO2_processed.npz')
NO2_mean = data['NO2_mean']
lat_tropomi=data['lat_tropomi']
lon_tropomi=data['lon_tropomi']
del data

lat_t, lon_t = np.meshgrid(lat_tropomi, lon_tropomi, indexing='ij')
hpi_area['NO2_Monthly_AVG']=np.nan


for j in range(len(hpi_area)):
    lat1 = hpi_area['INTPTLAT'][j]
    lon1 = hpi_area['INTPTLONG'][j]
    dist = np.sqrt(((lat_t-lat1)*111.)**2+(111*(lon_t-lon1))**2)
    
    ind1 = np.where(dist<=hpi_area.loc[j,'Radius'])
    if len(ind1[0])>0:
        hpi_area.loc[j,'NO2_Monthly_AVG']=np.nanmean(NO2_mean[ind1[0],
                                                                    ind1[1]])
        
    else:
        ii = np.where(dist==np.nanmin(dist))
        hpi_area.loc[j,'NO2_Monthly_AVG']=NO2_mean[ii[0],ii[1]]
        

#%% Save the master file
hpi_area.to_pickle('master_econ_env_data_zcta.pkl')

