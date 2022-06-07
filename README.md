# The Data Incubator (TDI) capstone requirements
- Motivation/objective: While housing prices are increasing almost everywhere across the U.S., in some areas, they are increasing faster than before the 2008 market crash, and in some areas (e.g., California, mid-Atlantic and Northeastern cities and suburbs) prices are increasing slower than before. As more people are able to move from home, it is possible that urban and suburban areas are no longer the magnets, and people are moving out to more rural areas, but it is unclear how we find which rural areas are more desirable. The goal of the project is to find and predict regions where housing prices have been increasing disproportionately fast or slow and see if including environmental factors can improve the model's prediction of these trends. 
- Data ingestion: The economic data used in this study are: 1) median housing value (from U.S. Census Bureau), 2) median income (from U.S. Census Bureau),  3) the ratio of homeowners to renters (from U.S. Census Bureau), and 4) local GDP trends (from Bureau of Economic Activity). The first three are already available at 3-digit zipcode level. The last one is computed from GDP timeseries reported at the 5-digit zipcode level and grouped into 3-digit zipcodes. Environmental data used in the model are: 1) land temperature (MODIS satellite), 2) vegetation cover (MODIS satellite), 3) air pollution levels (approximated as nitrogen dioxide concentration measured by Tropomi satellite), and 4) precipitation rates (collected from various sources by NOAA). Data was downloaded using APIs from each satellite website. Environmental data is reported in latitude-longitude grid space that is then tabulated at 3-digit zipcode level using center latitude-longitude and area of each zipcode.
- Data science: The project completes the ML and website requirements. I trained random forest models, one for the entire U.S., and one for each of the nine geographic regions with the economic and environmental features described above, also using polynomial interaction-only features. I compared R<sup>2</sup> of predicting change in HPI trends from 2000-2008 to 2018-2021 period from the base model, which uses only economic features, with that of the total model that includes both economic and environmental features. I also looked at the feature importance obtained from each random forest model for the total model to find whether environmental factors are actually important. For the entire U.S. and for seven out of nine geographic regions (excluding the west coast and mid-Atlantic), including environmental factors improved R<sup>2</sup> of the model and top three important features included several of the environmental factors. I then used predictions from IPCC climate models for temperature and precipitation (mean values and trends) for the 2027-2030 period and used the model to predict HPI trends over that period. The results are summarized in a Heroku app that was built using Flask: http://tdi-env-housing-model.herokuapp.com/
- Visualizations: The Heroku app shows several visualization. There is a summary map of change in housing trends and R<sup>2</sup> of each random forest model ("Results Overview" tab), Altair dashboard showing three most important features for the random forest model corresponding to the selected region of the U.S. ("Regional Breakdown" tab), and two Altair dashboards, one displaying chosen region and one displaying chosen state, showing investment profittability for 2027-2030 predicted by the model ("Future Price Predictions" tab).


# The Data Incubator (TDI) capstone data processing
See http://tdi-env-housing-model.herokuapp.com/ for summary of the project and to view all of the interactive dashboards.
- Scripts for raw data ingestion, processing, and model building for TDI capstone project on predicting trends in housing price indices. Includes scripts for data plotting.
- The goal of the project is to use publicly available economic and environmental data to build a model (here random forest model) that predicts where, based on 3-digit zipcode averages, housing prices will grow disproportionately faster or slower.
  - economic features: median house prices, median income, owner-to-renter ratio, GDP trends
  - environmental features: temperature (mean, trend), precipitation (mean, trend), air pollution levels, vegetation cover (mean, trend)

 
## "data" folder
contains processed data files, typically pandas dataframes stored in either pickled (.pkl) or json (.json) format.
- "master_econ_env_data_zcta.pkl": all economic and environmental data tabulated at 3-digit zipcode level; master dataframe used for plotting and in training the random forest model.
- "ipcc_master_df.pkl": in addition to the information in the master dataframe, includes IPCC climate model predictions for temperature/precipitation for 2027-2030 tabulated at 3-digit zipcode level and predictions for HPI trends for 2027-2030 period computed using regional random forest models.
- useful dictionary files (more information in "GeographicDictionaries.ipynb")
   - "state_region_dict.pkl": dictionary of economic regions and U.S. states that belong to each region
   - "state_id_dict.pkl": dictionary of U.S. state names and corresponding federal state I.D.s
   - "econ_env_predictors_dict.pkl": dictionary of column names from "master_econ_env_data_zcta.pkl" and corresponding interpretations for the economic and environmental predictors used in the random forest models
-  dataframes with results from trained random forest models:
   - "random_forest_r2.pkl" (R<sup>2</sup> for base and total random forest models for each region and entire U.S.)
   - "random_forest_top3_features.pkl" (top three most important features for each region and the entire U.S. from trained random forest models)
-  numpy zipped archive files with temperature and precipitation and latitude/longitude data from IPCC climate models: "RCP4_5_precip_temp.npz" ("best case scenario" IPCC model), "RCP8_5_precip_temp.npz" ("intermediate case scenario" IPCC model)
-  json files used for plotting interactive dashboards in "DataPlotting_predictions.ipynb": "predict_df.json", "predict_df_all.json", "predict_df_large.json" (stored dataframes contain the same information but in different layouts that are needed for making various figures in Altair) 

## "random_forest_models" folder
contains pickled Random Forest models trained for each economic region using economic and environmental features described above

## "raw_data_ingestion" folder
contains scripts for downloading data, in particular using API calls for large environmental data files ("raw_data_download" folder) and scripts for processing downloaded data so that it is all tabulated at the 3-digit zipcode level ("raw_data_processing" folder)

## Jupyter notebooks
Notebooks are listed in order of the workflow:
- "GeographicDictionaries.ipynb": generates useful dictionaries ("state_region_dict.pkl", "state_id_dict.pkl", "econ_env_predictors_dict.pkl") that are needed throughout other notebooks
- "DataPlotting_Exploratory.ipynb": loads all cleaned data from "master_econ_env_data_zcta.pkl" and makes scatterplot maps of economic and environmental data over the U.S.
- "RandomForestModels.ipynb": trains and saves Random Forest models for each of the economic region and the entire U.S. using economic and environmental data
- "DataPlotting_RandomForest.ipynb": plots trained Random Forest model results ("random_forest_r2.pkl", "random_forest_top3_features.pkl") as an interactive plot, where user can select a region of the U.S. to focus on.
- "DataCleaning_IPCC_predictions.ipynb": processes temperature and precipitation data from selected IPCC climate models to get averages for each 3-digit zipcode using "RCP4_5_precip_temp.npz" and "RCP8_5_precip_temp.npz"
- "Predicting_Future_HPI.ipynb": uses saved Random Forest models for each economic region to take new predicted temperature and precipitation data from IPCC climate models for 2027-2030 time period to make predictions for future HPI trends for each 3-digit zipcode
- "DataPlotting_predictions.ipynb": plots static and interactive plots for the predicted future HPI trends overlayed over map of the U.S. For the interactive maps, user can select a specific region or a specific state of interest.
