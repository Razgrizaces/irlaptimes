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

#this file logs you into iracing to obtain the data that you want
#if you're looking to manipulate the data look at irldmanip.py and create your own file

#Constant URLs
LOGIN_URL = "https://members.iracing.com/membersite/login.jsp"
SUBSESSION_RESULTS_URL = "https://members.iracing.com/membersite/member/GetSubsessionResults?subsessionID="
SERIES_RACE_RESULTS_URL = "https://members.iracing.com/memberstats/member/GetSeriesRaceResults?seasonid="
LAP_CHART_URL = "https://members.iracing.com/membersite/member/GetLapChart?&subsessionid="
SEASONS_URL = "https://members.iracing.com/membersite/member/GetSeasons?"

#Constants to modify URLs
AND = "&"
CAR_CLASS_ID = "carclassid=-1"
SIM_SES_NUM = "simsessnum=0"
RACE_WEEK = "raceweek="
ONLY_ACTIVE = "onlyActive="
SEASON_ALL_FIELDS = "fields=year,quarter,seriesshortname,seriesid,active,catid,licenseeligible,islite,carclasses,tracks,start,end,cars,raceweek,category,serieslicgroupid,carid,seasonid,seriesid"

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
RAW_RESULTS = "results\\raw\\"
MANIPULATED_RESULTS = "results\\manipulated\\"

#you should change this for the season
CURRENT_SEASON = "21S2"

#modified constants, create your own here, I'm just using these to grab the ids. 
SEASON_CAR_FIELDS = "fields=seasonid,seriesname,cars,carid"
SEASON_SERIES_FIELDS = "fields=seasonid,seriesname,catid,lowerseasonshortname"
SEASON_TRACK_FIELDS = "fields=seasonid,seriesname,tracks,trackid"

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
COMMANDS = "Commands:\ns(ubsession) n(umber)\n\tobtains subsession data for the given number.\nr(ace) s(eason id) w(eek number)\n\tgets the races for that season in that week\nl(ap chart) s(ubsession)\n\tgets the lap chart data for that subsession\nm(ember) i(d)\n\tgets the data for that member\ne(season) o(nly active) t(ype of data)\n\tupdates all of the current season/tracks/cars"

# -- SELENIUM / LOGIN METHODS --

# automatically logs in using your credentials so you don't have to
def login_using_credentials(driver, path):
    with open (path,"r") as read_file:
        credentials = json.load(read_file)
    u = driver.find_element_by_name('username')
    u.send_keys(credentials["user"])
    p = driver.find_element_by_name('password')
    p.send_keys(credentials["pw"])
    driver.find_element_by_id("submit").click()

#this initializes the chrome driver. Please note you might have to update chrome-driver if it's not the same as current.
def initialize_driver():
    #setting chrome options; note this uses chromedriver_81, use whatever driver you have
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--disable-extensions"); # disabling extensions
    chrome_options.add_argument("--disable-gpu"); # applicable to windows os only
    chrome_options.add_argument("--disable-dev-shm-usage"); # overcome limited resource problems
    chrome_options.add_argument("--no-sandbox");
    chrome_options.add_argument("--remote-debugging-port=9225");
    driver = webdriver.Chrome("dependencies\\chromedriver.exe", options=chrome_options)
    return driver

#processes login to iRacing, probably only need to do this once or once every few hours
def login (driver):
    #driver.get essentially loads the url of the page, here we're using the iracing login
    driver.get(LOGIN_URL)
    
    # here we're putting in our credentials by selenium, you can just comment this, do it yourself and enter it
    # alternatively, use your own credentials by filling in 
    login_using_credentials(driver, "credentials.json")

# JSON/DF METHODS

#if you need it, creates the full json so you can look at the data and select what you want
def create_full_json_from_url(driver, url, base_file_name):
    driver.get(url)
    data = json.loads(driver.find_element_by_xpath("//pre").text)
    file_name = base_file_name + FULL_JSON
    with open(file_name, "w") as write_file:
        write_file.write(json.dumps(data))

#this we know that the data is sitting 1-8
def get_headers_from_json(data, parse):
    data = data[parse]
    headers = []
    for i in range (1, 9):
        try:
            headers.append(data[str(i)])
        except KeyError:
            print("No data found.")
            break
    return headers

def get_json_from_url(driver, url):
    driver.get(url)
    data = json.loads(driver.find_element_by_xpath("//pre").text)
    return data

def create_json_file(data, file_name):
    file_name = file_name + JSON
    with open(file_name, "w") as write_file:
        write_file.write(json.dumps(data))

#creates a parsed json based parse
def parse_json(data, parse):
    if parse != "":
        data = data[parse]
    return data

def create_df_from_json_fields(data, kept_fields):
    new_json = dict((field, str(data[field])) for field in kept_fields if field in data)
    df = pd.DataFrame(new_json, index=[0], columns = kept_fields)
    return df

def create_df_from_json_data(json_data):
    df = pd.DataFrame(json_data)
    return df

def save_df_to_csv(df, file_name):
    csv_file_name = file_name + CSV
    df.to_csv(csv_file_name, encoding='utf-8', mode = "+w")

#lines up the columns with the amount for the df we have to 
def create_df_to_add_columns(df, size):
    return_df = pd.DataFrame(np.repeat(df.values, size, axis=0), columns = df.columns)
    return return_df

def keep_wanted_columns(df, wanted_columns):
    unwanted_columns = []
    for column in df.columns:
        if column not in wanted_columns:
            unwanted_columns.append(column)
    ', '.join(unwanted_columns)
    df = df.drop(unwanted_columns, axis = 1)
    return df
# -- DATA PULLING METHODS -- 

#gets url or file_name from field string fields
def create_params_for_season(only_active, field_type_int, is_url):
    field_string = SEASON_ALL_FIELDS
    type_string = "all"
    active_string = "active"
    
    #for the url later
    if(field_type_int == 0):
        field_string = SEASON_ALL_FIELDS
    elif(field_type_int == 1):
        field_string = SEASON_CAR_FIELDS
        type_string = 'cars'
    elif(field_type_int == 2):
        field_string = SEASON_SERIES_FIELDS
        type_string = 'season'
    elif(field_type_int == 3):
        field_string = SEASON_TRACK_FIELDS
        type_string = 'tracks'
    else:
        print("Invald input, putting default.")
    if (only_active == 0):
        active_string = "inactive_"
    #is_url = return url; otherwise return file_name
    if (is_url == 1):
        output = SEASONS_URL + ONLY_ACTIVE + str(only_active) + AND + field_string
    else:
        output = RAW_RESULTS + active_string + SEASON_RESULTS + type_string
    return output
    
#obtains the season df from iracing
def get_df_from_season(driver, only_active, field_type_int):
    url = create_params_for_season(only_active, field_type_int, 1)
    json_data = get_json_from_url(driver, url)
    season_df = create_df_from_json_data(json_data)
    return season_df

def loop_through_season_df(season_df, type_string):
    season_ids = season_df['seasonid'].tolist()
    type_df = season_df[type_string]
    type_df = type_df.reset_index(drop = True)
    season_df = season_df.drop(type_string, axis = 1)
    season_with_fields_df = pd.DataFrame()
    for i in range (0, len(season_ids)):
        #obtains the data for the type and puts it into a df, similar to parse_json
        sub_season_data = type_df[i]
        fields_df = pd.DataFrame(sub_season_data)
        
        #creates a df with the ids/season names
        id_df = pd.DataFrame(season_df.iloc[[i]])
        #print(id_df)
        id_df = create_df_to_add_columns(id_df, len(fields_df['id']))
        
        #combines the df with the season names to the type df
        fields_df = id_df.join(fields_df)
        
        #adds it to our bigger df
        season_with_fields_df = season_with_fields_df.append(fields_df)
    #resets the index
    season_with_fields_df = season_with_fields_df.reset_index(drop = True)
    return season_with_fields_df

# -- THESE GET THE DATA AS A DATAFRAME --

# -- these are examples of how you can modify the data in order to make it more readable. --

#the example here is for a lap data chart
def get_subsession_results(driver, subsession_id):       
    url = SUBSESSION_RESULTS_URL + subsession_id
    file_name = RAW_RESULTS + subsession_id + SUBSESSION_RESULTS
    
    #you can change these fields, I felt these were the most relevant. 
    kept_fields = ['subsessionid', 'season_name', 'eventstrengthoffield', 'weather_temp_value']
    
    #obtain the json from the url so we only get this once
    json_data = get_json_from_url(driver, url)
    #obtain the headers we want to keep with rows
    header_df = create_df_from_json_fields(json_data, kept_fields)
    #creates the df from the partial json that gets you the subsession results. 
    subsession_df = create_df_from_json_data(parse_json(json_data, 'rows'))
    wanted_columns = {SIMSESNAME, CCNAME, OLDIRATING, NEWIRATING, CARNUM, CARID, LAPSCOMPLETE, LAPSLEAD, FINISHPOSINCLASS}
    subsession_df = keep_wanted_columns(subsession_df, wanted_columns)
    #obtains only the race data
    subsession_df = subsession_df.loc[subsession_df[SIMSESNAME] == "RACE"]
    
    #drop the duplicates and race since we don't need the data anymore
    subsession_df = subsession_df.drop(SIMSESNAME, axis = 1)
    subsession_df = subsession_df.drop_duplicates(subset = CARNUM)
    #resets the index of the df
    subsession_df = subsession_df.reset_index(drop = True)
    header_df = create_df_to_add_columns(header_df, len(subsession_df.index))
    #merge the two dfs together
    header_df = header_df.join(subsession_df)
    return header_df

def get_series_race_results(driver, seriesid, raceweek):
    url = SERIES_RACE_RESULTS_URL + seriesid + AND + RACE_WEEK + raceweek
    #file_name = RAW_RESULTS + seriesid
    #obtain the json from the url so we only request it once
    json_data = get_json_from_url(driver, url)
    df_columns = get_headers_from_json(json_data, 'm')
    if(df_columns != []):
        df = create_df_from_json_data(parse_json(json_data, 'd'))
        df.columns = df_columns
    else:
        df = pd.DataFrame(index = [], columns = [])
    return df

#this combines the lap data so it's usable
def get_lap_chart(driver, subsession_id):
    url = LAP_CHART_URL + subsession_id + AND + CAR_CLASS_ID + SIM_SES_NUM
    json_data = get_json_from_url(driver, url)
    
    wanted_columns = {GROUP_ID, DISPLAY_NAME, START_POS, FINISH_POS, POINTS, CARNUM, NUM_INCIDENTS}

    startgrid_df = create_df_from_json_data(parse_json(json_data, 'startgrid'))
    #keeps the columns from wanted_columns, since there's so much useless data here
    startgrid_df = keep_wanted_columns(startgrid_df, wanted_columns)
    lapdata_df = create_df_from_json_data(parse_json(json_data, 'lapdata'))
    
    if(lapdata_df.empty == False):
        combined_df = pd.merge(startgrid_df, lapdata_df, how = 'inner', on = CARNUM)
        combined_df["lap_time"] = combined_df.groupby("displayName").sesTime.diff().fillna(0)
        return combined_df
    return pd.DataFrame(index = [], columns = [])
#combines the subsession and lap data to provide a neatly packaged lap table
def get_combined_subsession_and_lap_data(driver, subsession_id):
    lap_chart_df = get_lap_chart(driver, subsession_id)
    if(lap_chart_df.empty == True):
        return pd.DataFrame(index = [], columns = [])
    subsession_results_df = get_subsession_results(driver, subsession_id)
    combined_df = pd.merge(subsession_results_df, lap_chart_df, how = 'inner', on = CARNUM)
    combined_df.drop(FINISH_POS, axis=1)
    return combined_df

def get_flags(flags):
    lap_flags = []
    if(flags & 2):
        lap_flags.push("pitted")
    if(flags & 4):
        lap_flags.push("off track")
    if(flags & 8):
        lap_flags.push("black flag")
    if(flags & 16):
        lap_flags.push("car reset")
    if(flags & 32):
        lap_flags.push("contact")
    if(flags & 64):
        lap_flags.push("car contact")
    if(flags & 128):
        lap_flags.push("lost control")
    if(flags & 256):
        lap_flags.push("discontinuity")
    if(flags & 512):
        lap_flags.push("interpolated crossing")
    if(flags & 1024):
        lap_flags.push("clock smash")
    if(flags & 2048):
        lap_flags.push("tow")
    if(flags & 8192):
        lap_flags.push("first_lap")
    if(flags & 16384):
        lap_flags.push("last_lap")
    return (", ").join(lap_flags)

def process_lap_chart_data(lap_chart_df):
    #assuming we have lap_chart_df as an input
    processed_lap_df = lap_chart_df
    display_name = ""    
    lap_chart_df['laptime'] = lap_chart_df['sesTime']    
    for i in range(0, len(lap_chart_df['lapnum'])-1):
        if lap_chart_df.iloc[i]['lapnum'] != 0:
            num = lap_chart_df.iloc[i+1]['laptime'] - lap_chart_df.iloc[i]['laptime']
            if num > 0:
                lap_chart_df.at[i,'laptime'] = num
            else:
                lap_chart_df.at[i,'laptime'] = 0
        else:
            lap_chart_df.at[i,'laptime'] = 0
    file_name = MANIPULATED_RESULTS + "test"
    save_df_to_csv(lap_chart_df, file_name)

def remove_ascii_characters_from_df(df, column):
    strings_to_replace = []
    strings_replaced = []
    for x in df[column]:
        if(x.find("%") >= 0):
            strings_to_replace += [x]
            while x.find("%") >= 0:
                ascii_loc = int(x.find("%"))
                ascii_substring = x[ascii_loc:ascii_loc+3]
                ascii_hex = int(x[ascii_loc+1:ascii_loc+3], 16)
                x = x.replace(ascii_substring, chr(ascii_hex))
                print(x)
            strings_replaced += [x]
    #should replace them
    for replace_index in range(0, len(strings_to_replace)):
        df[column] = df[column].str.replace(strings_to_replace[replace_index], strings_replaced[replace_index])
    return df

def cleanup_df(df, is_season):
    df_name = "name"
    df_id = "id"
    if is_season == 1:
        df_name = "seriesname"
        df_id = "seasonid"
    df[df_name] = df[df_name].str.replace("+", " ")
    if is_season == 1:
        df_name = "lowerseasonshortname"
        df[df_name] = df[df_name].str.replace("+", " ")
    df = df.sort_values(by = df_id)
    df = df.drop_duplicates(subset = df_id)
    df = df.reset_index(drop = True)
    return df

def get_cars_df(driver):
    season_df = get_df_from_season(driver, 1, 1)
    cars_df = loop_through_season_df(season_df, "cars")
    columns = ['id','name']
    #replaces the + with spaces for readability, removes duplicates and sorts the value by id
    cars_df = cars_df[columns]
    cars_df = cleanup_df(cars_df, 0)
    #for some reason, iracing includes these dumb %s... gotta delete them
    cars_df = remove_ascii_characters_from_df(cars_df, 'name')
    return cars_df

def get_series_df(driver):
    series_df = get_df_from_season(driver, 1, 2)
    #replaces the + with spaces for readability, removes duplicates and sorts the value by id
    #columns = ['seasonid','seriesname']
    #season_df = season_df[columns]
    series_df = cleanup_df(series_df, 1)
    return series_df

def get_all_series_df(driver):
    series_df = get_df_from_season(driver, 0, 2)
    #replaces the + with spaces for readability, removes duplicates and sorts the value by id
    #columns = ['seasonid','seriesname']
    #season_df = season_df[columns]
    series_df = cleanup_df(series_df, 1)
    return series_df

def get_track_df(driver):
    track_df = get_all_tracks_per_current_season(driver)
    columns = ['name', 'id']
    track_df['name'] = track_df['name'] +"|" +  track_df['config']
    track_df = track_df[columns]
    track_df = cleanup_df(track_df, 0)
    return track_df

def get_all_tracks_per_current_season(driver):
    season_df = get_df_from_season(driver, 1, 3)
    track_df = loop_through_season_df(season_df, "tracks")
    return track_df

def get_all_tracks_per_non_current_season(driver):
    season_df = get_df_from_season(driver, 0, 3)
    track_df = loop_through_season_df(season_df, "tracks")
    return track_df

def get_track_per_season(driver, seasonid):
    season_df = get_df_from_season(driver, 1, 3)
    season_df = season_df[season_df["seasonid"] == seasonid]
    track_df = loop_through_season_df(season_df, "tracks")
    return track_df
    
#updates cars and adds them to a new file
def update_cars_csv(driver, file_name):
    save_df_to_csv(get_cars_df(driver), file_name)
   
#updates the current seasons. 
def update_season_csv(driver, file_name):
    save_df_to_csv(get_series_df(driver), file_name)
    
#updates the current tracks. 
def update_tracks_csv(driver, file_name):
    save_df_to_csv(get_track_df(driver), file_name)

# -- SAVER HELPER METHODS --     

#these methods save the df, basically create csvs from the get methods, saves you from writing your own.

def save_subsession_results(driver, subsession_id):       
    url = SUBSESSION_RESULTS_URL + subsession_id
    file_name = RAW_RESULTS + subsession_id + SUBSESSION_RESULTS
    save_df_to_csv(get_subsession_results(driver, subsession_id), file_name)

def save_series_race_results(driver, series_number, raceweek):
    url = SERIES_RACE_RESULTS_URL + series_number + AND + RACE_WEEK + raceweek
    file_name = RAW_RESULTS + series_number + RACE_RESULTS + WEEK + raceweek
    save_df_to_csv(get_series_race_results(driver, series_number, raceweek),file_name)

#only gets race data, can't seem to grab qualy data from this(?)
def save_lap_chart(driver, subsession_id):
    url = LAP_CHART_URL + subsession_id + AND + CAR_CLASS_ID + SIM_SES_NUM
    file_name = RAW_RESULTS + subsession_id + LAP_DATA + CSV
    save_df_to_csv(get_lap_chart(driver, subsession_id),file_name)

#I only added user input to manipulate and play around with the commands, feel free to use this and swap your own methods if you want
def testing_user_input(driver, file_name):
    user_input = ""
    while user_input != "q":
        user_input = input(COMMANDS)
        try:
            input_data = user_input.split(" ")
            if input_data[0] == 's':
                save_subsession_results(driver, input_data[1])
            elif input_data[0] == 'r':
                save_series_race_results(driver, input_data[1], input_data[2])
            elif input_data[0] == 'l':
                save_lap_chart(driver, input_data[1])
            elif input_data[0] == 'e':
                update_active()
            else:
                print("Incorrect input... please try again...")
        except IndexError:
            print("Incorrect input... please try again...")

#updates the current season for cars/tracks/etc
def update_active():
    dir_name = RAW_RESULTS + CURRENT_SEASON
    print(dir_name)
    try:
        os.mkdir(dir_name)
    except:
        print("Directory exists.")
    cars_file_name = RAW_RESULTS + CURRENT_SEASON + "\\cars"
    season_file_name = RAW_RESULTS + CURRENT_SEASON + "\\season"
    tracks_file_name = RAW_RESULTS + CURRENT_SEASON + "\\tracks"
    update_cars_csv(driver, file_name)
    update_season_csv(driver, file_name)
    update_tracks_csv(driver, file_name)

#example data, if you modified too much or want to see the data again
def get_fresh_raw_data(driver, file_name):
    subsession_id = "37617183"
    race_id = "3059"
    race_week = "11"
    save_subsession_results(driver, subsession_id)
    save_series_race_results(driver, race_id, race_week)
    save_lap_chart(driver, subsession_id)

#Need to use this for a new season. season = name of current season we're trying to get constants for
#def refresh_constants(driver, season):

def main():
    #testing_user_input(driver, file_name)
    #file_name = MANIPULATED_RESULTS + "31717531" + LAP_DATA
    #save_df_to_csv(combine_subsession_and_lap_data(driver, "31717531"), file_name)
    
    #print(chr(233))
    driver = initialize_driver()
    login(driver)
    update_active()
    get_fresh_raw_data(driver, file_name)
    driver.quit()
    #lc_df_loc = MANIPULATED_RESULTS + "31717531" + LAP_DATA + CSV
    #lc_df = pd.read_csv(lc_df_loc, index_col=[0])
    #process_lap_chart_data(lc_df)

#main()