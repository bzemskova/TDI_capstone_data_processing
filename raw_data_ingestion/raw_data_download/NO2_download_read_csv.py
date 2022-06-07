# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 15:11:47 2022

----Code to download all of the NO_2 satellite data files from Copernicus S5P satellite.----

Satellite data is stored in swaths, so a particular NetCDF file is not guaranteed to
    have data for the continental U.S.
In order to deal with this problem, files are grouped by month (original data is daily)
    and within each file, I look if any part of the data falls within the continental
    U.S. latitude and longitude. All relevant data for the continental U.S. is then
    extracted and stored as monthly averages.
    
Resulting data is stored as a zarr file, which has good compression for storing large
    data, but easy to deal with timeseries information for data arranged as grid-like arrays.   

@author: Barbara Zemskova
"""
import pandas as pd
import requests
import io
import re
from netCDF4 import Dataset
import numpy as np
import zarr
import time as tm


#%% 
# Get all filenames from the Copernicus satellite folder for S5P satellite NO_2 data
# for 2018 (data only available daily starting in March, 2018)

# Filenames will be stored in a dataframe to know which files to download 

df_NO2_filenames = pd.DataFrame(columns=['Id','Name','ContentLength','IngestionDate',
                                         'ContentDate:Start','ContentDate:End',
                                         'Checksum:Algorithm','Checksum:Value'])

m_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
for month in range(3,12,1):
        url_csv_base = 'https://scihub.copernicus.eu/catalogueview/S5P/2018/'+m_list[month]
        base = requests.get(url_csv_base)
        match = re.findall('S5P.+csv', base.text)
        for x in match:
            filename = url_csv_base +'/'+ x
            file = requests.get(filename)
            df = pd.read_csv(io.StringIO(file.text))
            df_NO2_filenames=df_NO2_filenames.append(df[df.Name.str.contains('L2__NO2')],
                                                     ignore_index=True)



#%%
# Get all filenames from the Copernicus satellite folder for S5P satellite NO_2 data
# for 2019-2021 (data available daily)

m_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
for year in range(2019,2022,1):
    for month in range(0,12,1):
        url_csv_base = 'https://scihub.copernicus.eu/catalogueview/S5P/' \
                            +str(year)+'/' +m_list[month]
        base = requests.get(url_csv_base)
        match = re.findall('S5P.+csv', base.text)
        for x in match:
            filename = url_csv_base +'/'+ x
            file = requests.get(filename)
            df = pd.read_csv(io.StringIO(file.text))
            df_NO2_filenames=df_NO2_filenames.append(df[df.Name.str.contains('L2__NO2')],
                                                     ignore_index=True)

# Save names of all the files to download
df_NO2_filenames.to_pickle('NO2_filenames.pkl')
#%%
# Here actually download each file and save information

df_NO2_filenames = pd.read_pickle('NO2_filenames.pkl') #open df with filenames

# find time (start date) for each file (each satellite swath)
time = pd.to_datetime(df_NO2_filenames['ContentDate:Start'])
start_date = time.dt.floor('D')
df_NO2_filenames['time'] = start_date

# group files by start dates, resample to monthly interval
day_group = df_NO2_filenames.groupby(['time'])
group_names = list(day_group.groups)
dates = pd.DataFrame({'date':group_names})
dates = dates.set_index('date')
dates_monthly = dates.resample('M').last()
monthly_list = list(dates_monthly.index)

# Start API session to download data
s = requests.Session()
s.post('https://s5phub.copernicus.eu/dhus/',auth=('s5pguest', 's5pguest'))

# continental U.S. latitude and longitude bounds at 1/10 degree interval
lat_list = np.arange(23,50.01,0.01)
lon_list = np.arange(-130,-64.99,0.01)

# needed for filenames url prefix
url_base = 'https://s5phub.copernicus.eu/dhus/odata/v1/Products('
url_rem = ')/$value'

for name in range(len(monthly_list)):
    # list of all files that fall within a certain month group
    df_name = day_group.get_group(monthly_list[name])['Id']
    
    #initialize df to store lat, lon and NO_2 data
    df_NO2  = pd.DataFrame(columns=['Lat','Lon','NO2'])
    i=0
    for filename in df_name:
        # download each file
        url = url_base +"'"+str(filename)+"'"+url_rem
        r = s.get(url, auth=('s5pguest', 's5pguest')).content
        link = Dataset('file.nc', memory=r)
        product=link.groups["PRODUCT"]
        
        # extract lat, lon, NO2 data from NetCDF file
        lat_1 = product.variables["latitude"][0,:,:]
        lon_1=product.variables["longitude"][0,:,:]
        NO2_1 = product.variables["nitrogendioxide_tropospheric_column"][0,:,:]
        
        # mask over where there is no satellite coverage (i.e., extract actual swath)
        mask1 = np.ma.getmaskarray(NO2_1)
        lat_1 = np.ma.array(lat_1,mask=mask1)
        lon_1 = np.ma.array(lon_1,mask=mask1)
        
        #Create dataframe with latitude, longtitude and NO2 concentration values 
        NO2_df1 = pd.DataFrame({"Lat":lat_1.compressed(),"Lon":lon_1.compressed(),
                       "NO2":NO2_1.compressed()},index=range(len(NO2_1.compressed())))
        
        #Crop data frame to go from longitude 65-130 degrees West and latitude 23-50 degrees North (approx. U.S.)
        NO2_df1.drop(NO2_df1[NO2_df1['Lon'] >-65].index, inplace=True)
        NO2_df1.drop(NO2_df1[NO2_df1['Lon'] <-130].index, inplace=True)
        NO2_df1.drop(NO2_df1[NO2_df1['Lat'] >50].index, inplace=True)
        NO2_df1.drop(NO2_df1[NO2_df1['Lat'] <23].index, inplace=True)
        NO2_df1.drop(NO2_df1[NO2_df1['NO2'] <0].index, inplace=True)
        df_NO2 = df_NO2.append(NO2_df1,ignore_index=True)
        
    # Group data for each month by latitude and longitude 
    #       (rounded to 2 decimal points because that is satellite accuracy)    
    df_NO2["Lat_round"]= df_NO2["Lat"].round(2)
    df_NO2["Lon_round"]= df_NO2["Lon"].round(2)
    
    # get latitude groups and average NO2
    res2 = df_NO2.groupby(['Lat_round', 'Lon_round'], 
                           as_index=False)['NO2'].mean()
    lat_group = res2.groupby("Lat_round")
    gr = list(lat_group.groups)
    
    # store NO2 data in lat/lon 2D array
    NO2_arr = np.zeros((len(lat_list),len(lon_list)))
    
    # loop over all latitude groups, get longitude groups, 
    # find average NO2 value for those lat/long 
    for j in range(len(gr)):
        gr1 = lat_group.get_group(gr[j]).sort_values(by=['Lon_round']).reset_index()
        gr1['Ind']=((gr1['Lon_round']+130)/0.01).round(0)
        for ind in range(len(gr1)):
            NO2_arr[j,int(gr1['Ind'][ind])] = gr1['NO2'][ind]
            
    # Store NO2 data for a particular month/year as a zarr file
    # (better compression for later dealing with arrays)
    filename_zarr = ('NO2'+str(monthly_list[name].year)+
                     str(monthly_list[name].month)
                     +str(monthly_list[name].day)+'.zarr')
    zarr.save(filename_zarr,NO2_arr)
    
    # needed because otherwise stops downloading data
    tm.sleep(300)  