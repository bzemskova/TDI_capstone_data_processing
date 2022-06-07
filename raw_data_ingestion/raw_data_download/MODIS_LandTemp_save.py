# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 14:29:35 2022

----Code to download all of the land temperature satellite data files from MODIS satellite.----

First, I scrape the website with all file names and using regex, extract and
    store the names of all MODIS files in a list.

Then I loop over this list of files names, 
    and extract and store all relevant data for the continental U.S.
    
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
import pickle
import time
import glob
#%%
download_list = []
url_base = 'https://e4ftl01.cr.usgs.gov/MOLT/MOD11C3.061/'
r = requests.get(url_base)
match_link = r'href..(\d\d\d\d\.\d\d\.\d\d)'
match = re.findall(match_link, r.text)
for x in match:
    tot_url = url_base + x
    r2=requests.get(tot_url)
    match_file = r'<\s*a [^>]*href="(MOD.+hdf)</a'
    match_name = re.findall(match_file,r2.text)
    a =match_name[0].split('">')[-1]
    download_list.append(tot_url+'/'+a)
    
#%%
from http.cookiejar import CookieJar
import urllib.request as urllib2
from pyhdf.SD import SD, SDC
import zarr

download_list = pd.read_pickle('MODIS_temp_list.pkl')
username = "b_zemskova"
password = "Ocean2019!"

password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_manager.add_password(None, "https://urs.earthdata.nasa.gov", 
                              username, password)

cookie_jar = CookieJar()
opener = urllib2.build_opener(
    urllib2.HTTPBasicAuthHandler(password_manager),
    #urllib2.HTTPHandler(debuglevel=1),    # Uncomment these two lines to see
    #urllib2.HTTPSHandler(debuglevel=1),   # details of the requests/responses
    urllib2.HTTPCookieProcessor(cookie_jar))
urllib2.install_opener(opener)

for url in download_list:
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    body = response.read()
    file_name = url.split('/')[-1]
    file_ = open(file_name,'wb')
    file_.write(body)
    file_.close()
    hdf = SD(file_name,SDC.READ)
    
     #Select contiguous U.S. cells
    land_temp = hdf.select('LST_Day_CMG')[800:1320,1000:2300]
    if 'temp_z' not in dir():
        temp_z = zarr.array(land_temp.reshape(520,1300,1), chunks=(40, 100,1))
    else:
        temp_z.append(land_temp.reshape(520,1300,1),axis=2)
    
    # Write to Xarray files chunked for processing
    zarr.save('MODIS_LandTemp.zarr',temp_z)