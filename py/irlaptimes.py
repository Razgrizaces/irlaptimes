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
    except:
        print("The directory " + dir_name + " exists.")

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
        create_directory(path)

def fix_week_df(week_df):
    #adds one to the raceweek since it starts at 0
    week_df['raceweek'] = week_df['raceweek'].astype(int) + 1
    week_df['raceweek'] = week_df['raceweek'].astype(str)
 
    #creates the folder for the week.
    week_df['name'] = week_df['raceweek'] + "#" + week_df['name'] + "#" + week_df['config']
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
    season_path = RESULTS + CURRENT_SEASON_FOLDER + week_df['id_name'].iloc[0]
    csv_path = season_path + "\\" + str(seasonid) + TRACKS
    ir_api.save_df_to_csv(week_df, csv_path)
    
    for s in week_df["name"]:
        track_path = season_path + "\\" + s
        create_directory(track_path)

def create_season_directories(series_df, tracks_df, catid):
    season_path = RESULTS + CURRENT_SEASON
    create_directory(season_path)
    create_series_directories(series_df, catid)
    series_df = series_df[series_df["catid"] == catid]
    for s in series_df['seasonid']:
        week_df = tracks_df[tracks_df['seasonid'] == s]
        week_df = fix_week_df(week_df)
        create_week_directories(week_df, s)

#dfvalue =-1 means we load the whole df
def load_series_df_for_subession_data(csv_path, df_type, df_value):
    df = pd.read_csv(csv_path, index_col = 0)
    #0 = series_df, df_value = raceweek
    if(df_type == 0):
        if(df_value != -1):
            df = df[df['raceweek'] == df_value]
    #1 = season_df, df_value = seasonid
    elif(df_type == 1):
        if(df_value != -1):
            df = df[df['seasonid'] == df_value]
    df = df.reset_index(drop = True)
    return df

def slice_season_df_from_seasonid(season_df, seasonid):
    season_df = season_df[season_df['seasonid'] == seasonid]
    season_df = season_df.reset_index(drop = True)
    return season_df
    
def obtain_track_data_for_series(season_df, base_path, raceweek):
    base_path = RESULTS + CURRENT_SEASON_FOLDER + season_df['id_name'].iloc[0] + "\\"
    csv_path = base_path + str(season_df['seasonid'].iloc[0]) + TRACKS + CSV
    series_df = load_series_df_for_subession_data(csv_path, 0, raceweek)
    return series_df

def obtain_subsession_data_from_series(driver, season_df, raceweek):
    #split the season df properly, then grab the directory
    seasonid = season_df['seasonid'].iloc[0]
    base_path = RESULTS + CURRENT_SEASON_FOLDER + season_df['id_name'].iloc[0] + "\\"
    
    #grab the correct week
    series_df = obtain_track_data_for_series(season_df, base_path, raceweek)
    week_path = base_path + series_df['name'].iloc[0] + "\\"
    
    #we moved the raceweek up 1, so gotta correct it to get the right data
    ir_raceweek = raceweek-1
    
    csv_path = week_path + str(seasonid) + "_" + str(raceweek) +  SESSIONS
    #pull the subsession data for the series
    try: 
        csv_file_path = csv_path + CSV
        subsession_df = pd.read_csv(csv_file_path, index_col = 0)
        #check the last subsession and see if it's pulled
        if(subsession_df.empty == False):
            last_subsession = subsession_df['subsessionid'].iloc[-1]
            ls_results_csv_path = week_path + str(last_subsession) 
            results_csv_file_path = ls_results_csv_path + CSV
            results_df = pd.read_csv(results_csv_file_path, index_col = 0)
            return subsession_df
    #if it doesn't exist, we must pull anyways
    except FileNotFoundError:
        subsession_df = ir_api.get_series_race_results(driver, str(seasonid), str(ir_raceweek))
    print(subsession_df)
    if(subsession_df.empty != True):
        ir_api.save_df_to_csv(subsession_df, csv_path)
    return subsession_df
    
def obtain_race_data_from_subesssions(driver, season_df, raceweek):

    seasonid = season_df['seasonid'].iloc[0]
    base_path = RESULTS + CURRENT_SEASON_FOLDER + season_df['id_name'].iloc[0] + "\\"
    
    series_df = obtain_track_data_for_series(season_df, base_path, raceweek)
    #next we load the series with the race week to grab the sessions
    week_path = base_path + series_df['name'].iloc[0] + "\\" 
    
    subsession_path = week_path + str(seasonid) + "_" + str(raceweek) + SESSIONS + CSV
    subsession_df = pd.DataFrame(index = [], columns = [])
    try:
        subsession_df = pd.read_csv(subsession_path, index_col = 0)
    #if subsession data doesn't exist, pull it
    except FileNotFoundError:
        obtain_subsession_data_from_series(driver, season_df, raceweek)
    #counts the subsession number
    subsession_num = 0
    
    #check to see if the last subsession is made or not
    last_subsession = subsession_df['subsessionid'].iloc[-1]
    ls_results_csv_path = week_path + str(last_subsession) 
    try:
        results_csv_file_path = ls_results_csv_path + CSV
        results_df = pd.read_csv(results_csv_file_path, index_col = 0)
        print("Last Subsession")
        return results_df
    #if it does, we can skip the loop pretty much.
    except FileNotFoundError:
        for s in subsession_df['subsessionid']:
            subsession = str(s)
            print(str(subsession_num) + ": " + str(subsession))
            subsession_num = subsession_num + 1
            results_csv_path = week_path + subsession 
            #first we should check if s already exists as a csv file or not
            try:
                results_csv_file_path = results_csv_path + CSV
                results_df = pd.read_csv(results_csv_file_path, index_col = 0)
            #if it doesn't, gotta pull it from iracing.
            except FileNotFoundError:
                results_df = ir_api.get_combined_subsession_and_lap_data(driver, str(s))
                if(results_df.empty == False):
                    ir_api.save_df_to_csv(results_df, results_csv_path)
        return pd.DataFrame(index = [], columns = [])

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
    season_df = pd.DataFrame(columns = ['A','B','C','D'])
    try:
        #check if the mapping is created for the season
        print("reading the season csv...")
        season_df = pd.read_csv(csv_path, index_col = 0)
    except FileNotFoundError:
        #create the directories since they're not created.
        print("Creating Directories...")
        series_df = ir_api.get_series_df(driver)
        tracks_df = ir_api.get_all_tracks_per_current_season(driver)
        create_season_directories(series_df, tracks_df, 2)
    
    #for each series, loop through all of them to obtain the subsession data
    #first, we obtain the subsession data to get the subsessions we missed out on
    
    season_df = season_df[season_df['catid'] == 2]
    wanted_ids = [3124, 3157, 3164, 3166]
    season_df = season_df[season_df['seasonid'].isin(wanted_ids)]
    season_df = season_df.reset_index(drop = True)
    
    print(season_df)
    for s in season_df['seasonid']:
        print("Subsession: " + str(s))
        #obtain the series to load
        series_df_to_load = slice_season_df_from_seasonid(season_df, s)
        
        #obtain the amount of weeks we have to load for
        base_path = RESULTS + CURRENT_SEASON_FOLDER + season_df['id_name'].iloc[0] + "\\"
        track_df = obtain_track_data_for_series(season_df, base_path, -1)
        for t in track_df['raceweek']:
            print(str(t))
            #this only returns if we have the last subsession
            results_df = obtain_subsession_data_from_series(driver, series_df_to_load, t)
            #print(results_df)
            if(results_df.empty == False):
                obtain_race_data_from_subesssions(driver, series_df_to_load, t)
            else:
                break
        
    #quit the driver.
    driver.quit()

def main():
    
    obtain_subsession_results_for_season()
    
    #these will have to be refreshed every so often
    #obtain_subsession_data_from_series(driver, season_df, 3164, 1)
    
    
    #input("Press enter to quit")   
    #ir_api.update_active()
    #driver.quit()
    

main()