import fastf1 as ff1
import pandas as pd

ff1.Cache.enable_cache("ff1")

#add mapping for f1 races to numbers
#should we limit it to hamilton + bottas?

iracing_track_df = pd.read_csv("ff1_data/gp_to_iracing_mapping.csv", index_col = 0)

#obtains the data for f1 tracks
for t in iracing_track_df.iloc:
    session = ff1.get_session(t.year, t.gp, "R")
    lap_data = session.load_laps()
    csv_path = "ff1_data/f1_data/" + t.gp + "_gp_" + str(t.year) + ".csv"
    lap_data.to_csv(csv_path)
