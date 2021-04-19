import requests as req
import json
import pandas as pd
import numpy as np
import time
import os
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import sys
sys.path.append(".py")
import iracingapi as ir_api

#Constants for the file names
FULL_JSON = "_full.json"
SUBSESSION_RESULTS = "_session_results"
RACE_RESULTS = "_race_results"
WEEK = "_week"
LAP_DATA = "_lap_data"
SEASON_RESULTS = "_season_"
JSON = ".json"
CSV = ".csv"
START_GRID = "_start_grid"

#you should change this for the season
CURRENT_SEASON = "21S2"

#constants for the folder names
RESULTS = "results\\"
MAPPING = "mappings\\"
CURRENT_SEASON_FOLDER = CURRENT_SEASON + "\\"


#Constants for some important fields

#START GRID
CUST_ID = 'custid'
GROUP_ID = 'groupid'
DISPLAY_NAME = 'displayName'
START_POS = 'startPos'
FINISH_POS = 'finishPos'
FASTEST_LAP_NUM = 'fastestLapNum'
FASTEST_LAP_TIME = 'fastestLapTime'
POINTS = 'points'
CARNUM = 'carnum'
AVG_LAP_TIME = 'avgLapTime'
NUM_INCIDENTS = 'numIncidents'

#SUBSESSION RESULTS
SUBSESSIONID = 'subsessionid'
SEASON_NAME = 'season_name'
EVENTSTRENGTHOFFIELD = 'eventstrengthoffield'
SIMSESNAME = 'simsesname'
CCNAME = 'ccName'
OLDIRATING = 'oldirating'
NEWIRATING = 'newirating'
CARNUM = 'carnum'
CARID = 'carid'
LAPSCOMPLETE = 'lapscomplete'
INCIDENTS = 'incidents'
SIMSESTYPENAME = 'simsestypename'
FINISHPOSINCLASS = 'finishposinclass'
LAPSLEAD = 'lapslead'
CLUBSHORTNAME = 'clubshortname'
LEAGUE_POINTS = 'league_points'
OLDLICENSELEVEL = 'oldlicenselevel'
NEWLICENSELEVEL = 'newlicenselevel'

#SEASON COLUMNS
TRACK_COLUMNS = "'seasonid', 'seriesname', 'lowername', 'name', 'id', 'pkgid', 'priority', 'raceweek', 'config', 'timeOfDay'"

def create_directory(dir_name):
    try:    
        os.mkdir(dir_name)
    except:
        print("The directory " + dir_name + " exists.")

def create_series_directories(series_df, catid):
    #getting only the road series, oval 1, road is 2, dirt is 3, rally prob is 4
    mapping_path = RESULTS + MAPPING + CURRENT_SEASON + "_season_ids"
    ir_api.save_df_to_csv(series_df, mapping_path)
    
    series_df = series_df[series_df["catid"] == catid]
    #create the season folder
    season_path = RESULTS + CURRENT_SEASON_FOLDER
    #create the seasons for that season folder
    create_directory(season_path)
    
    series_df["id_name"] = series_df["seasonid"].astype(str) + "#" +  series_df["seriesname"].str.replace(" ", "_")
    for s in series_df["id_name"]: 
        path = RESULTS + CURRENT_SEASON_FOLDER + str(s)
        create_directory(path)
    return series_df

def fix_week_df(week_df):
    #adds one to the raceweek since it starts at 0
    week_df['raceweek'] = week_df['raceweek'].astype(int) + 1
    week_df['raceweek'] = week_df['raceweek'].astype(str)
 
    #creates the folder for the week. 
    week_df['name'] = week_df['raceweek'] + "_" + week_df['name'] + "#" + week_df['config']
    week_df['name'] = week_df['name'].str.replace("+", "_")
    
    #for the umalut 'cause iracing is dumb
    week_df['name'] = week_df['name'].str.replace("%C3%BC", "ü")
    
    #adding this to match the directories
    week_df['id_name'] = week_df['seasonid'].astype(str) + "#" + week_df['seriesname'].str.replace("+","_")
    return week_df

#create week directory mappings
def create_week_directories(week_df, seasonid):
    #drop the dataframe in the directory
    season_path = RESULTS + CURRENT_SEASON_FOLDER + week_df['id_name'][0]
    csv_path = season_path + "\\" + str(seasonid) + "_tracks"
    ir_api.save_df_to_csv(week_df, csv_path)
    
    for s in week_df["name"]:
        track_path = season_path + "\\" + s
        create_directory(track_path)

def create_season_directories(driver):
    series_df = ir_api.get_series_df(driver)
    print(series_df)
    series_df = create_series_directories(series_df, 2)
    for s in series_df['seasonid']:
        print(s)
        week_df = ir_api.get_track_per_season(driver, s)
        week_df = fix_week_df(week_df)
        create_week_directories(week_df, s)

def main():
    driver = ir_api.initialize_driver()
    ir_api.login(driver)
    create_season_directories(driver)
    input("Press enter to quit")
    #ir_api.update_active()
    driver.quit()
    

main()