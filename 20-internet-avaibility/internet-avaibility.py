#############################################################################################
### Internet Availability - Script to run in 2minlog.com system.
###
### This script visualizes the availability of your internet. It consists of two parts:
### 1. interval_ping.py - you need to run this script on a suitable computer in your network,
###     e.g., on your server, router, NAS, RPi, or anything that runs reliably 24/7. It
###     sends data every minute to 2minlog.com sever.
### 2. This script, internet-avaibility.py, to vistualize internet avaibility over the past five weeks.
###     It draws five columns, from bottom to top - 168 hours per week, and left to right minutes per hour.
###     When the internet is available, it shows a green pixel, while if the internet is not available,
###     the respective pixel is red. You need to upload the script to 2minlog.com portal
###
### To visualize the image on the full screen and autorefresh, you may use the ImgTuner.com service. See
### https://doc.2minlog.com/tutorials/full-screen-autorefresh for details.
###
### In the portal, you need to set the Dataset and Graph. Also, do not forget to set maximum number of data
### points to 5 weeks * 168 hours * 60 = 50,400 in the Dataset and corresponding figures in Graph (i.e., 35
### days back).
###

DATASET_NAMES = ['intervalping']  # .csv
OUTPUT_TYPE = 'png'

import pandas as pd
import base64
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import matplotlib.colors as mcolors


def covert_to_numeric(df, drop_nonnumeric):
    columns_to_drop = []
    for column in df.columns:
        original_data = df[column].copy()
        original_data = original_data.str.strip()
        mask_empty = original_data == ''
        converted_data = pd.to_numeric(original_data, errors='coerce')
        converted_data_masked = converted_data.copy()
        converted_data_masked[mask_empty] = 0  # Convert empty strings as NaN

        if converted_data_masked.isna().sum() > 0:
            df.loc[:, column] = original_data
            columns_to_drop.append(column)
        else:
            df.loc[:, column] = converted_data

    if drop_nonnumeric:
        df.drop(columns=columns_to_drop, inplace=True)

    return df


def plotimg(df):
    df = covert_to_numeric(df, drop_nonnumeric=True)

    # Ensure the DataFrame has a 'timestamp' column; else assume it's an index
    if 'timestamp' not in df.columns and df.index.name == 'timestamp':
        df = df.reset_index()

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC')
    df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Berlin')

    now = pd.Timestamp.now(tz='Europe/Berlin')

    df['timestamp'] = df['timestamp'].dt.floor('min')

    # Calculate the number of days until the next Sunday (end of the week)
    days_until_sunday = 7 - now.weekday()  # Sunday is day 6

    # Compute the next Sunday at midnight (00:00:00)
    end_time = (now + timedelta(days=days_until_sunday)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(days=35)
    end_time = end_time - timedelta(minutes=1)

    # Find the oldest and most recent timestamps in the data
    most_recent_time = df['timestamp'].max()
    cutoff_date = most_recent_time - pd.Timedelta(days=5 * 7)
    df = df[df['timestamp'] >= cutoff_date]

    oldest_time = df['timestamp'].min()

    # Create 'record' column for actual data
    df['record'] = 1  # Mark actual data with 1

    # Generate all timestamps in the desired range (past 35 days)
    all_timestamps = pd.date_range(start=start_time, end=end_time, freq='min')

    # Create a DataFrame for all timestamps and merge with the provided data
    df_full = pd.DataFrame(all_timestamps, columns=['timestamp'])

    df = pd.merge(df_full, df, on='timestamp', how='left')

    df.loc[df['timestamp'] < oldest_time, 'record'] = -1  # too old
    df.loc[df['timestamp'] > most_recent_time, 'record'] = -1  # too youg
    df.loc[df['timestamp'] > now, 'record'] = -2  # future
    df.loc[df['record'].isna(), 'record'] = 0  # missing data

    # Prepare the data for visualization
    df['date'] = df['timestamp'].dt.date
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['minute_of_hour'] = df['timestamp'].dt.minute

    # df.to_csv('tmp.csv')

    # Split data into 5 weeks (7 days each)
    last_35_days = sorted(df['date'].unique())[-35:]

    weeks = [last_35_days[i - 7:i] for i in range(35, 0, -7)]  # 5 * 7 = 35

    # Prepare matrices for each week
    records_matrices = []
    for week in weeks:
        records_matrix = np.zeros((7 * 24, 60))  # 7 days * 24 hours, 60 minutes per hour
        for day_idx, day in enumerate(reversed(week)):  # Start from the most recent day
            day_data = df[df['date'] == day]
            for _, row in day_data.iterrows():
                hour_idx = row['hour_of_day']
                minute_idx = row['minute_of_hour']
                records_matrix[day_idx * 24 + 23 - hour_idx, minute_idx] = row['record']
                # records_matrix[day_idx * 24 + 23 - hour_idx, minute_idx] = row['timestamp'].timestamp() # row['record']
        records_matrices.append(records_matrix)

    # Plotting
    # fig, axs = plt.subplots(1, 5, figsize=(10.24, 6), dpi=300, gridspec_kw={'wspace': 0.5, 'hspace': 0.3})
    fig, axs = plt.subplots(1, 5, figsize=(10.24, 6 / 655 * 600 - 0.05), dpi=200 / 1738 * 1024,
                            gridspec_kw={'wspace': 0.5, 'hspace': 0.3})
    # fig, axs = plt.subplots(1, 5, figsize=(30, 12), gridspec_kw={'wspace': 0.3})  # 5 blocks with more space between them

    fig.patch.set_facecolor('black')
    cmap = mcolors.ListedColormap(['black', 'gray', 'red',
                                   'green', ])  # Gray for padding, red for missing, green for actual data # Frankly no idea, why swapped green & red.
    bounds = [-2.5, -1.5, -0.5, 0.5, 1.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    # Plot each week in a separate block
    for i, ax in enumerate(axs):
        ax.imshow(records_matrices[i], cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')
        ax.set_facecolor('black')
        ax.tick_params(colors='white', labelsize=6)
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['right'].set_color('white')

        ax.set_xticks(np.arange(0, 60, 5))
        ax.set_xticklabels([f"{i}" for i in range(0, 60, 5)], color='white', fontsize=6)

        day_ticks = np.arange(0, 7 * 24, 24)
        hour_ticks = np.array([0 - 1, 6 - 1, 12 - 1, 18 - 1])
        all_ticks = np.sort(np.concatenate([day_ticks + h for h in hour_ticks]))
        ax.set_yticks(all_ticks)

        y_labels = []
        for day_idx in range(7):
            y_labels.extend([f'{hour}:00' for hour in [24, 18, 12, 6]])

        ax.set_yticklabels(y_labels, color='white', fontsize=6)

        for day_idx, day in enumerate(reversed(weeks[i])):
            ax.text(-18, day_idx * 24 + 12, day.strftime('%Y-%m-%d'), rotation=90,
                    verticalalignment='center', horizontalalignment='right', fontsize=6, color='white')

        week_start = weeks[i][0].strftime('%Y-%m-%d')
        week_end = weeks[i][-1].strftime('%Y-%m-%d')
        ax.set_title(f'{week_start} - {week_end}', color='white', pad=8, fontsize=8)
        ax.set_xlabel('Minute of the Hour', color='white', fontsize=6)

    plt.suptitle('Internet access Vojenova (past 5 weeks)', color='white', y=0.95, fontsize=10)
    plt.savefig('/tmp/img.' + OUTPUT_TYPE, format=OUTPUT_TYPE, bbox_inches='tight', facecolor='black')
    plt.close()

    return "/tmp/img." + OUTPUT_TYPE


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
    else:  # If dfs = [] let's set some dummy graph
        df = pd.DataFrame({'timestamp': [0, 1], 'value': [1, 2]}).set_index('timestamp')

    ff = plotimg(df)

    response = returnimg(ff)

    return response


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
    else:  # If dfs = [] let's set some dummy graph
        df = pd.DataFrame({'timestamp': [0, 1], 'value': [1, 2]}).set_index('timestamp')

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
        with open(DSN + '.csv', 'r') as f:
            data = f.readlines()
            data = [line.strip().split(',') for line in data]
            csvs.append(data)

    dfs = []
    for csv in csvs:
        if csv == [[]]:
            continue

        df = pd.DataFrame(data=csv[1:], columns=csv[0])
        df.columns = df.columns.str.strip()  # Strip white spaces around elements
        df.set_index('timestamp', inplace=True)
        df.index = pd.to_datetime(df.index, format='ISO8601')
        dfs.append(df)

    result = handler(dfs)

    if OUTPUT_TYPE == 'png' or OUTPUT_TYPE == 'jpg':
        img_data = base64.b64decode(result['body'])

        with open('output.' + OUTPUT_TYPE, 'wb') as file:
            file.write(img_data)
    else:
        print(80 * '*')
        print(result['body'])
        print(80 * '*')
### End of code to run locally, mimicking the cloud environment
#################################################################
