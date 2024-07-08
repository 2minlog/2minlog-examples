#############################################################################################
### Python code to circular plot of temperature over past day.
### For the use case, see https://doc.2minlog.com/tutorials/wifi-arduino-thermometer/
###

# It uses nonstandard font Poppins. The font is installed in 2minlog.
# How to manually install font on Widows 10:
#     1. Go to https://fonts.google.com, search for Poppins
#     2. Select the font, click on Get font, Click Download all.
#     3. Unzip the font to a folder
#     4. Go to the folder; select all .ttf font files, right-click on the font, "Install for all users"
#
# How to manually install font on Linux:
#     1. yum -y install wget fontconfig zip unzip
#     2. wget https://fonts.google.com/download?family=Poppins -O poppins.zip
#     3. unzip poppins.zip -d /usr/share/fonts/poppins
#     4. fc-cache -fv
#
# Refresh cache dir
#     1. Understand where is the cache: print(matplotlib.get_cachedir())
#     2. Delete the folder

# Ignored if you run in 2minlog system:
DATASET_NAMES = ['Arduino thermometer'] # .csv
OUTPUT_TYPE = 'jpg'

bg_color = "black"
fg_color = "white"

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import math
import pandas as pd
import base64

def covert_to_numeric(df):
    for column in df.columns:
        # Make a copy of the original column data
        original_data = df[column].copy()
        # Attempt to convert the column to numeric types, coerce errors to NaN
        converted_data = pd.to_numeric(df[column], errors='coerce')
        # If the conversion introduces NaNs where there weren't any, revert to original data
        if converted_data.isna().sum() > original_data.isna().sum():
            df.loc[:, column] = original_data
        else:
            df.loc[:, column] = converted_data
    return df

def plotimg(df):
    plt.rcParams.update({
        'font.family': 'Poppins'
    })

    df = covert_to_numeric(df)

    df.index = df.index.tz_localize('UTC').tz_convert('Europe/Paris')

    # Can be handy for debugging
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    # Filter to the last 24 hours
    last_date = df.index.max()  # Get the last date from the index
    df = df[last_date - pd.Timedelta(days=1):last_date + pd.Timedelta(days=1)].copy() # Upper limit is not inclusive

    df['radians'] = (df.index.hour / 24 + df.index.minute / 24 / 60 + df.index.second / 24 / 3600 ) * 2 * np.pi

    # Create a polar plot
    fig = plt.figure(figsize=(8, 8), dpi=100)
    fig.patch.set_facecolor(bg_color)

    ax = plt.subplot(111, polar=True)
    ax.set_facecolor(bg_color)
    ax.xaxis.grid(True, color=fg_color, linestyle='-', linewidth=2)
    ax.yaxis.grid(True, color=fg_color, linestyle='-', linewidth=2)
    ax.tick_params(colors=fg_color)
    ax.spines['polar'].set_edgecolor(fg_color)

    # Create custom colormap
    colors = ['violet', 'indigo', 'blue', 'green', 'yellow', 'orange', 'red']
    n_bins = len(df)  # Number of bins
    cmap = LinearSegmentedColormap.from_list("Custom", colors, N=n_bins)

    # Convert index to seconds since minimum timestamp
    df['seconds'] = (df.index - df.index.min()).total_seconds()

    # Assign colors based on seconds
    norm = plt.Normalize(df['seconds'].min(), df['seconds'].max())
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    df['color'] = df['seconds'].apply(lambda x: sm.to_rgba(x))

    # Plot the data with colors
    for i in range(len(df) - 1):
        ax.plot(df['radians'].iloc[i:i + 2], df['temperature'].iloc[i:i + 2],
                color=df['color'].iloc[i], linewidth=3)

    # Set the direction of the zero angle
    ax.set_theta_zero_location('N')  # 'N' for North

    # Set the rotation of the plot (clockwise/counter-clockwise)
    ax.set_theta_direction(-1)  # Clockwise

    # Set labels for the angles
    ax.set_xticks(np.linspace(0, 2 * np.pi, 24, endpoint=False))
    ax.set_xticklabels(range(24))

    # Set number of radial grid lines
    max_temperature = np.ceil(df['temperature'].max())
    min_temperature = np.floor(df['temperature'].min())

    def find_base(value_range):
        if value_range > 80:
            return 20
        if value_range > 40:
            return 10
        elif value_range > 20:
            return 5
        elif value_range > 8:
            return 2
        else:
            return 1

    base = find_base(max_temperature - min_temperature)
    min_temperature = base * math.floor(min_temperature / base)
    max_temperature = base * math.ceil(max_temperature / base)

    origin_value = min_temperature - (max_temperature - min_temperature)

    # Set radial grids
    radial_ticks = np.arange(min_temperature, max_temperature + base, base)
    ax.set_yticks(radial_ticks)
    ax.set_rlabel_position(0)  # 0 degrees is north

    ax.set_ylim(origin_value, max_temperature)

    # Add a circle at the center
    circle_radius = max_temperature - min_temperature
    circle = plt.Circle((0, 0), circle_radius,
                        transform=ax.transData._b, facecolor=bg_color,
                        edgecolor=fg_color, linewidth=2,
                        zorder=10)
    ax.add_artist(circle)

    # Add the latest temperature inside the white circle
    latest_temperature = df.iloc[-1]['temperature']
    latest_color = df.iloc[-1]['color']
    print(f'{latest_temperature=}')

    ax.text(0, origin_value, f'{latest_temperature:.1f}°C',
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=42,
            color=latest_color,
            zorder=11)

    # Add second set of radial labels to the south manually
    for r in radial_ticks:
        ax.text(np.pi, r, f'{r:.0f}', ha='left', va='bottom', color=fg_color)

    plt.savefig('/tmp/img' + OUTPUT_TYPE, format=OUTPUT_TYPE)
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
    df = dfs[0]
    ff = plotimg(df)
    response = returnimg(ff)

    return response


#################################################################
### Code to run locally, mimicking the cloud environment
OUTPUT_TYPE = 'jpg'

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
