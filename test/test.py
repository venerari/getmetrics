#!/usr/bin/python

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

nsrange = ["cs-dev", "cs-lt"]
dcl1 = TinyDB('./dcl1.json')
for _nsrange in nsrange:
     try:
         f = open("./dcl.json")
         dcp1 = json.load(f)
         f.close()    
         current_number = 1    
         while current_number <=1000: 
             current_number = str(current_number)
             if dcp1['_default'][current_number]['ns'] == _nsrange:
                 dcl1.insert({'ns': dcp1['_default'][current_number]['ns'],'dc': dcp1['_default'][current_number]['dc'],'getmetric': dcp1['_default'][current_number]['getmetric']})
             current_number = int(current_number)
             current_number += 1
     except:
         KeyError    
