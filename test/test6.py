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

headers = {'Authorization': 'Bearer sha256~xxxxxxxxxxx'}   
url='https://prometheus-k8s-openshift-monitoring.apps.mssocp4uat.corp.server.ca/api/v1/query?query=openshift_deploymentconfig_created&time=1623585600&_=1623585600000'

response=requests.request("GET", url, headers=headers, verify=False)
data=response.content
_data=json.loads(data)
print(_data)
