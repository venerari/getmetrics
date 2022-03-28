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
import ssl
from tinydb import TinyDB, Query
from datetime import date
#from urllib.request import urlopen

os.system("rm -f ./metrics.json") 
token = 'sha256~ik1_1y12DWD56u5WpxSIVJMR-sj12-qcphHzLcBFwm8'
metrics = TinyDB('./metrics.json')

_token = f'Bearer {token}'
headers = {'Authorization': _token}   
try:
    f = open("./dcl1.json")
    dcp = json.load(f)
    f.close()    
    current_number = 1    
    while current_number <= 1000: 
        current_number = str(current_number)   
        url=dcp["_default"][current_number]["getmetric"]     
        response=requests.request("GET", url, headers=headers, verify=False)
        data=response.content
        _data=json.loads(data)
        dc=dcp['_default'][current_number]['dc']
        ns=dcp['_default'][current_number]['ns']
        for _dat in _data["data"]["result"]:
            ts2 ='01 January 1970'
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

