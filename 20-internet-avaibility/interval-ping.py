#############################################################################################
### Internet Availability - Script to run in 2minlog.com system.
###
### This script visualizes the availability of your internet. It consists of two parts:
### 1. interval_ping.py - you need to run this script on a suitable computer in your network,
###     e.g., on your server, router, NAS, RPi, or anything that runs reliably 24/7. It
###     sends data every minute to 2minlog.com sever.
### 2. internet-avaibility.py script, to vistualize internet avaibility over the past five weeks.
###     It draws five columns, from bottom to top - 168 hours per week, and left to right minutes per hour.
###     When the internet is available, it shows a green pixel, while if the internet is not available,
###     the respective pixel is red. You need to upload the script to 2minlog.com portal.
###
### To visualize the image on the full screen and autorefresh, you may use the ImgTuner.com service. See
### https://doc.2minlog.com/tutorials/full-screen-autorefresh for details.
###
### In the portal, you need to set the Dataset and Graph. Also, do not forget to set maximum number of data
### points to 5 weeks * 168 hours * 60 = 50,400 in the Dataset and corresponding figures in Graph (i.e., 35
### days back).
###

# pip install requests

import requests
import time
from datetime import datetime

## Set here secret from 2minlog.com Dataset.
URL = "https://api.2minlog.com/log?datasetSecret=SEC-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

def ping_url(url):
    while True:
        # Get the current time
        now = datetime.now()

        # Calculate the number of seconds to wait until the next 30-second mark
        if now.second < 30:
            seconds_to_wait = 30 - now.second - now.microsecond / 1_000_000
        else:
            seconds_to_wait = 60 - now.second - now.microsecond / 1_000_000 + 30

        # Wait until the next 30-second mark
        time.sleep(seconds_to_wait)

        try:
            # Send the HTTP GET request
            print(f"Pinging to {url}")
            response = requests.get(url)
            print(f"[{datetime.now()}] Ping to {url} - Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Error pinging {url}: {e}")

ping_url(URL)
