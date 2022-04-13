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

short_description: Push prometheus metrics on cpu avg per deploymentconfig.

version_added: "2.9"

description:
    - This is a custom module to push the prometheus metrics on the Confluence page.
      This is dependent on metrics.json from get_metrics.py.

author:
    - venerari@server.ca

options:
    namespace:
        description:
            - Namespaces list ie '["ns1","ns2","ns3"]'.
              You can put with_items here but you will waste time and slow down the process.
        required: True
        type: List
    conf_token:
        description:
            - Confluence token.
        required: True
        type: String
    conf_url:
        description:
            - url address of confluence ie https://confluence.corp.server.ca/rest/api/content/.
        required: True
        type: String
    conf_page_id:
        description:
            - confluence page id.
        required: True
        type: String

'''

EXAMPLES = '''
---
- name: Call the module to get prometheus metrics
  push_metrics:
    namespace: "['ns-lt', 'ns-dev', 'ns-et']"
    conf_token: 'xxxxxxxxxxxxxxxxx'
    conf_url: 'https://confluence.corp.server.ca/rest/api/content/'
    conf_id: 'xxxxxxxx'
    jsession_id: "xxxxxxxxxxxxxxx"
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
import time
import datetime
import re
import requests

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native
from datetime import date

class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results

def main():

    module_args = dict(
        namespace=dict(required=True, type='list'),         
        conf_token=dict(required=True, type='str'),
        conf_url=dict(required=True, type='str'),
        conf_id=dict(required=True, type='str'),
        jsession_id=dict(required=True, type='str')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    namespace = module.params['namespace'] 
    conf_token = module.params['conf_token']
    conf_url = module.params['conf_url']
    conf_id = module.params['conf_id']
    jsession_id = module.params['jsession_id']
   
    continuex = True
    error_msg = 0
    nsrange = namespace
    if len(nsrange) == 0:
        continuex = False
        error_msg = 5
    
    folder = '/tmp/'
    with open(f'{folder}metrics.json') as json_file:
        metric = json.load(json_file)    
    my_path = f"{folder}metrics.json"
    if continuex and os.path.exists(my_path) and os.path.getsize(my_path) > 0:         
        # upload metrics start
        savedc = ""
        ns_counter = 0
        one_liner = []
        one_liner = ["" for i in range(int(len(nsrange)))]         
        for _nsrange in nsrange:
            counter = 1
            for item in metric['_default']:
                if counter > 1 and savedc != item['dc']:
                    one_liner[ns_counter] += "\n"
                    break
                if counter == 1:
                    one_liner[ns_counter] = f"|| ||{item['date']}||"
                if savedc == item['dc'] and counter > 1:    
                    one_liner[ns_counter] += f"{item['date']}||"  
                savedc = item['dc']    
                counter += 1 
            savedc = ""         
            getdc = []
            for item in metric['_default']: 
                if _nsrange == item['ns']:
                    if item['dc'] != savedc:  # get unique dc name 
                        getdc.append(item['dc'])
                    savedc = item['dc']     
            savedc = ""
            for itemdc in getdc:     
                counter = 1
                for item in metric['_default']:
                    if _nsrange == item['ns']:
                        if counter == 1:
                            one_liner[ns_counter] += f"| {itemdc[:20]}|" # DC name
                        if item['dc'] == itemdc and counter >= 1:    
                            one_liner[ns_counter] += f"{item['cpu']}|" # add the cpu metrics
                        counter += 1
                one_liner[ns_counter] += "\n"      
            ns_counter += 1        
        
        url = f'{conf_url}{conf_id}'
        auth = f'Basic {conf_token}'
        jsessionid = f'JSESSIONID={jsession_id}' 
        headers = {
          'Authorization': auth,
          'Cookie': jsessionid
        }
        response = requests.request("GET", url, headers=headers, verify=False)
        new_version_number = response.json()['version']['number'] + 1

        # loop the wiki charts 
        _value = []
        counter = 0
        for _nsrange in nsrange:
            if counter == 0:
               _value = "{expand:title=" + nsrange[counter].upper() + "}{chart:type=xyLine|orientation=vertical|width=900|dataOrientation=horizontal|timeSeries=true}" + one_liner[counter] + "{chart}{expand}"
            elif counter != 0:
               _value += "{expand:title=" + nsrange[counter].upper() + "}{chart:type=xyLine|orientation=vertical|width=900|dataOrientation=horizontal|timeSeries=true}" + one_liner[counter] + "{chart}{expand}"    
            counter += 1

        payload = json.dumps({
          "id": conf_id,
          "type": "page",
          "status": "current",
          "title": "Dashboard",
          "body": {
            "storage": {
              "value": _value,
              "representation": "wiki"
            }
          },
          "version": {
            "minorEdit": True,
            "number": new_version_number
          }
        })

        headers = {
          'Authorization': auth,
          'Content-Type': 'application/json',
          'Cookie': jsessionid
        }
        try:
            response = requests.request("PUT", url, headers=headers, data=payload, verify=False)        
        except:
            continuex = False
            error_msg = 6
        # upload metrics end
        os.system(f"rm -f {folder}metrics.json") 
        if continuex: 
            result = dict(
                changed=True,
                Response=f'Success metrics uploaded with {response.status_code} !'
            )
            module.exit_json(**result)
        elif error_msg == 6: 
            module.fail_json(msg=f'Error uploading with code {response.status_code}!')     
    elif error_msg == 5: 
        module.fail_json(msg=f'Error namespace is required!') 
    else:
        module.fail_json(msg='Error getting metrics.json or no data available!') 

if __name__ == '__main__':
    main()
