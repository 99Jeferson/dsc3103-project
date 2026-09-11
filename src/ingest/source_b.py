from datetime import timezone

import requests
import pandas as pd 
 from src.common.config import RAINFALL_START_DATE, RAINFALL_END_DATE, RAINFALL_URL     
def get_mkt_rainfall(mkt_name, latitude, longitude, start_date=RAINFALL_START_DATE, end_date=RAINFALL_END_DATE, "timezone"="auto", "daily"="precipitation_sum"):
 response = requests.get(RAINFALL_URL, params={"latitude": latitude, "longitude": longitude, "start_date": start_date, "end_date": end_date, "timezone": timezone, "daily": daily})
 if response.status_code != 200:
         raise RuntimeError(f"Failed to fetch rainfall data for {mkt_name}. Status code: {response.status_code}")
 daily = response.json()[daily]
 return pd.DataFrame({
    "date": daily["time"], 
    "rainfall": daily["precipitation_sum"]
    })
