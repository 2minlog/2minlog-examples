#################################################################################################
### This is a system to gather disc temperature of you Synology NAS via SNMP protocol
### and plot the temperature history in 2minlog.com system.
### It consists of two Python scripts - one to gather the temperature measurements
### and one to plot the tempearture in a nice graph.
###
### For further technical information, see: 
### https://www.pysnmp.com/ -> Documentation & help
### SNMP Gurtu GPT https://chat.openai.com/g/g-ZWj5VHbh7-snmp-guru
### https://www.synology.com/support/snmp_mib.php -> https://global.synologydownload.com/download/Document/Software/DeveloperGuide/Firmware/DSM/All/enu/Synology_DiskStation_MIB_Guide.pdf
###

# pip install pysnmp requests

import asyncio
from pysnmp.hlapi.v3arch.asyncio import *

import requests
from requests.auth import HTTPBasicAuth

import time
from datetime import datetime, timedelta

#### Update secrets and IP addresses below:
username = '2minlog'
passwd = '2minlog_passwd'

synology_servers = [
    {'name': 'Synology1', 'ip': 'xx.xx.xx.xx', 'user': 'Synology1_snmp_user', 'password': 'Synology1_snmp_passwd'},
    {'name': 'Synology2', 'ip': 'xx.xx.xx.xx', 'user': 'Synology2_snmp_user', 'password': 'Synology2_snmp_passwd'}
]

synology_servers = confidentials.synology_servers

async def run(server_name, ipaddress, username, passwd, outinfo):
    # SNMP walk for disk name, model, and temperature
    oids = [
        ObjectType(ObjectIdentity('1.3.6.1.4.1.6574.2.1.1.2')),  # Disk name (diskID)
        ObjectType(ObjectIdentity('1.3.6.1.4.1.6574.2.1.1.3')),  # Disk model (diskModel)
        ObjectType(ObjectIdentity('1.3.6.1.4.1.6574.2.1.1.6'))   # Disk temperature (diskTemperature)
    ]

    errorIndication, errorStatus, errorIndex, varBinds = await bulkCmd(
        SnmpEngine(),
        UsmUserData(username, passwd, authProtocol=usmHMACSHAAuthProtocol),  # Use the appropriate auth protocol
        await UdpTransportTarget.create((ipaddress, 161)),
        ContextData(),
        0, 10,  # Increase the max-repetitions to get more results in one request
        *oids  # Query disk name, model, and temperature
    )

    if errorIndication:
        print(f"Error: {errorIndication}")
    elif errorStatus:
        print(f"Error Status: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1] or '?'}")
    else:
        disk_data = {}
        for varBind in varBinds:
            oid, value = varBind
            oid_str = str(oid)

            # Disk name
            if oid_str.startswith('1.3.6.1.4.1.6574.2.1.1.2'):
                index = oid_str.split('.')[-1]
                if index not in disk_data:
                    disk_data[index] = {}
                disk_data[index]['name'] = value

            # Disk model
            elif oid_str.startswith('1.3.6.1.4.1.6574.2.1.1.3'):
                index = oid_str.split('.')[-1]
                if index not in disk_data:
                    disk_data[index] = {}
                disk_data[index]['model'] = value

            # Disk temperature
            elif oid_str.startswith('1.3.6.1.4.1.6574.2.1.1.6'):
                index = oid_str.split('.')[-1]
                if index not in disk_data:
                    disk_data[index] = {}
                disk_data[index]['temperature'] = value

        # Print out the disk information
        for index, info in disk_data.items():
            name = info.get('name', 'Unknown')
            model = info.get('model', 'Unknown')
            temperature = info.get('temperature', 'Unknown')

            name = str(name)
            model = str(model)
            temperature = str(temperature)

            print(f"IP Address {ipaddress}, Disk {index}: Name: {name}, Model: {model}, Temperature: {temperature} °C")
            outinfo.append({'server_name': server_name, 'ip': ipaddress, 'disk': index, 'name': name, 'model': model, 'temperature': temperature})

            

def send_log(url, payload, username, passwd):      
    # Sending the POST request
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(username, passwd))

    # Check the response
    if response.status_code == 200:
        print('Log successfully sent!')
    else:
        print(f'Failed to send log. Status code: {response.status_code}, Response: {response.text}')

def wait_until_next_5_min():
    # Get current time
    now = datetime.now()

    # Calculate next 5-minute mark (round up)
    next_5_min = (now + timedelta(minutes=5 - (now.minute % 5))).replace(second=0, microsecond=0)

    # Calculate how many seconds until the next 5-minute mark
    wait_seconds = (next_5_min - now).total_seconds()

    print(f"Waiting {wait_seconds} seconds until the next full 5-minute mark.")
    
    # Wait until the next 5-minute mark
    time.sleep(wait_seconds)


while True:
    outinfo = []

    for server in synology_servers:
        asyncio.run(run(server['name'], server['ip'], server['user'], server['password'], outinfo))


    print(outinfo)

    url = "https://api.2minlog.com/log"


    for payload in outinfo:
        send_log(url, payload, username, passwd)

    wait_until_next_5_min()
    
   