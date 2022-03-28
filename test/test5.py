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

inc = TinyDB('./increment.json')
ns = ['first','second']

for _ns in ns:
    inc.insert({'dc': 'data','ns': _ns})

#if run this the second time, the json will get incremented until u delete it

