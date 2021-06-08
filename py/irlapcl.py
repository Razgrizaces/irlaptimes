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
import irlaptimes as ir_lap

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
CURRENT_SEASON = "21S2"

#constants for the folder names
RESULTS = "results\\"
MAPPING = "mappings\\"
CURRENT_SEASON_FOLDER = CURRENT_SEASON + "\\"
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

#Command constant
COMMANDS = "~irlap season track irating [carid]: tells you the average time across multiple sessions for the specific irating. If the irating doesn't exist in the pool, then we calculate an average of +-25. Please note that track and season should be in number formats, see the help for more details.\nExample: ~irlap 3164 2 1350 94 would get you the VRS Sprint series for Season 2 2021, calculating 1350 as the irating and 94 as the carid. If the car id doesn't exist, we list all of them instead.\n~irlap i[nfo] season [v]: Default tells you the tracks for the season you're looking for.\n[v] is a flag that also lets you know the track and cars for that series, you can omit if you want. t is track, c is cars and b is both.\nExample: ~irlap i 3164 t would let you know the tracks for VRS Sprint Series Season 2 2021.\n~irlap -h[elp]: Tells you the current seasons and prints this quote again.\n~irlap q quits the bot."

def load_df_and_calculate_average_irating(seasonid, trackid, irating, carid):
    return

def print_season_fields(seasonid, verbosity):
    return

def print_seasons():
    return

def testing_user_input(driver, file_name):
    user_input = ""
    while user_input != "q":
        user_input = input(COMMANDS)
        try:
            input_data = user_input.split(" ")
            if(int(input_data[1]) > 0):
                if(len(input_data) == 3):
                    load_df_and_calculate_average_irating(int(input_data[1]), int(input_data[2]), int(input_data[3]), -1)
                elif(len(input_data == 4):
                    load_df_and_calculate_average_irating(int(input_data[1]), int(input_data[2]), int(input_data[3]), int(input_data[4]))
                else:
                    print("Please refer to the commands again.")
            elif(input_data[1] == 'i'):
                if(len(input_data) == 2):
                    print_season_fields(int(input_data[2]), 't')
                elif(len(input_data) == 3):
                    print_season_fields(int(input_data[2]), input_data[3])
                else:
                    print("Please refer to the commands again.")
            elif(input_data[1] == '-h' || input_data[1] == '-help'):
                print_seasons()
            elif:
                print("Please enter a valid command.")
        except IndexError:
            print("Incorrect input... please try again...")
        except ValueError: 
            print("Please enter a valid id.")


def main():

    season_df = ir_lap.load_season_df(None)
    season_df = season_df[season_df['catid'] == 2]
    
    try:
        user_input = input("Please enter a season id: ")
        wanted_ids = [int(user_input)]
    except ValueError:
        print("Please enter a valid ID.")
        return 
    season_df = season_df[season_df['seasonid'].isin(wanted_ids)]
    season_df = season_df.reset_index(drop = True)
    
    #grab the series
    series_df = ir_lap.slice_season_df_from_seasonid(season_df, user_input)
    base_path = RESULTS_PATH + season_df['id_name'].iloc[0] + "\\"
    track_df = ir_lap.obtain_track_data_for_series(season_df, base_path, -1)
    
    print(track_df)
    
    try:
        print(track_df['name'])
        user_input = input("Please enter a track id: ")
        selected_track = track_df.iloc[int(user_input)]
    except ValueError:
        print("Please enter a valid ID.")
        return 
    
    subsessions_path = base_path + selected_track['name'] + "\\"
    csv_path = subsessions_path + str(selected_track['seasonid']) + "_" + str(selected_track['raceweek']) + SESSIONS + CSV 
    try:
        subsession_df = pd.read_csv(csv_path, index_col = 0)
        #create one fat ass subsession_df
        #week_lap_data_df = combine_session_dataframes(subsession_df, subsessions_path, t)
        fat_df_path = subsessions_path + str(selected_track['seasonid']) + "_" + str(selected_track['raceweek']) + LAP_DATA + MMM + CSV
        week_lap_data_df = pd.read_csv(fat_df_path, index_col = 0)
        
        print(week_lap_data_df)
        
        user_input = input("Please enter an irating: ")
        print(week_lap_data_df[week_lap_data_df['oldirating'] == int(user_input)])
        
    except FileNotFoundError:
        return
                
main()