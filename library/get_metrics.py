#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: get_metrics

short_description: Get the prometheus metrics on cpu avg per deploymentconfig and create metrics.json.

version_added: "2.9"

description:
    - This is a custom module to get the prometheus metrics on avg cpu of deploymentconfig per environment/all or per namespace with date ranges and put it in metrics.json. 

author:
    - venerari@server.ca

options:
    ocptoken:
        description:
            - User OCP 4 token.
        required: True
        type: String
    server:
        description:
            - server name of the OCP ie 'mssocp4uat'.
        required: True
        type: String
    startdatetime:
        description:
            - Start date in 'yyyy-MMM-dd HH:mm'.
        required: True
        type: String
    enddatetime:
        description:
            - End date in 'yyyy-MMM-dd HH:mm'.
        required: True
        type: String
    namespace:
        description:
            - Namespaces list ie '["ns1","ns2","ns3"]', you can put this either as one variable or with_items.
              One variable would be faster to run rather than with_items because it will loop.
        required: True
        type: List

'''

EXAMPLES = '''
---
- name: Call the module to get prometheus metrics
  get_metrics:
    ocptoken: sha256~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    server: server1
    startdatetime: "2021-06-03 12:00"
    enddatetime : "2021-06-10 12:00"
    namespace: "{{item}}"
  with_items:                                # THIS WILL LOOP AND SLOW THE PROCESS
    - ns-lt
    - ns-dev
    - ns-et

    -OR-

- name: Call the module to get prometheus metrics
  get_metrics:
    ocptoken: sha256~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    server: server1
    startdatetime: "2021-06-03 12:00"
    enddatetime : "2021-06-10 12:00"
    namespace: "["ns-lt","ns-dev","ns-et"]"  # THIS WILL NOT LOOP AND SPEED UP THE PROCESS
'''

RETURN = '''
---
current:
  description: The output of successful execution
  returned: success
  type: dict
  sample:
        {
            "Response": "Successful",
            "changed": false,
            "failed": false
        }

error:
  description: The output of failed execution
  returned: failure
  type: dict
  sample:
        {
            "changed": false,
            "message": "get_metrics call failed",
            "msg": "Error: failed to get metrics"
        }
        
'''

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
import subprocess as sp

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native

class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results

def converthumantoepochtime(dstr):
     element = datetime.datetime.strptime(dstr,"%Y-%m-%d %H:%M")
     tuple = element.timetuple()
     return time.mktime(tuple)

def main():

    module_args = dict(
        ocptoken=dict(required=False, type='str'),
        server=dict(required=True, type='str'),
        startdatetime=dict(required=False, type='str'),
        enddatetime=dict(required=False, type='str'),
        namespace=dict(required=True, type='list')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    ocptoken = module.params['ocptoken']
    server = module.params['server']
    startdatetime = module.params['startdatetime']
    enddatetime = module.params['enddatetime']
    namespace = module.params['namespace'] 

    continuex = True
    error_msg = 0
    folder = '/tmp/'

    if ocptoken == '' or ocptoken == None:
        ocptoken = sp.getoutput('oc whoami -t')

    if startdatetime == '' and enddatetime == '' or startdatetime == None and enddatetime == None:
        startdatetime = datetime.datetime.now() + datetime.timedelta(days=-7, hours=0) # should always start at 00
        startdatetime = startdatetime.strftime("%Y-%m-%d %H:%M")
        enddatetime = datetime.datetime.now() + datetime.timedelta(hours=-3) # need to deduct 3 hours
        enddatetime = enddatetime.strftime("%Y-%m-%d %H:%M")
    elif startdatetime != '' and enddatetime == '' or startdatetime == '' and enddatetime != '' or startdatetime != None and enddatetime == None or startdatetime == None and enddatetime != None:
        continuex = False
        error_msg = 6

    if continuex:
        currentdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        epochtoday = converthumantoepochtime(currentdate)
        element = datetime.datetime.strptime(startdatetime,"%Y-%m-%d %H:%M")
        tuple = element.timetuple()
        epochstart = time.mktime(tuple)
        epochstart = converthumantoepochtime(startdatetime)
        epochend = converthumantoepochtime(enddatetime)        
    
        if epochend>epochtoday and continuex:
            error_msg=1
            continuex = False
        elif epochstart>epochend and continuex:
            error_msg=2
            continuex = False
        epochdiff=int(epochend)-int(epochstart)
        if epochdiff<172800 and continuex: 
            error_msg=3
            continuex = False
        elif epochdiff>604800 and continuex:  # match 1
            error_msg=4
            continuex = False
        nsrange = namespace
        if len(nsrange) == 0:
            continuex = False
            error_msg = 5

    if continuex:
        if epochdiff >= 3600 and epochdiff < 7200: # 1 hr
            step='14'
        elif epochdiff >= 7200 and epochdiff < 21600: # 2 hr
            step='28'
        elif epochdiff >= 21600 and epochdiff < 43200: # 6 hr
            step='86'
        elif epochdiff >= 43200 and epochdiff < 86400: # 12 hr
            step='172'
        elif epochdiff >= 86400 and epochdiff < 172800: # 1 day
            step='345'
        elif epochdiff >= 172800 and epochdiff < 604800: # 2 day
            step='691'
        elif epochdiff >= 604800 and epochdiff < 1209600: # 1 week     # match 1
            step='2419'
        elif epochdiff == 1209600:  
            step='4838'
        
        # get all deploymentconfig
        url = f'{server}/api/v1/query?query=openshift_deploymentconfig_created&time={epochend}&_={epochend}000'
        _ocptoken = f'Bearer {ocptoken}'
        headers = {'Authorization': _ocptoken}   
        response=requests.request("GET", url, headers=headers, verify=False)
        _data=response.content
        data=json.loads(_data)

        # create the dc, ns and getmetric
        dcl = {}
        dcl['_default'] = []
        for _data in data["data"]["result"]:
            def datainsert():
                calc = 'avg'
                # metric used
                dcl['_default'].append({"dc": _data["metric"]["deploymentconfig"],"ns": _data["metric"]["namespace"],"getmetric": f"{server}/api/v1/query_range?query={calc}(pod%3Acontainer_cpu_usage%3Asum%7Bnamespace%3D%27"+_data["metric"]["namespace"]+"%27%2Cpod%3D~%27"+_data["metric"]["deploymentconfig"]+f".*%27%7D)&start={epochstart}&end={epochend}&step={step}&_={epochend}000"})
            if nsrange: 
                 cont = [ele for ele in nsrange if(ele in _data["metric"]["namespace"])]  # make unique on namespace
                 if bool(cont):
                     datainsert()
            else: 
                 datainsert()

        # sort dcl and save to dcl1
        dcl1 = {}
        dcl1['_default'] = []
        for _nsrange in nsrange:
            for _dcl in dcl['_default']:
                if _dcl['ns'] == _nsrange: 
                    dcl1['_default'].append({"ns": _dcl['ns'],"dc": _dcl['dc'],"getmetric": _dcl['getmetric']})

        # average all metrics per day, limit the data otherwise the graph is not nice and average the cpu metrics
        metric = {}
        metric['_default'] = []
        for _dcl1 in dcl1['_default']:
            url = _dcl1['getmetric']     
            response = requests.request("GET", url, headers=headers, verify=False)
            data = response.content
            _data=json.loads(data)
            dc = _dcl1['dc']
            ns = _dcl1['ns']
            for _dat in _data["data"]["result"]: # this will loop once per deploymentconfig
                ts2 ='01 January 1970'  # put an old date
                counter = 1 # counter is needed on average
                addcpu = float(0)
                avgcpu = float(0)
                for _val in _dat["values"]:   # loop here                     
                    ts = datetime.datetime.fromtimestamp(int(_val[0])).strftime('%d %B %Y') # save the date metric
                    _cpu = f"{float(_val[1]):.12f}"
                    addcpu = float(addcpu) + float(_cpu)
                    if ts != ts2 and counter>1: # if date change then save the metrics, the counter prevents from happening on the beginning
                        addcpu = float(addcpu) - float(_cpu) # deduct cpu that does not belong to the same date
                        counter = counter - 1 # deduct counter that does not belong to the same date
                        avgcpu = float(addcpu) / float(counter)  # calculate the average 
                        _cpu = f"{float(avgcpu):.12f}" # prevent [xxx]e-[x] for it will not graph properly
                        cpu = str(_cpu)
                        metric['_default'].append({'dc': dc,'ns': ns,'cpu': cpu, 'date': ts2}) # store the metrics on the json
                        counter = 1 # counter should start at 1 on the new date
                        addcpu = float(_cpu) # save the cpu on the new date
                        avgcpu = float(0)
                    ts2 = ts # make the timestamps equal
                    counter += 1
                # calculate the last date here 
                avgcpu = float(addcpu) / float(counter)  # calculate the average 
                _cpu = f"{float(avgcpu):.12f}" # prevent [xxx]e-[x] for it will not graph properly
                cpu = str(_cpu)
                metric['_default'].append({'dc': dc,'ns': ns,'cpu': cpu, 'date': ts2}) # store the metrics on the json 
        # store metric to metrics.json    
        with open(f'{folder}metrics.json', 'w') as outfile:
            json.dump(metric, outfile)  
        totalmetrics = len(metric['_default'])              

    my_path = f"{folder}metrics.json"
    if continuex and os.path.exists(my_path) and os.path.getsize(my_path) > 0:         
        result = dict(
            changed=True,
            Response=f'Success metrics.json created {totalmetrics} !'  
        )
        module.exit_json(**result)
    elif error_msg == 1:
        module.fail_json(msg='Error enddate cannot be greater than today date and time!') 
    elif error_msg == 2:
        module.fail_json(msg='Error startdate should be < endate in two days!') 
    elif error_msg == 3:
        module.fail_json(msg='Error timeframe should be at least 2 days or greater!') 
    elif error_msg == 4:
        module.fail_json(msg='Error timeframe is only accepting from 2 days up to 1 week for now!') 
    elif error_msg == 5: 
        module.fail_json(msg=f'Error namespace is required!') 
    elif error_msg == 6: 
        module.fail_json(msg=f'Error startdate and enddate can only be both empty but not one is empty and one has value!') 
    else:
        module.fail_json(msg=f'Error getting metrics or no data available!')

if __name__ == '__main__':
    main()
