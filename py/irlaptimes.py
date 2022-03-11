from datetime import date
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
CARS = "_cars"
MMM = "_mmm"

#you should change this for the season, 
PREVIOUS_SEASON = "21S4"
global CURRENT_SEASON
CURRENT_SEASON = "22S1"

#constants for the folder names
RESULTS = "results/"
MAPPING = "mappings/"
CURRENT_SEASON_FOLDER = CURRENT_SEASON + "/"
RESULTS_PATH =  RESULTS + CURRENT_SEASON_FOLDER

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
    series_df['season'] = CURRENT_SEASON
    #create the season folder
    season_path = RESULTS_PATH
    #create the seasons for that season folder
    create_directory(season_path)
    
    for s in series_df["id_name"]: 
        path = RESULTS_PATH + str(s)
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
    week_df['name'] = week_df['name'].str.replace("%C3%B9", "ù")
    week_df['name'] = week_df['name'].str.replace("%C3%B3", "ó")
    week_df['name'] = week_df['name'].str.replace("%C3%83", "Ã")
    
    #adding this to match the directories
    week_df['id_name'] = week_df['seasonid'].astype(str) + "#" + week_df['seriesname'].str.replace("+","_")
    
    #reset the index+
    week_df = week_df.reset_index(drop = True)
    return week_df

#create week directory mappings
def create_week_directories(week_df, seasonid, driver):
    #drop the dataframe in the directory
    try:
        season_path = RESULTS_PATH + week_df['id_name'].iloc[0]
    except IndexError:
        week_df = ir_api.get_all_tracks_per_non_current_season(driver)
        week_df = week_df[week_df['seasonid'] == seasonid]
        week_df = fix_week_df(week_df)
    csv_path = season_path + "/" + str(seasonid) + TRACKS
    ir_api.save_df_to_csv(week_df, csv_path)
    
    for s in week_df["name"]:
        track_path = season_path + "/" + s
        create_directory(track_path)

def create_season_directories(series_df, tracks_df, catid, driver):
    season_path = RESULTS + CURRENT_SEASON
    create_directory(season_path)
    create_series_directories(series_df, catid)
    series_df = series_df[series_df["catid"] == catid]
    for s in series_df['seasonid']:
        week_df = tracks_df[tracks_df['seasonid'] == s]
        week_df = fix_week_df(week_df)
        create_week_directories(week_df, s, driver)

#dfvalue =-1 means we load the whole df
def load_series_df_for_subsession_data(csv_path, df_type, df_value):
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
    
def obtain_track_data_for_series(season_df, raceweek, season):
    
    if season != CURRENT_SEASON:
        base_path = RESULTS + season + "/" + season_df['id_name'].iloc[0] + "/"
    else:
        #if not, then let's begin loading the data.
        base_path = RESULTS_PATH + season_df['id_name'].iloc[0] + "/"
        
    csv_path = base_path + str(season_df['seasonid'].iloc[0]) + TRACKS + CSV
    series_df = load_series_df_for_subsession_data(csv_path, 0, raceweek)
    return series_df

def obtain_subsession_data_from_series(driver, season_df, raceweek, season):
    #split the season df properly, then grab the directory
    seasonid = season_df['seasonid'].iloc[0]

    if season != CURRENT_SEASON:
        base_path = RESULTS + season + "/" + season_df['id_name'].iloc[0] + "/"
    else:
        #if not, then let's begin loading the data.
        base_path = RESULTS_PATH + season_df['id_name'].iloc[0] + "/"

    #grab the correct week
    series_df = obtain_track_data_for_series(season_df, raceweek, season)
    week_path = base_path + series_df['name'].iloc[0] + "/"
    
    #we moved the raceweek up 1, so gotta correct it to get the right data
    ir_raceweek = raceweek-1
    
    csv_path = week_path + str(seasonid) + "_" + str(raceweek) +  SESSIONS
    try: 
        #pull our subsession file for the series
        csv_file_path = csv_path + CSV
        subsession_df = pd.read_csv(csv_file_path, index_col = 0)
        #compare iracing's pull vs what we currently have
        if(subsession_df.empty == False):
            #sort the df and pull the last one
            ir_subsession_df = ir_api.get_series_race_results(driver, str(seasonid), str(ir_raceweek))
            ir_subsession_df = ir_subsession_df.sort_values(by='subsessionid')
            ir_last_subsession = ir_subsession_df['subsessionid'].iloc[-1]
            
            #pull the last subsession and see if it's different
            last_subsession = subsession_df['subsessionid'].iloc[-1]
            print(ir_last_subsession, last_subsession)
            if(ir_last_subsession != last_subsession):
                subsession_df = ir_subsession_df
    #if it doesn't exist, we must pull anyways
    except FileNotFoundError:
        subsession_df = ir_api.get_series_race_results(driver, str(seasonid), str(ir_raceweek))
    if(subsession_df.empty == False):
        subsession_df = subsession_df.drop_duplicates(subset = "subsessionid")
        ir_api.save_df_to_csv(subsession_df, csv_path)
    return subsession_df
    
def obtain_race_data_from_subesssions(driver, season_df, raceweek, season):

    seasonid = season_df['seasonid'].iloc[0]
    
    if season != CURRENT_SEASON:
        base_path = RESULTS + season + "/" + season_df['id_name'].iloc[0] + "/"
    else:
        #if not, then let's begin loading the data.
        base_path = RESULTS_PATH + season_df['id_name'].iloc[0] + "/"
        
    series_df = obtain_track_data_for_series(season_df, raceweek, season)
    #next we load the series with the race week to grab the sessions
    week_path = base_path + series_df['name'].iloc[0] + "/" 
    
    subsession_path = week_path + str(seasonid) + "_" + str(raceweek) + SESSIONS + CSV
    subsession_df = pd.DataFrame(index = [], columns = [])
    try:
        subsession_df = pd.read_csv(subsession_path, index_col = 0)
    #if subsession data doesn't exist, pull it
    except FileNotFoundError:
        obtain_subsession_data_from_series(driver, season_df, raceweek, season)
    #counts the subsession number
    subsession_num = 0
    
    #check to see if the last subsession is made or not
    last_subsession = subsession_df['subsessionid'].iloc[-1]
    ls_results_csv_path = week_path + str(last_subsession) 
    try:
        results_csv_file_path = ls_results_csv_path + CSV
        results_df = pd.read_csv(results_csv_file_path, index_col = 0)
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
 
#season should refer to the year number + season number like 21S2
def load_season_df(driver, season):
       
    #loading an old season, so we have to load from a previous one. 
    if season != CURRENT_SEASON:
        csv_path = RESULTS + MAPPING + season + SEASON_IDS + CSV
    else:
        #if not, then let's begin loading the data.
        csv_path = RESULTS + MAPPING + CURRENT_SEASON + SEASON_IDS + CSV
    season_df = pd.DataFrame(columns = ['A','B','C','D'])
    try:
        #check if the mapping is created for the season
        print("reading the season csv...")
        season_df = pd.read_csv(csv_path, index_col = 0)
        print(season_df)
        if driver is not None:
            tracks_df = ir_api.get_all_tracks_per_current_season(driver)
            print(tracks_df)
            create_season_directories(season_df, tracks_df, 2, driver)
    except FileNotFoundError:
        #create the directories since they're not created.
        print("Creating Directories...")
        series_df = ir_api.get_series_df(driver)
        tracks_df = ir_api.get_all_tracks_per_current_season(driver)
        create_season_directories(series_df, tracks_df, 2, driver)
    return season_df

def current_season_check(driver):
    #load the 'current' seasons id
    global CURRENT_SEASON
    current_season_df = load_season_df(driver, CURRENT_SEASON)
    
    ir_active_season_df = ir_api.get_series_df(driver)
    
    ir_13th_week = ir_active_season_df[ir_active_season_df['seriesname'].str.contains('13th Week')]
    if(ir_13th_week.size == 0):
        ir_active_season_df = ir_active_season_df.sort_values(by='seasonid')
        ir_active_season_df = ir_active_season_df.reset_index(drop = True)

        print(ir_active_season_df)
        #check if it's empty, if so, gotta create new ones for the new season
        if not current_season_df.empty:
            sym_diff = len(set(current_season_df.seasonid).symmetric_difference(ir_active_season_df.seasonid))
        else:
            sym_diff = len(ir_active_season_df.seasonid) #the current season df is empty
        #check if the symmetric difference is greater than 0
        #if the sym_diff > 0 then it's possible we could have one or two extra seasons due to special events, so we should filter that
        #week 13 usually is like 5 special events-ish, so should be:
        #sym_diff >=1 & <=5: update the current season, but don't update the string
        if(sym_diff >=1 and sym_diff <=5):
            csv_path = RESULTS + MAPPING + CURRENT_SEASON + SEASON_IDS
            ir_api.save_df_to_csv(ir_active_season_df, csv_path)
        #sym_diff > 5: update the string and the current season
        elif (sym_diff > 5):
            cs_substring = CURRENT_SEASON.split ("S")
            last_two_year_digits = date.today().year-2000
            #year is the same, advance the season
            if(last_two_year_digits == int(cs_substring[0])):
                CURRENT_SEASON = cs_substring[0] + "S" + str(int(cs_substring[1])+1)
            else:
                CURRENT_SEASON = str(int(cs_substring[0]+1)) + "S1"
            #save the df to the new path
            print(CURRENT_SEASON)
            csv_path = RESULTS + MAPPING + CURRENT_SEASON + SEASON_IDS
            ir_api.save_df_to_csv(ir_active_season_df, csv_path)
            print(ir_active_season_df)
            create_series_directories(ir_active_season_df, ir_active_season_df.catid)
            driver.quit()
            return CURRENT_SEASON
        #sym_diff == 0: do nothing; season is the same
        return CURRENT_SEASON
    else:
        return CURRENT_SEASON

def raceweek_check(season_df, track_df, season):
    season_id_name = season_df['id_name'].iloc[0]
    
    if season != CURRENT_SEASON:
        base_path = RESULTS + season + "/" + season_df['id_name'].iloc[0] + "/"
    else:
        #if not, then let's begin loading the data.
        base_path = RESULTS_PATH + season_df['id_name'].iloc[0] + "/"
        
    last_raceweek = 0
    for n in track_df['name']:
        try:
            sessions_csv_path = base_path + n + "/" + str(season_df['seasonid'].iloc[0]) + "_" + str(n[0]) + SESSIONS + CSV
            pd.read_csv(sessions_csv_path, index_col = 0)
            last_raceweek = last_raceweek + 1
        except FileNotFoundError:
            return last_raceweek

#this is the method that will get looped to obtain the data from iracing's servers    
#we only use the driver here
def obtain_subsession_results_for_season():
    #initialize and login
    driver = ir_api.initialize_driver()
    ir_api.login(driver)
    
    #Check if the current season is different [*]
    
    #pull the active season ids
    #if so, change the current season to a different name, means we have to create new directories [*]
        #if week 13, create a new directory for the 13th week [*]
    
    #for each series, loop through all of them to obtain the subsession data
    #first, we obtain the subsession data to get the subsessions we missed out on
    
    season_df = load_season_df(driver, CURRENT_SEASON)
    season_df = season_df[season_df['catid'] == 2]
    wanted_ids = [3529,3520,3522]
    season_df = season_df[season_df['seasonid'].isin(wanted_ids)]
    season_df = season_df.reset_index(drop = True)
    
    print(season_df)
    for s in season_df['seasonid']:
        print("Subsession: " + str(s))
        #obtain the series to load
        series_df_to_load = slice_season_df_from_seasonid(season_df, s)
        #obtain the amount of weeks we have to load for
        track_df = obtain_track_data_for_series(series_df_to_load, -1, CURRENT_SEASON)
        #checks what's the last raceweek we ran on
        last_raceweek = raceweek_check(series_df_to_load, track_df, CURRENT_SEASON)
        for r in track_df['raceweek']:
            print("Race week: " + str(r))
            if(r >= last_raceweek):
                #this only breaks if we have the last subsession
                results_df = obtain_subsession_data_from_series(driver, series_df_to_load, r, CURRENT_SEASON)
                if(results_df.empty == False):
                    obtain_race_data_from_subesssions(driver, series_df_to_load, r, CURRENT_SEASON)
                else:
                    break
        
    #quit the driver.
    driver.quit()

def combine_session_dataframes(subsession_df, subsessions_path, track_df, driver):
    if subsession_df.empty == 0:
        #create a mother df so we can combine all the data into one fat df
        columns_to_keep = ['weather_temp_value','custid','oldirating','carid','lap_time','ccName', 'subsessionid','lapnum', 'flags']
        session_data_df = pd.DataFrame(columns = columns_to_keep)

        for s in subsession_df['subsessionid']:
            csv_path = subsessions_path + str(s) + CSV
            print(csv_path)
            try:
                session_df = pd.read_csv(csv_path, index_col = 0)
            except FileNotFoundError:
                #if it's not found, maybe we can try making the driver and pulling it?
                session_df = ir_api.get_combined_subsession_and_lap_data(driver, str(s))
                print(session_df)
                print(csv_path + " not found")
            if(session_df.empty == False):
                #session_df = trim_session_df(session_df, columns_to_keep)
                session_df = session_df[columns_to_keep]
                session_df = session_df[session_df['lapnum'] != 0]
                session_data_df = pd.concat([session_data_df, session_df])
        print("Finished reading all subsessions.")
        print(session_data_df)
        full_data_csv_path = subsessions_path + str(track_df['seasonid']) + "_" + str(track_df['raceweek']) + LAP_DATA
        session_data_df = session_data_df.sort_values(by = ['custid','subsessionid'])
        session_data_df = session_data_df.reset_index(drop = True)
        
        ir_api.save_df_to_csv(session_data_df, full_data_csv_path)
        
        return session_data_df

def add_type_to_results_df(lap_time_df, results_df, type_num):
    results_df = pd.merge(results_df, lap_time_df, how = 'inner', on = 'custid')
    results_df['type'] = type_num
    return results_df

def subset_df_with_columns(df_to_subset, columns_to_keep):
    df_to_subset = df_to_subset[columns_to_keep]
    df_to_subset = df_to_subset.drop_duplicates(subset = 'custid')
    df_to_subset = df_to_subset.reset_index(drop = True)
    return df_to_subset

def create_min_max_mean_for_results_df(results_df):
    
    columns_to_keep = ['weather_temp_value', 'custid', 'oldirating', 'carid', 'ccName', 'subsessionid']
    combine_df = subset_df_with_columns(results_df, columns_to_keep)
    
    min_lap_time = results_df.groupby(by=['custid']).lap_time.min()
    avg_lap_time = results_df.groupby(by=['custid']).lap_time.mean()
    max_lap_time = results_df.groupby(by=['custid']).lap_time.max()
    
    combine_df_min = add_type_to_results_df(min_lap_time, combine_df, "min")
    combine_df_avg = add_type_to_results_df(avg_lap_time, combine_df, "avg")
    combine_df_max = add_type_to_results_df(max_lap_time, combine_df, "max")
    
    combine_df = pd.concat([combine_df_min, combine_df_avg, combine_df_max])
    combine_df = combine_df.reset_index(drop = True)
    
    return combine_df
    
def trim_session_df(results_df, columns_to_keep):
    
    #trim the unacceptable laps
    unacceptable_flags = 0B011111111111111
    results_df = results_df[results_df['flags']&unacceptable_flags == 0]
    results_df = results_df[results_df['lap_time'] > 0]
    
    #trim the columns
    results_df = results_df[columns_to_keep]
    #based on the 1.07 rule in F1, might tweak this a bit
    cutoff_time = results_df['lap_time'].min(axis=0) * 1.07
    max_time = results_df['lap_time'].max(axis=0)
    
    print(max_time, cutoff_time)
    #print(round(max_time/cutoff_time,2))'
    #print(cutoff_time) 
    #takes the laps that are within the cutoff time
    results_df = results_df[results_df['lap_time'] < cutoff_time]
    
    #print(results_df['flags'])
    return results_df

def create_mmm_df_for_seasons(season_df):
    for s in season_df:
        series_df = slice_season_df_from_seasonid(season_df, s)
        base_path = RESULTS + season_df['season'][0] + "/" + series_df['id_name'].iloc[0] + "/"
        print(base_path)
        track_df = obtain_track_data_for_series(series_df, -1,  season_df['season'][0])
        for t in track_df.iloc:
            subsessions_path = base_path + t['name'] + "/"
            print(t['raceweek'], t['seasonid'])
            csv_path = subsessions_path + str(t['seasonid']) + "_" + str(t['raceweek']) + SESSIONS + CSV 
            mmm_df = pd.DataFrame()
            try:
                mmm_df_path = subsessions_path + str(t['seasonid']) + "_" + str(t['raceweek']) + LAP_DATA + CSV
                mmm_df = pd.read_csv(mmm_df_path, index_col=0)
            except FileNotFoundError:
                print("mmm df doesn't exist, so we'll create one")
                #was the data pulled?
            if mmm_df.empty == True:
                try:
                    #this obtains all the subsessions for that week
                    subsession_df = pd.read_csv(csv_path, index_col = 0)
                    print(csv_path + "Found")
                    #print("Combining data for subsessions... for week " + str(t['raceweek']))
                    week_lap_data_df = combine_session_dataframes(subsession_df, subsessions_path, t)
                    fat_df_path = subsessions_path + str(t['seasonid']) + "_" + str(t['raceweek']) + LAP_DATA
                    fat_df_csv_path = fat_df_path + CSV
                    #read the session df, if it exists
                    #week_lap_data_df = pd.read_csv(fat_df_csv_path, index_col = 0)
                    print("Calculating avg time per irating per week for week " + str(t['raceweek']))
                    print(fat_df_path)
                    #calculate_avg_time_per_irating_per_week(week_lap_data_df, 1350, -1, fat_df_path)
                except FileNotFoundError:
                    print(csv_path + " Not found")
                   

def test_loop():
    season_df = load_season_df(None, "22S1")
    season_df = season_df[season_df['catid'] == 2]
    wanted_ids = [3529]
    #print(season_df['seasonid'])
    season_df = season_df[season_df['seasonid'].isin(wanted_ids)]
    season_df = season_df.reset_index(drop = True)
    #log into the api in case we need to pull subsessions
    driver = ir_api.initialize_driver()
    ir_api.login(driver)
    season = "22S1"
    #grab the series
    for i in wanted_ids:
        series_df = slice_season_df_from_seasonid(season_df, i)
        base_path = RESULTS + season + "/" + series_df['id_name'].iloc[0] + "/"
        #print(base_path)
        track_df = obtain_track_data_for_series(series_df, -1,  season)
        for t in track_df.iloc:
            subsessions_path = base_path + t['name'] + "/"
            print(t['raceweek'], t['seasonid'])
            csv_path = subsessions_path + str(t['seasonid']) + "_" + str(t['raceweek']) + SESSIONS + CSV    
            mmm_df = pd.DataFrame()
            try:
                mmm_df_path = subsessions_path + str(t['seasonid']) + "_" + str(t['raceweek']) + LAP_DATA + CSV
                mmm_df = pd.read_csv(mmm_df_path, index_col=0)
            except FileNotFoundError:
                print("lap data df doesn't exist, so we'll create one")
                #was the data pulled?
                print(mmm_df)
            if mmm_df.empty == True:
                try:
                    #this obtains all the subsessions for that week
                    subsession_df = pd.read_csv(csv_path, index_col = 0)
                    print(csv_path + "Found")
                    #print("Combining data for subsessions... for week " + str(t['raceweek']))
                    week_lap_data_df = combine_session_dataframes(subsession_df, subsessions_path, t, driver)
                    fat_df_path = subsessions_path + str(t['seasonid']) + "_" + str(t['raceweek']) + LAP_DATA
                    fat_df_csv_path = fat_df_path + CSV
                    #read the session df, if it exists
                    #week_lap_data_df = pd.read_csv(fat_df_csv_path, index_col = 0)
                    print("Calculating avg time per irating per week for week " + str(t['raceweek']))
                    print(fat_df_path)
                    #calculate_avg_time_per_irating_per_week(week_lap_data_df, 1350, -1, fat_df_path)
                except FileNotFoundError:
                    print(csv_path + " Not found")

#formats the time to make it simlilar to how iracing displays time
def format_duration(x):
    seconds, milliseconds  = divmod(x, 10000)
    milliseconds = int(milliseconds/10)
    minutes, seconds = divmod(seconds, 60)
    seconds = int(seconds)
    minutes = int(minutes)
    return '{:02d}:{:02d}:{:3d}'.format(minutes, seconds, milliseconds)

def main():
    
    test_loop() 
    #lap_data = pd.read_csv("results\\21S3\\3280#VRS_GT_Sprint_Series\\1#Road_Atlanta#Full_Course\\3280_1_lap_data.csv", index_col = 0)
    #print(lap_data)
    #lap_data['lap_time_iracing'] = lap_data['lap_time'].apply(format_duration)
    #print(lap_data['lap_time_iracing'])
    
    #obtain_subsession_results_for_season()
    
    #these will have to be refreshed every so often
    #input("Press enter to quit")   
    #ir_api.update_active()
    #driver.quit()
    

main()
