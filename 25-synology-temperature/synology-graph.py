#################################################################################################
### This is a system to gather disc temperature of you Synology NAS via SNMP protocol
### and plot the temperature history in 2minlog.com system.
### It consists of two Python scripts - one to gather the temperature measurements
### and one to plot the tempearture in a nice graph.
###
### This script works if deployed in 2minlog environment, and also in your local environment.


DATASET_NAMES = ['Synology temp - do not delete'] # .csv
OUTPUT_TYPE = 'png'

import pandas as pd
import base64
import matplotlib.pyplot as plt

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from datetime import datetime, timedelta
import pytz
import numpy as np
import matplotlib.collections as mcoll
from matplotlib.colors import LinearSegmentedColormap

# Function to plot colored lines based on temperature
def colorline(x, y, z=None, cmap='Greens', norm=None, linewidth=2, ax=None):
    if ax is None:
        ax = plt.gca()
    if z is None:
        z = y
    z = np.asarray(z)

    # Normalize the temperature values between 0 and 1 for the custom colormap
    norm = plt.Normalize(15, 50)  # Adjusting this to cover temperatures from 15°C to 50°C

    segments = [np.array([[x[i], y[i]], [x[i + 1], y[i + 1]]]) for i in range(len(x) - 1)]
    lc = mcoll.LineCollection(segments, array=z[:-1], cmap=cmap, norm=norm, linewidth=linewidth)
    ax.add_collection(lc)
    ax.autoscale()
    return lc


def plotimg(df):
    data = df
    df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')

    print(df.head())  # It won't show anything in the cloud, but it does when ran locally.

    # Parse the 'datetime' column and convert to Europe/Berlin time zone
    data['datetime'] = pd.to_datetime(data.index)
    data['datetime'] = data['datetime'].dt.tz_localize('UTC').dt.tz_convert('Europe/Berlin')

    # Filter data for the last week
    now = pd.Timestamp.now(tz='Europe/Berlin')
    one_week_ago = now - pd.Timedelta(days=7)
    data = data[data['datetime'] >= one_week_ago]

    # Group the data by 'server_name' and 'name'
    groups = data.groupby(['server_name', 'name'])

    # Set up the figure dimensions and properties
    dpi = 100
    fig_width = 10.24  # 1024 pixels / 100 dpi
    fig_height = 6.00  # 600 pixels / 100 dpi
    fig, axes = plt.subplots(nrows=len(groups), ncols=1, figsize=(fig_width, fig_height), dpi=dpi)
    fig.patch.set_facecolor('black')
    fig.subplots_adjust(hspace=0.5)

    # Ensure axes is iterable
    if len(groups) == 1:
        axes = [axes]

    # Define the temperature range for all graphs
    temp_min = data['temperature'].min()
    temp_max = data['temperature'].max()
    temp_range = (min(temp_min, 20), max(temp_max, 45))  # Include 20 and 45 for the reference lines

    # Create a custom colormap that transitions from dark blue, light blue, green, light red, to dark red
    colors = [(0, 'darkblue'), (0.25, 'lightblue'), (0.5, 'green'), (0.75, 'lightcoral'), (1, 'darkred')]
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)

    # Plot each group
    for ax, ((server_name, disk_name), group) in zip(axes, groups):
        group = group.sort_values('datetime').reset_index(drop=True)  # Reset index to fix KeyError

        # Prepare data for plotting
        x = mdates.date2num(group['datetime'])
        y = group['temperature']
        z = y  # Color based on temperature

        # Plot the temperature line with varying color using the custom colormap
        colorline(x, y, z=z, cmap=cmap, ax=ax)

        # Set graph properties
        ax.set_title(f"{server_name} / {disk_name}", color='white')
        ax.set_facecolor('black')
        ax.tick_params(axis='both', colors='white')
        ax.set_ylim(temp_range)

        # Add reference lines at 20°C and 45°C
        ax.axhline(y=20, color='grey', linewidth=2)
        ax.axhline(y=45, color='grey', linewidth=2)

        # Format x-axis with tick marks at midnight of every day
        ax.xaxis.set_major_locator(mdates.DayLocator(tz=pytz.timezone('Europe/Berlin')))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d', tz=pytz.timezone('Europe/Berlin')))
        ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5, color='gray')

        # Set tick labels color
        for label in ax.get_xticklabels(which='both'):
            label.set_color('white')
        for label in ax.get_yticklabels():
            label.set_color('white')

        # Get font properties from the x-tick labels (date labels)
        xtick_labels = ax.get_xticklabels()
        if xtick_labels:
            font_properties = xtick_labels[0].get_fontproperties()

            # Add the latest temperature value as a label with the same font properties
            latest_temp = y.iloc[-1]
            latest_time = x[-1]
            ax.text(latest_time, latest_temp, f'{latest_temp:.0f}°C', color='white',
                    fontproperties=font_properties, ha='left', va='center')

    # Adjust layout and save the figure
    plt.tight_layout()

    plt.savefig('/tmp/img' + OUTPUT_TYPE, format=OUTPUT_TYPE, facecolor=fig.get_facecolor(), dpi=dpi)
    plt.close()

    return "/tmp/img" + OUTPUT_TYPE


def returnimg(ff):
    with open(ff, 'rb') as image_file:
        img = image_file.read()

    body = base64.b64encode(img).decode('utf-8')

    response = {
        'headers': {"Content-Type": "image/" + OUTPUT_TYPE},
        'statusCode': 200,
        'body': body,
        'isBase64Encoded': True
    }
    return response

def handler(dfs):
    if len(dfs) > 0:
        df = dfs[0]
    else: # If dfs = [] let's set some dummy graph
        df = pd.DataFrame({'timestamp': [0,1], 'value': [1,2]}).set_index('timestamp')

    ff = plotimg(df)

    response = returnimg(ff)

    return response


#################################################################
### Code to run locally, mimicking the cloud environment
if 'TWO_MINLOG_EXECUTION_ENV' not in globals():
    import os
    import tempfile
    import pandas as pd
    import base64

    os.makedirs("/tmp", exist_ok=True)
    globals()['MPLCONFIGDIR'] = tempfile.mkdtemp(dir='/tmp')

    csvs = []
    for DSN in DATASET_NAMES:
        with open( DSN + '.csv', 'r') as f:
            data = f.readlines()
            data = [line.strip().split(',') for line in data]
            csvs.append(data)

    dfs = []
    for csv in csvs:
        if csv == [[]]:
            continue

        df = pd.DataFrame(data=csv[1:], columns=csv[0])
        df.columns = df.columns.str.strip() # Strip white spaces around elements
        df.set_index('timestamp', inplace=True)
        df.index = pd.to_datetime(df.index, format='ISO8601')

        dfs.append(df)

    result = handler(dfs)

    if OUTPUT_TYPE == 'png' or OUTPUT_TYPE == 'jpg':
        img_data = base64.b64decode(result['body'])

        with open('output.' + OUTPUT_TYPE, 'wb') as file:
            file.write(img_data)
    else:
        print(80*'*')
        print(result['body'])
        print(80*'*')
### End of code to run locally, mimicking the cloud environment
#################################################################