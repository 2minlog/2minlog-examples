Setup HDD temperature monitor of our Synology NAS server. 
1.	Enable SNMP on your Synology NAS (Control Panel -> Teminal & SNMP -> SNMP -> SNMPv2 service + username + protocol: SHA + Passwd. You may keep Enable SNMP privacy disabled.
2.	Set up new project in 2minlog.com portal
3.	Modify the synology-temperature script to include 2minlog.com credentials, SNMP Synology NAS credentials and IP address
4.	Run the script on Docker machine within Synology with `docker-compose up -d` command
5.	Set the graphing script in 2minlog.com portal by compying the synology-graph.py script there
6.	Set the display (e.g., https://doc.2minlog.com/tutorials/full-screen-autorefresh and https://doc.2minlog.com/tutorials/old-android-tablet)
7.	Enjoy wonderful graphs!
