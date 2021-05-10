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
SEASON_IDS = "_season_ids"
SESSIONS = "_sessions"
TRACKS = "_tracks"

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
        return 1
    except:
        print("The directory " + dir_name + " exists.")
        return 0

def create_series_directories(series_df, catid):
    #getting only the road series, oval 1, road is 2, dirt is 3, rally prob is 4
    mapping_path = RESULTS + MAPPING + CURRENT_SEASON + SEASON_IDS
    series_df["id_name"] = series_df["seasonid"].astype(str) + "#" +  series_df["seriesname"].str.replace(" ", "_")
    
    ir_api.save_df_to_csv(series_df, mapping_path)
    
    series_df = series_df[series_df["catid"] == catid]
    #create the season folder
    season_path = RESULTS + CURRENT_SEASON_FOLDER
    #create the seasons for that season folder
    create_directory(season_path)
    
    for s in series_df["id_name"]: 
        path = RESULTS + CURRENT_SEASON_FOLDER + str(s)
        if(create_directory(path) == 0):
            return 0
    return 1

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
    
    #reset the index+
    week_df = week_df.reset_index(drop = True)
    return week_df

#create week directory mappings
def create_week_directories(week_df, seasonid):
    #drop the dataframe in the directory
    season_path = RESULTS + CURRENT_SEASON_FOLDER + week_df['id_name'][0]
    csv_path = season_path + "\\" + str(seasonid) + TRACKS
    ir_api.save_df_to_csv(week_df, csv_path)
    
    for s in week_df["name"]:
        track_path = season_path + "\\" + s
        if create_directory(track_path) == 0:
            return 0
    return 1

def create_season_directories(series_df, tracks_df, catid):
    season_path = RESULTS + CURRENT_SEASON
    create_directory(season_path)
    create_series_directories(series_df, catid)
    series_df = series_df[series_df["catid"] == catid]
    for s in series_df['seasonid']:
        week_df = tracks_df[tracks_df['seasonid'] == s]
        week_df = fix_week_df(week_df)
        create_week_directories(week_df, s)

def load_series_df_for_subession_data(csv_path, df_type, df_value):
    df = pd.read_csv(csv_path)
    #0 = series_df, df_value = raceweek
    if(df_type == 0):
        df = df[df['raceweek'] == df_value]
    #1 = season_df, df_value = seasonid
    elif(df_type == 1):
        df = df[df['seasonid'] == df_value]
    df = df.reset_index(drop = True)
    return df

def obtain_subsession_data_from_series(driver, season_df, seasonid, raceweek):
    #split the season df properly, then grab the directory
    season_df = season_df[season_df['seasonid'] == seasonid]
    season_df = season_df.reset_index(drop = True)
    base_path = RESULTS + CURRENT_SEASON_FOLDER + season_df['id_name'][0] + "\\"
    
    #grab the correct week
    csv_path = base_path + str(seasonid) + TRACKS + CSV
    series_df = load_series_df_for_subession_data(csv_path, 0, raceweek)
    week_path = base_path + series_df['name'][0] + "\\"
    
    #pull the subsession data for the series
    subsession_df = ir_api.get_series_race_results(driver, str(seasonid), str(raceweek))
    csv_path = week_path + str(seasonid) + SESSIONS
    ir_api.save_df_to_csv(subsession_df, csv_path)
    
    return subsession_df
    
def obtain_race_data_from_subesssions(driver, season_df, seasonid, raceweek):
    #this is the big cheese
    season_df = season_df[season_df['seasonid'] == seasonid]
    season_df = season_df.reset_index(drop = True)    
    base_path = RESULTS + CURRENT_SEASON_FOLDER + season_df['id_name'][0] + "\\"
    csv_path = base_path + str(seasonid) + TRACKS + CSV
    series_df = load_series_df_for_subession_data(csv_path, 0, raceweek)
    week_path = base_path + series_df['name'][raceweek-1] + "\\" 
    subsession_path = week_path + str(seasonid) + SESSIONS + CSV
    subsession_df = pd.read_csv(subsession_path, index_col = 0)
    print(subsession_df)
    #for s in subsession_df['subsessionid']:
    s = subsession_df['subsessionid'][0]
    print(s)
    subsession = str(s)
    results_df = ir_api.get_combined_subsession_and_lap_data(driver, str(s))
    #print(results_df)
    results_csv_path = week_path + subsession 
    ir_api.save_df_to_csv(results_df, results_csv_path)

#this is the method that will get looped to obtain the data from iracing's servers    
def obtain_subsession_results_for_season():
    #initialize and login
    driver = ir_api.initialize_driver()
    ir_api.login(driver)
    
    #Check if the current season is different [*]
    
    #if so, change the current season to a different name, means we have to create new directories [*]
        #if week 13, create a new directory for the 13th week [*]
    
    #if not, then let's begin loading the data.
    csv_path = RESULTS + MAPPING + CURRENT_SEASON + SEASON_IDS + CSV
    try:
        #check if the mapping is created for the season
        season_df = pd.read_csv(csv_path, index_col = 0)
    except FileNotFoundError:
        #create the directories since they're not created.
        series_df = ir_api.get_series_df(driver)
        tracks_df = ir_api.get_all_tracks_per_current_season(driver)
        create_season_directories(series_df, tracks_df, 2)
    
    #for each series, loop through all of them to obtain the subsession data
    obtain_subsession_data_from_series(driver, season_df, 3164, 1)
    obtain_race_data_from_subesssions(driver, season_df, 3164, 1)

    #print(season_df)
    
    
    #quit the driver.
    driver.quit()

def main():
    obtain_subsession_results_for_season()
    
    #these will have to be refreshed every so often
    #obtain_subsession_data_from_series(driver, season_df, 3164, 1)
    
    #load_series_subsession_data(driver, season_df, 3164)
    #this uses a separate connection per series, pretty slow, about 9-10s slower
    #create_season_directories_slow(driver)
    #driver.quit()
    
    #input("Press enter to quit")   
    #ir_api.update_active()
    #driver.quit()
    

main()