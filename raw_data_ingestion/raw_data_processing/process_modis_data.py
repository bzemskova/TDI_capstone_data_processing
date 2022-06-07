# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 16:40:58 2022

----Code to process all of the MODIS satellite data (land temperature, vegatation index).----

Data is stored after ingestion as zarr files, which are good for large arrays.
Here, I need to find temporal trends, so I will open the zarr files in chunks (lat-lon-time)
    and process data chunk by chunk.
    
Temporal trend analysis is performed using TSA Seasonal model from statsmodels module,
    which automatically subtracts seasonal trends.

@author: Barbara Zemskova
"""


import zarr
import numpy as np
import pandas as pd
import datetime
from statsmodels.tsa.seasonal import STL, seasonal_decompose
from scipy import stats
#%% Calculate mean and trend of land temperature


temp_z = zarr.open('MODIS_LandTemp.zarr', mode='r')

xlen = temp_z.shape[0]
ylen = temp_z.shape[1]

#Temporal trend analysis over 2000-2021 time period
time_range=pd.date_range(start=datetime.date(2000,3,1),
                         end=datetime.date(2021,12,31),freq='M')

mean_temp = np.zeros((xlen,ylen))
temp_trend = np.zeros((xlen,ylen))

for i in range(xlen):
    for j in range(ylen):
        #adjust raw data to be in degrees C
        land_temp = (temp_z[i,j,:])*0.02-273.15
        
        #calculate mean value and trend in every cell where there is data
        if land_temp.mean()!=0:
            mean_temp[i,j] = land_temp.mean()
            vipdm = pd.Series(land_temp, 
                              index=time_range, 
                              name = 'VI')
            stl = STL(vipdm)
            res = stl.fit()
            s=stats.linregress(np.arange(0,len(res.trend.to_numpy()),1),
                                                 res.trend.to_numpy())
            temp_trend[i,j]=12*s.slope
            
#Save data:
np.savez('modis_temp_data.npz', 
         mean_temp=mean_temp, temp_trend=temp_trend)
            
#%% Calculate mean and temporal trend of the vegetation coverage index


temp_vi = zarr.open('MODIS_VegInd.zarr', mode='r')

xlen = temp_vi.shape[0]
ylen = temp_vi.shape[1]

time_range=pd.date_range(start=datetime.date(2000,2,1),
                         end=datetime.date(2022,1,31),freq='M')

mean_vi = np.zeros((xlen,ylen))
vi_trend = np.zeros((xlen,ylen))

for i in range(xlen):
    for j in range(ylen):
        veg_ind = (temp_vi[i,j,:])*0.0001
        if veg_ind.mean()!=0:
            mean_vi[i,j] = veg_ind.mean()
            vipdm = pd.Series(veg_ind, 
                              index=time_range, 
                              name = 'VI')
            stl = STL(vipdm)
            res = stl.fit()
            s=stats.linregress(np.arange(0,len(res.trend.to_numpy()),1),
                                                 res.trend.to_numpy())
            vi_trend[i,j]=12*s.slope
            
np.savez('modis_vegind.npz', 
         mean_vi=mean_vi, vi_trend=vi_trend)