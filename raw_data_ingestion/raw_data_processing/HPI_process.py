# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 10:08:43 2022

----Code to process housing price index data----

This code loads data, which is reported quarterly over 2000-2021 time period
     into a Pandas dataframe and groups data by the first 3 digits of the zipcode.
Then, temporal trend analysis is performed over different time periods
    (2000-2008, 2016-2021, 2018-2021).

Temporal trends are computed using the TSA seasonal model from the statsmodel module.
    This model calculates seasonal trends and subtracts them.

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
hpi = pd.read_excel('HPI_AT_3zip.xlsx',header=0,
                    names=['Zipcode','Year',	'Quarter'	,'Index','Index_Type'],
                    dtype={'Zipcode':str})

hpi.to_pickle('hpi_rawdata.pkl')

#%%
hpi = pd.read_pickle('hpi_rawdata.pkl')

for i in range(len(hpi)):
    if len(hpi.loc[i,'Zipcode'])<3:
        hpi.loc[i,'Zipcode'] = '0'+hpi.loc[i,'Zipcode']

hpi_groups = hpi.groupby(by='Zipcode')
hpi_group_names = list(hpi_groups.groups)
#%%
hpi_trends = pd.DataFrame({'Zipcode':hpi_group_names})
hpi_trends['AnnualTrend_2000_2021']=np.nan#np.zeros((len(hpi_trends),))
hpi_trends['AnnualTrend_2000_2008']=np.nan # zeros((len(hpi_trends),))
hpi_trends['AnnualTrend_2015_2021']=np.nan #zeros((len(hpi_trends),))
hpi_trends['min_year']=np.nan
hpi_trends['max_year']=np.nan


for i in range(len(hpi_group_names)):
    df1 = hpi_groups.get_group(hpi_group_names[i]).reset_index(drop=True)
    df1.drop(df1[df1['Year']<2000].index,inplace=True)
    if len(df1)>0:
        df1 = df1.reset_index(drop=True)
        hpi_trends.loc[i,"min_year"]=df1['Year'].min()
        hpi_trends.loc[i,"max_year"]=df1['Year'].max()        
        ind=pd.date_range(start=datetime.date(df1['Year'].min(),1,1),
                                            end=datetime.date(df1['Year'].max(),12,31),
                                            freq='Q')
        time_delta = (ind-ind[0]).days/365.
        result = stats.linregress(time_delta, 
                                  df1["Index"]/df1.loc[0,'Index'])
        
        hpi_trends.loc[i,'AnnualTrend_2000_2021']=result.slope
        
        df2 = df1.copy()
        df2.drop(df2[df2['Year']>2009].index,inplace=True)
        if len(df2)>0:
            df2 = df2.reset_index(drop=True)
            ind=pd.date_range(start=datetime.date(df2['Year'].min(),1,1),
                                            end=datetime.date(df2['Year'].max(),12,31),
                                            freq='Q')
            time_delta = (ind-ind[0]).days/365.
            result = stats.linregress(time_delta, 
                                  df2["Index"]/df2.loc[0,'Index'])
        
            hpi_trends.loc[i,'AnnualTrend_2000_2008']=result.slope
        
        
        df3 = df1.copy()
        df3.drop(df3[df3['Year']<2016].index,inplace=True)
        if len(df3)>0:
            df3 = df3.reset_index(drop=True)
            ind=pd.date_range(start=datetime.date(df3['Year'].min(),1,1),
                                            end=datetime.date(df3['Year'].max(),12,31),
                                            freq='Q')
            time_delta = (ind-ind[0]).days/365.
            result = stats.linregress(time_delta, 
                                  df3["Index"]/df3.loc[0,'Index'])
        
            hpi_trends.loc[i,'AnnualTrend_2016_2021']=result.slope
            
        df4 = df1.copy()
        df4.drop(df4[df4['Year']<2018].index,inplace=True)
        if len(df4)>0:
            df4 = df4.reset_index(drop=True)
            ind=pd.date_range(start=datetime.date(df4['Year'].min(),1,1),
                                            end=datetime.date(df4['Year'].max(),12,31),
                                            freq='Q')
            time_delta = (ind-ind[0]).days/365.
            result = stats.linregress(time_delta, 
                                  df4["Index"]/df4.loc[0,'Index'])
        
            hpi_trends.loc[i,'AnnualTrend_2018_2021']=result.slope
        


hpi_trends.to_pickle('HPI_trends_lat_long.pkl')
