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


def create_season_directories(driver, catid):
    season_df = ir_api.get_season_df(driver)
    #getting only the road series, oval 1, road is 2, dirt is 3, rally prob is 4
    mapping_path = RESULTS + MAPPING + CURRENT_SEASON + "_season_ids"
    ir_api.save_df_to_csv(season_df, mapping_path)
    
    season_df = season_df[season_df["catid"] == catid]
    print(season_df)
    #create the season folder
    season_path = RESULTS + CURRENT_SEASON_FOLDER
    #create the seasons for that season folder
    create_directory(season_path)
    for s in season_df["seasonid"]: 
        path = RESULTS + CURRENT_SEASON_FOLDER + str(s)
        create_directory(path)

#create week directory mappings
def create_week_directories(driver, seasonid):
    week_df = ir_api.get_track_per_season(driver, seasonid)
    
    print(week_df)


def main():
    driver = ir_api.initialize_driver()
    ir_api.login(driver)
    #create_season_directories(driver, 2)
    
    create_week_directories(driver, 3164)
    input("Press enter to quit")
    #ir_api.update_active()
    driver.quit()
main()