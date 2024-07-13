#############################################################################################
### A simple bolilerplate code for 2minlog service.
### https://raw.githubusercontent.com/2minlog/2minlog-examples/main/00-default_code/00_hello_world.py
###
### - Works if deployed in 2minlog environment, and also in your local environment.
### - You need to install the libraries if you want to run it locally on your computer: pip3 install pandas matplotlib
### - It shows a dummy graph if called with no parameters
### - Else it plots the dataset
###

DATASET_NAMES = ['example_dataset'] # .csv
OUTPUT_TYPE = 'jpg'

import pandas as pd
import base64
import matplotlib.pyplot as plt

def covert_to_numeric(df):
    for column in df.columns:
        original_data = df[column].copy()
        original_data = original_data.str.strip()
        mask_empty = original_data == '' # Convert empty strings as NaN
        converted_data = pd.to_numeric(original_data, errors='coerce')
        converted_data_masked = converted_data.copy()
        converted_data_masked[mask_empty] = 0

        if converted_data_masked.isna().sum() > 0:
            df.loc[:, column] = original_data
        else:
            df.loc[:, column] = converted_data
    return df

def plotimg(df):
    df = covert_to_numeric(df)

    print(df.head()) # It won't show anything in the cloud, but it does when ran locally.

    plt.figure(figsize=(6.4, 4.8), dpi=100) # 640 x 480 pixels
    plt.plot(df)

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
    if len(dfs) > 0:
        df = dfs[0]
    else: # If dfs = [] let's set some dummy graph
        df = pd.DataFrame({'timestamp': [0,1], 'value': [1,2]}).set_index('timestamp')

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
