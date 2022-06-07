# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 11:30:21 2022

----Code to process all of the NO_2 satellite data files----

There is not enough temporal data (only 2018-2021 period) to compute long-term
    trend, so only calculate mean NO_2 concentrations for each grid cell.
    
First, all NO_2 files for each month are combined into a single zarr file.
Then, each chunk (lat-lon-time) is averaged to compute temporal average at
    each lat-lon grid cell.

@author: Barbara
"""


import zarr
import numpy as np
import glob

files=glob.glob('NO2*zarr')

#%%
# Open each of the NO_2 files processed from the raw satellite data and
#combine them into a single zarr array.

for file in files:
    no2 = zarr.open(file, mode='r')[:]
    if 'no2_z' not in dir():
        no2_z = zarr.array(no2.reshape(2701,6501,1), chunks=(100, 100,1))
    else:
        no2_z.append(no2.reshape(2701,6501,1),axis=2)

b = zarr.array(no2_z, chunks=(73,197,None), store='b.zarr')

#%%
# Calculate long-term mean for each lat-lon grid cell
#by loading each of the chunks of the zarr array

b = zarr.open('b.arr',mode='r')

#chunks are (73,197,25), there are (37,33) chunks
NO2_mean = np.zeros((2701,6501))


# Also, need to make sure that cells with no data (filled with zeros) are 
#filled with NaNs to be excluded from calculating the mean.
for i in range(37):
    for j in range(33):
        b_arr = b[73*i:73*(i+1),197*j:197*(j+1)]
        b_arr[np.where(b_arr==0)] = np.nan
        NO2_mean[73*i:73*(i+1),197*j:197*(j+1)] = np.nanmean(b_arr,axis=2)

np.savez('NO2_processed.npz',NO2_mean=NO2_mean)