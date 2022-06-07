# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 11:49:21 2022

----Code to process all of economic data from various sources----

All data is tabulated at the 3-digit zipcode level and stored in a Pandas dataframe.

Data sources are:
    1) median housing value (from U.S. Census Bureau), 
    2) median income (from U.S. Census Bureau),  
    3) the ratio of homeowners to renters (from U.S. Census Bureau), 
    4) local GDP trends (from Bureau of Economic Activity)

@author: Barbara Zemskova
"""

import pandas as pd
import pickle
import numpy as np
from scipy import stats

#%% Open CSV with housing values, groupby 3-digit zipcode

housing = pd.read_csv('Housing_data_2019.csv',
                      header=0, skiprows=[1],
                    index_col=False,
                    usecols=['NAME','DP04_0046E', 'DP04_0047E']
                    )

for i in range(len(housing)):
    housing.loc[i,'Zipcode']=housing.loc[i,'NAME'].split()[1][0:3]
    
housing_groups = housing.groupby(by='Zipcode').sum()
housing_groups = housing_groups.reset_index()


#%% Open CSV with income data, groupby 3-digit zipcode

income = pd.read_csv('Income_USCensus_data.csv',
                      header=0, skiprows=[1],
                    index_col=False,
                    usecols=['NAME','S1901_C01_012E']
                    )

for i in range(len(income)):
    income.loc[i,'Zipcode']=income.loc[i,'NAME'].split()[1][0:3]
    
income['Median_income'] = pd.to_numeric(income['S1901_C01_012E'],
                                        errors='coerce')

income_groups = income.groupby(by='Zipcode').mean()
income_groups = income_groups.reset_index()



#%% Create dictionary with state name abbreviations to tabulate data

state_abv = {'AL': 'Alabama', 'AK':'Alaska',
             'AZ': 'Arizona', 'AR': 'Arkansas',
             'CA': 'California', 'CO': 'Colorado',
             'CT': 'Connecticut', 'DE': 'Delaware',
             'FL': 'Florida', 'GA': 'Georgia',
             'HI':'Hawaii', 'ID': 'Idaho', 
             'IL': 'Illinois', 'IN': 'Indiana',
             'IA': 'Iowa', 'KS': 'Kansas',
             'KY': 'Kentucky', 'LA': 'Louisiana',
             'ME': 'Maine', 'MD': 'Maryland',
             'MA': 'Massachusetts', 'MI': 'Michigan',
             'MN': 'Minnesota', 'MS': 'Mississippi',
             'MO': 'Missouri', 'MT': 'Montana',
             'NE': 'Nebraska', 'NV': 'Nevada',
             'NH': 'New Hampshire', 'NJ': 'New Jersey',
             'NM': 'New Mexico', 'NY': 'New York',
             'NC': 'North Carolina', 'ND': 'North Dakota',
             'OH': 'Ohio', 'OK': 'Oklahoma',
             'OR': 'Oregon', 'PA': 'Pennsylvania',
             'RI': 'Rhode Island', 'SC': 'South Carolina',
             'SD': 'South Dakota', 'TN': 'Tennessee',
             'TX': 'Texas', 'UT':'Utah',
             'VT': 'Vermont', 'VA': 'Virginia',
             'WA': 'Washington', 'WV': 'West Virginia',
             'WI': 'Wisconsin', 'WY':'Wyoming',
             'DC': 'Washington, DC'}

state_df = pd.DataFrame(columns=['state','abbv'])
state_list = list(state_abv.keys())
i=0
for x in state_list:
    state_df.loc[i,'abbv'] = x
    state_df.loc[i,'state'] = state_abv[x]
    i+=1
    
#%% Open CSV with GDP data (available by county) and merge state names for each county

gdp_df = pd.read_csv('GDP_county.csv',
                      header=4, 
                    index_col=False,
                    )
gdp_df = gdp_df.dropna()
for i in range(len(gdp_df)):
    gdp_df.loc[i,'County']=gdp_df.loc[i,'GeoName'].split(', ')[0]
    gdp_df.loc[i,'State_abv']=gdp_df.loc[i,'GeoName'].split(', ')[1]
    
gdp_df['State_abv']=gdp_df['State_abv'].str.replace('\*','')
gdp_df_merge = pd.merge(left=gdp_df, right=state_df, 
                        how='left',left_on='State_abv', 
                        right_on='abbv')

null_index = gdp_df_merge.loc[pd.isna(gdp_df_merge["state"]), :].index
gdp_df_merge.loc[null_index[0],'state']='Virginia'
gdp_df_merge.loc[null_index[0],'abbv']='VA'

gdp_df_merge.loc[null_index[1],'state']='Virginia'
gdp_df_merge.loc[null_index[1],'abbv']='VA'

gdp_df_merge.loc[null_index[2],'state']='Virginia'
gdp_df_merge.loc[null_index[2],'abbv']='VA'

gdp_df_merge.loc[null_index[3],'state']='Virginia'
gdp_df_merge.loc[null_index[3],'abbv']='VA'

gdp_df_merge.loc[null_index[4],'state']='Virginia'
gdp_df_merge.loc[null_index[4],'abbv']='VA'

gdp_df_merge=gdp_df_merge.drop(gdp_df_merge[gdp_df_merge['2016']=='(NA)'].index)
gdp_df_merge=gdp_df_merge.drop(gdp_df_merge[gdp_df_merge['2017']=='(NA)'].index)
gdp_df_merge=gdp_df_merge.drop(gdp_df_merge[gdp_df_merge['2018']=='(NA)'].index)
gdp_df_merge=gdp_df_merge.drop(gdp_df_merge[gdp_df_merge['2019']=='(NA)'].index)
gdp_df_merge=gdp_df_merge.drop(gdp_df_merge[gdp_df_merge['2020']=='(NA)'].index)

#%% Fix some errors

county_null = gdp_df_merge.loc[gdp_df_merge['County'].str.contains('\+'),:].index
gdp_df_merge.loc[county_null[0],'County'] = 'Kalawao'
gdp_df_merge.loc[county_null[1],'County'] = 'Albemarle'
gdp_df_merge.loc[county_null[2],'County'] = 'Alleghany'
gdp_df_merge.loc[county_null[3],'County'] = 'Campbell'
gdp_df_merge.loc[county_null[4],'County'] = 'Carroll'
gdp_df_merge.loc[county_null[5],'County'] = 'Frederick'
gdp_df_merge.loc[county_null[6],'County'] = 'Greensville'
gdp_df_merge.loc[county_null[7],'County'] = 'Henry'
gdp_df_merge.loc[county_null[8],'County'] = 'James City'
gdp_df_merge.loc[county_null[9],'County'] = 'Montgomery'
gdp_df_merge.loc[county_null[10],'County'] = 'Pittsylvania'
gdp_df_merge.loc[county_null[11],'County'] = 'Prince George'
gdp_df_merge.loc[county_null[12],'County'] = 'Roanoke'
gdp_df_merge.loc[county_null[13],'County'] = 'Rockingham'
gdp_df_merge.loc[county_null[14],'County'] = 'Southampton'
gdp_df_merge.loc[county_null[15],'County'] = 'Spotsylvania'
gdp_df_merge.loc[county_null[16],'County'] = 'Washington'
gdp_df_merge.loc[county_null[17],'County'] = 'Wise'
gdp_df_merge.loc[county_null[18],'County'] = 'York'

gdp_df_merge = gdp_df_merge.reset_index()

#%% Calculate temporal GDP trends for each county


gdp_df_merge['GDP_trend'] = np.nan


for i in range(len(gdp_df_merge)):
    data=gdp_df_merge.loc[i,['2016','2017','2018','2019','2020']].to_numpy('float')    
    result = stats.linregress(np.arange(0,5,1),data)
    gdp_df_merge.loc[i,'GDP_trend']=result.slope
    
gdp_df_merge['GDP_trend_norm'] = np.nan
for i in range(len(gdp_df_merge)):
    data=gdp_df_merge.loc[i,['2016','2017','2018','2019','2020']].to_numpy('float')    
    result = stats.linregress(np.arange(0,5,1),data/data[0])
    gdp_df_merge.loc[i,'GDP_trend_norm']=result.slope


#%%
