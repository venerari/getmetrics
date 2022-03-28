########### note: this is only use for debugging purposes, check the library/get_metris.py instead ###########

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import sys
import string
import subprocess
import time
import datetime
import re
import glob
import requests

from tinydb import TinyDB, Query
from datetime import date

def converthumantoepochtime(dstr):
     element = datetime.datetime.strptime(dstr,"%Y-%m-%d %H:%M")
     tuple = element.timetuple()
     return time.mktime(tuple)

def main():
    token = sys.argv[1]
    startdatetime = sys.argv[3]
    enddatetime = sys.argv[4]
    nsrange = ""
    if len(sys.argv) == 6:
       nsrange = sys.argv[5].split(" ")
    epochstart = converthumantoepochtime(startdatetime)
    epochend = converthumantoepochtime(enddatetime)
    epochtoday = converthumantoepochtime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    continuex = True 
    error_msg = 0   

    if epochend>epochtoday:
         error_msg=1
         continuex = False
    elif epochstart>epochend and continuex:
         error_msg=2
         continuex = False
    
    epochdiff=int(epochend)-int(epochstart)
    
    if epochdiff<3600 and continuex:
         error_msg=3
         continuex = False
    elif epochdiff>2419200 and continuex:  # match
         error_msg=4
         continuex = False
    
    if continuex:
        if epochdiff >= 3600 and epochdiff < 7200:
             step='14'
        elif epochdiff >= 7200 and epochdiff < 21600:
             step='28'
        elif epochdiff >= 21600 and epochdiff < 43200:
             step='86'
        elif epochdiff >= 43200 and epochdiff < 86400:
             step='172'
        elif epochdiff >= 86400 and epochdiff < 172800:
             step='345'
        elif epochdiff >= 172800 and epochdiff < 604800:
             step='691'
        elif epochdiff >= 604800 and epochdiff < 1209600:
             step='2419'
        elif epochdiff >= 1209600 and epochdiff < 2419200:
             step='4838'
        elif epochdiff == 2419200: # match
             step='9676'
        os.system("rm -f ./dc*.json") # delete all ???     
        os.system("rm -f ./metrics.json")      
        os.system(f"curl -ks -H 'Authorization: Bearer {token}' 'https://prometheus-k8s-openshift-monitoring.apps.{sys.argv[2]}.corp.server.ca/api/v1/query?query=openshift_deploymentconfig_created&time={epochend}&_={epochend}000' > dc.json")        
        f = open("./dc.json")
        data = json.load(f)
        f.close()
        dcl = TinyDB('./dcl.json')
        for _data in data["data"]["result"]:
            def datainsert():
                dcl.insert({'dc': _data["metric"]["deploymentconfig"],'ns': _data["metric"]["namespace"],'getmetric':  f'https://prometheus-k8s-openshift-monitoring.apps.{sys.argv[2]}.corp.server.ca/api/v1/query_range?query=avg(container_cpu_usage_seconds_total%7Bnamespace%3D%27'+_data["metric"]["namespace"]+'%27%2Cpod%3D~%27'+_data["metric"] ["deploymentconfig"]+f'.*%27%7D)%20by%20(namespace)%20&start={epochstart}&end={epochend}&step={step}&_={epochend}000'})        
            if nsrange: # range in namespace
                 cont = [ele for ele in nsrange if(ele in _data["metric"]["namespace"])]  
                 if bool(cont):
                     datainsert()
            else: 
                 datainsert()
        metrics = TinyDB('./metrics.json')
        try:
            f = open("./dcl.json")
            dcp = json.load(f)
            f.close()        
            current_number = 1    
            while current_number <=1000: 
                current_number = str(current_number)
                os.system(f'curl -ks -H "Authorization: Bearer {token}" "'+dcp["_default"][current_number]["getmetric"]+f'" > temp{current_number}.json')
                k = open(f'./temp{current_number}.json')
                temp = json.load(k)
                k.close()        
                dc=dcp['_default'][current_number]['dc']
                ns=dcp['_default'][current_number]['ns']
                for _dat in temp["data"]["result"]:
                    ts2 ='1970/01/01-00'
                    for _val in _dat["values"]:
                        ts = datetime.datetime.fromtimestamp(int(_val[0])).strftime('%d %B %Y')
                        cpu = _val[1]
                        if ts != ts2: 
                            metrics.insert({'dc': dc,'ns': ns,'cpu': cpu, 'date': ts})
                        ts2 = ts
                current_number = int(current_number)
                current_number += 1
        except:
            KeyError    

    os.system("rm -f ./temp*.json")  
    os.system("rm -f ./dc*.json")  
    my_path = f"./metrics.json"
    if continuex and os.path.exists(my_path) and os.path.getsize(my_path) > 0:
         #print('Success metrics.json created!')
         # upload metrics start
         
         savedc = ""
         counter = 1
         for item in metrics:
             if counter > 1 and savedc != item['dc']:
                 one_liner += "\n"
                 break
             if counter == 1:
                 one_liner = f"|| ||{item['date']}||"
             if savedc == item['dc'] and counter > 1:    
                 one_liner += f"{item['date']}||"  
             savedc = item['dc']    
             counter += 1    
         savedc = ""         
         getdc = []
         for item in metrics: 
              if item['dc'] != savedc:
                  getdc.append(item['dc'])
              savedc = item['dc']     
         savedc = ""
         for itemdc in getdc:     
              counter = 1
              for item in metrics:
                  if counter == 1:
                      one_liner += f"| {itemdc[:10]}|"
                  if item['dc'] == itemdc and counter > 1:    
                      one_liner += f"{item['cpu']}|"  
                  counter += 1
              one_liner += "\n"        
         url = "https://confluence.corp.server.ca/rest/api/content/87198483"
         headers = {
           'Authorization': 'Basic c3ZjLWRvcmEtbWV0cmljczpAQyt4S1QwcQ==',
           'Cookie': 'JSESSIONID=045BC72DA68F8D99D93D3B0704FFB243'
         }
         response = requests.request("GET", url, headers=headers, verify=False)
         new_version_number = response.json()['version']['number'] + 1
         payload = json.dumps({
           "id": "87198483",
           "type": "page",
           "status": "current",
           "title": "Dashboard",
           "body": {
             "storage": {
               "value": "{expand:title=CS-LT}{chart:type=xyLine|orientation=vertical|width=1000|dataOrientation=horizontal|timeSeries=true}" + one_liner + "{chart}{expand}",
               "representation": "wiki"
             }
           },
           "version": {
             "minorEdit": True,
             "number": new_version_number
           }
         })
         headers = {
           'Authorization': 'Basic c3ZjLWRvcmEtbWV0cmljczpAQyt4S1QwcQ==',
           'Content-Type': 'application/json',
           'Cookie': 'JSESSIONID=045BC72DA68F8D99D93D3B0704FFB243'
         }
         response = requests.request("PUT", url, headers=headers, data=payload, verify=False)
         # upload metrics end

    elif error_msg == 1:
         print('Error enddate cannot be greater than today date and time!') 
    elif error_msg == 2:
         print('Error startdate should be <= endate!') 
    elif error_msg == 3:
         print('Error timeframe should be at least hour or greater!') 
    elif error_msg == 4:
         print('Error timeframe is only accepting 1 hour up to 4 weeks for now!') 
    elif error_msg == 5: 
         print('Error for testing only!') 
    else:
         print('Error getting metrics!') 


if __name__ == '__main__':
    main()
