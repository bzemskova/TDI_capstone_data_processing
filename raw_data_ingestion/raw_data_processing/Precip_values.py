# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 17:36:09 2022

----Code to download and process precipitation data from NOAA----

Scrape NOAA data repository to find precipitation gauge stations within contiguous U.S.
    and find all the data for each station available over 2000-2021 time period.
Only keep stations that have sufficient data (at least two-years worth).
Backfill missing data, if there are enough observations.

Calculate mean and temporal trend for each gauge station, and store along with
    geographic information.

@author: Barbara Zemskova
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

#%%

#Get names of all precipitation gauge stations from NOAA website
r = requests.get('https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt')

#Organize gauge station information in a Pandas dataframe
with open("precip_table.txt", "w") as f:
    f.write(r.text)
precip_table = pd.read_csv('precip_table.txt',sep='\s+',
                           header=None,
                           names=['Id','Lat','Lon','Sm1','Name','Sm2','Sm3'],
                           index_col=False)
df1 = precip_table.copy()

#Only keep gauge stations that are located in the contiguous U.S.
df1.drop(df1[df1['Lon'] >-65].index, inplace=True)
df1.drop(df1[df1['Lon'] <-130].index, inplace=True)
df1.drop(df1[df1['Lat'] >50].index, inplace=True)
df1.drop(df1[df1['Lat'] <23].index, inplace=True)
df1 = df1[df1['Id'].str.contains(r'US.+')]    
precip_table = df1.loc[:,['Id','Lat','Lon']].reset_index(drop=True)
precip_table.to_pickle('precip_filenames.pkl')
 
#Find all data files gauge stations that actually have data and save their names in a dataframe
r = requests.get('https://www.ncei.noaa.gov/data/gsom/access/')
match_file = r'<\s*a [^>]*href="(US.+csv)</a'
match_name = re.findall(match_file,r.text)

lst = []
for x in match_name:
    lst.append(x.split('">')[-1][:-4])
    
valid_stations = pd.Series(lst,name='Id')
valid_stations.to_pickle('precip_valid.pkl')    
 
#%%    

precip_table = pd.read_pickle('precip_filenames.pkl')
valid_stations = pd.read_pickle('precip_valid.pkl')

#Initialize a dataframe to calculate precipitation data for each gauge station
df_precip = pd.merge(valid_stations,precip_table,left_on='Id',right_on='Id')
df_precip['Montly_Mean'] = np.zeros((len(df_precip),))
df_precip['Annual_Trend'] = np.zeros((len(df_precip),))
df_precip['Yrs'] = np.zeros((len(df_precip),))
df_precip['Yr:Start'] = np.zeros((len(df_precip),))
df_precip['Yr:End']=np.zeros((len(df_precip),))
df_precip['NumObs']=np.zeros((len(df_precip),))


# Read all precipitation files (CSV) for each gauge station
     
for i in range(len(df_precip)):
    url = 'https://www.ncei.noaa.gov/data/gsom/access/'+df_precip.loc[i,'Id']+'.csv'
    ex = pd.read_csv(url)
    if 'PRCP' not in list(ex.columns):
        df_precip.loc[i,'Annual_Trend'] = np.nan
        df_precip.loc[i,'Montly_Mean'] = np.nan
    else:
        ex_timeseries = ex.loc[:,['DATE','PRCP']].reset_index(drop=True)
        ex_timeseries['DATE'] = pd.to_datetime(ex_timeseries['DATE'])
        
        # If precipitation data after the year 2000 is available, store data.
        # Also, count number of observations/data points
        
        ex2 = ex_timeseries.set_index('DATE').resample('M').last()
        ex2['Year'] = ex2.index.year
        ex2 = ex2[ex2['Year']>=2000]
        count_yr = ex2.groupby(['Year']).size().reset_index(name='counts').set_index('Year')
        count_yr_na = ex2.dropna(subset=['PRCP']).groupby(['Year']).size().reset_index(name='counts').set_index('Year')
        count = pd.merge(count_yr,count_yr_na,how='outer',left_index=True,right_index=True)
        count.drop(count[(count['counts_x']-count['counts_y'])<4].index,inplace=True)
        a = list(count.index.values)
        a.reverse()
        yrs = list(count_yr.index.values)
        yrs.reverse()
        b = []
        while (a and yrs) and min(a)==min(yrs):
            b.append(min(a))
            a.pop()
            yrs.pop()
        a = list(count.index.values)
        yrs = list(count_yr.index.values)
        while (a and yrs) and max(a)==max(yrs):
            b.append(max(a))
            a.pop()
            yrs.pop()
            
        if b:
            ex_df=ex2[~ex2['Year'].isin(b)]
        else:
            ex_df = ex2.copy()
            
        #Backfill missing data so that can compute temporal trends
        ex_df = ex_df.fillna(method='ffill')
        ex_df = ex_df.fillna(method='bfill')
        
        # If there are at least 2 years of observations and 10 distinct data points,
        #       compute temporal trends using statsmodel TSA seasonal model
        if ex_df['Year'].nunique()>=2 and len(ex_df)>=10:
            vipdm = pd.Series(ex_df['PRCP'], 
                              index=pd.date_range(start=ex_df.index.min(),
                                                  end=ex_df.index.max(),
                                                  freq='M'), 
                              name = 'VI')
            stl = STL(vipdm)
            res = stl.fit()
            [s,_,_,_,_]=stats.linregress(np.arange(0,len(res.trend.to_numpy()),1),
                                                 res.trend.to_numpy())
            df_precip.loc[i,'Annual_Trend'] = s*12
            df_precip.loc[i,'Montly_Mean'] = (ex_df['PRCP'].sum())/len(ex_df)
            df_precip.loc[i,'Yrs'] = ex_df['Year'].nunique()
            df_precip.loc[i,'Yr:Start'] = ex_df['Year'].min()
            df_precip.loc[i,'Yr:End']=ex_df['Year'].max()
            df_precip.loc[i,'NumObs']=len(ex_df)
        else:
            df_precip.loc[i,'Annual_Trend'] = np.nan
            df_precip.loc[i,'Montly_Mean'] = np.nan
            df_precip.loc[i,'Yrs'] = ex_df['Year'].nunique()
            df_precip.loc[i,'Yr:Start'] = ex_df['Year'].min()
            df_precip.loc[i,'Yr:End']=ex_df['Year'].max()
            df_precip.loc[i,'NumObs']=len(ex_df)

#Store data:
df_precip.to_pickle('precip_data.pkl')