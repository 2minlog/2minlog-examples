# pip install numpy pandas seaborn Pillow testresources astral

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
import pytz
import base64
from astral.sun import sun
from astral import LocationInfo
import matplotlib.transforms as transforms

def preprocess(df):
    df.index = df.index.tz_localize('UTC')

    cutoff_time = datetime.now(pytz.timezone('Europe/Prague')) - timedelta(days=2)

    df = df[df.index > cutoff_time]

    # Loop through possible sensor value columns

    processed_df = {}
    # BME280_humidity
    # BME280_pressure
    # BME280_temperature
    # HECA_dc
    # HECA_humidity
    # HECA_RHdc
    # HECA_Tdc
    # HECA_temperature
    # max_micro
    # min_micro
    # NAMF - 2020 - 46
    # rc6
    # samples
    # SDS_P1
    # SDS_P2
    # signal

    for sensor_type in ['BME280_temperature', 'BME280_humidity', 'SDS_P2']:
        processed_df[sensor_type] = pd.DataFrame()
        for i in range(14):
            value_col = f'sensordatavalues_{i}_value'
            type_col = f'sensordatavalues_{i}_value_type'

            if type_col in df.columns:
                # Filter rows where the type is 'HECA_temperature'
                mask = df[type_col] == sensor_type
                temp_data = df.loc[mask, [value_col]].copy()
                temp_data.rename(columns={value_col: sensor_type}, inplace=True)

                if not processed_df[sensor_type].empty:
                    processed_df[sensor_type] = pd.concat([processed_df[sensor_type], temp_data], axis=0)
                else:
                    processed_df[sensor_type] = temp_data

        processed_df[sensor_type] = processed_df[sensor_type].sort_index()

    return processed_df


def annotate_line_end(ax, data, unit, color):
    last_index = data.index[-1]
    last_value = data.iloc[-1,0]
    trans = transforms.blended_transform_factory(ax.transAxes, ax.transData)
    ax.text(1.0, last_value, f' {last_value:.1f}{unit}', color=color, va='center', ha='left', transform=trans)


def plotimg(df_dict):
    dft = df_dict['BME280_temperature'].astype(float)
    dfh = df_dict['BME280_humidity'].astype(float)
    dfp = df_dict['SDS_P2'].astype(float)

    prague_tz = pytz.timezone('Europe/Prague')

    fig, host = plt.subplots(figsize=(1920/300, 1080/300), dpi=300, layout='constrained')
    ax2 = host.twinx()
    ax3 = host.twinx()

    host.set_xlabel("Time")
    host.set_ylabel("Temperature")
    ax2.set_ylabel("Humidity")
    ax3.set_ylabel("Particles P2.5")

    color1, color2, color3 = 'red', 'blue', 'green'
    p1 = host.plot(dft.index, dft, color=color1)
    p2 = ax2.plot(dfh.index, dfh, color=color2)
    p3 = ax3.plot(dfp.index, dfp, color=color3, zorder=3)

    annotate_line_end(host, dft, "°C", color1)
    annotate_line_end(ax2, dfh, "%", color2)
    annotate_line_end(ax3, dfp, "μg/m³", color3)

    # Adding black horizontal lines at temperature y-ticks
    for tick in host.get_yticks():
        host.axhline(y=tick, color='black', linewidth=0.8, linestyle='--', alpha=0.5)  # Lighter lines for visibility

    # Setting the color for y-axis
    host.yaxis.label.set_color(color1)
    host.tick_params(axis='y', colors=color1)
    host.spines['left'].set_color(color1)

    ax2.yaxis.label.set_color(color2)
    ax2.tick_params(axis='y', colors=color2)
    ax2.spines['left'].set_color(color2)

    ax3.yaxis.label.set_color(color3)
    ax3.tick_params(axis='y', colors=color3)
    ax3.spines['left'].set_color(color3)

    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_position(('outward', 50))
    ax2.spines['left'].set_visible(True)
    ax2.yaxis.set_label_position('left')
    ax2.yaxis.set_ticks_position('left')

    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_position(('outward', 90))
    ax3.spines['left'].set_visible(True)
    ax3.yaxis.set_label_position('left')
    ax3.yaxis.set_ticks_position('left')

    # Formatting the x-axis
    host.xaxis.set_major_locator(mdates.DayLocator(tz=prague_tz))
    host.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m',tz=prague_tz))
    host.xaxis.set_minor_locator(mdates.HourLocator(byhour=[0, 6, 12, 18],tz=prague_tz))
    host.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M',tz=prague_tz)) # '%H:%M'

    # Adjusting the size of the ticks to be uniform
    host.tick_params(axis='x', which='major', length=8, width=1)
    host.tick_params(axis='x', which='minor', length=2, width=1)

    host.yaxis.label.set_color(p1[0].get_color())
    ax2.yaxis.label.set_color(p2[0].get_color())
    ax3.yaxis.label.set_color(p3[0].get_color())

    city_name = "Prague"
    latitude=50.0755
    longitude=14.4378

    city = LocationInfo(city_name, "Czech Republic", timezone="Europe/Prague", latitude=latitude, longitude=longitude)

    # Extend the date range to cover all possible night spans
    start_date = dft.index.min() - pd.Timedelta(days=1)
    end_date = dft.index.max() + pd.Timedelta(days=1)

    for dt in pd.date_range(start_date, end_date, freq='D'):
        s = sun(city.observer, date=dt, tzinfo=pytz.timezone('Europe/Prague'))
        night_start = s['sunset'].replace(tzinfo=None)
        night_end = s['sunrise'].replace(tzinfo=None) + timedelta(days=1)

        # Ensure that night spans are within the data bounds
        if night_start < dft.index.min().replace(tzinfo=None):
            night_start = dft.index.min().replace(tzinfo=None)
        if night_end > dft.index.max().replace(tzinfo=None):
            night_end = dft.index.max().replace(tzinfo=None)

        if night_start < night_end:  # This check ensures we have a valid range to display
            host.axvspan(night_start, night_end, color='gray', alpha=0.3)

    # Setting up the x-axis to cover the full date range of the data
    host.set_xlim([dft.index.min(), dft.index.max()])

    plt.savefig('/tmp/img.jpg', format='jpg')
    plt.close()

    return "/tmp/img.jpg"

def returnimg(ff):
    with open(ff, 'rb') as image_file:
        img = image_file.read()

    body = base64.b64encode(img).decode('utf-8')

    response = {
        'headers': {"Content-Type": "image/jpg"},
        'statusCode': 200,
        'body': body,
        'isBase64Encoded': True
    }
    return response


def handler(dfs):
    df = dfs[0]
    df = preprocess(df)
    ff = plotimg(df)

    response = returnimg(ff)

    return response
