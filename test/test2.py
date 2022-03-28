#!/usr/bin/python

import json

nsrange=["ric-sandbox","servicenow-connector","third","fourth"]
one_liner=["||aaa||","|bbb|","|ccc|","|ddd|"]
new_version_number = 123
_value = []

counter = 0
for _nsrange in nsrange:
    if counter == 0:
       _value = "{expand:title=" + nsrange[counter].upper() + "}{chart:type=xyLine|orientation=vertical|width=1000|dataOrientation=horizontal|timeSeries=true}" + one_liner[counter] + "{chart}{expand}"
    elif counter != 0:
       _value += "{expand:title=" + nsrange[counter].upper() + "}{chart:type=xyLine|orientation=vertical|width=1000|dataOrientation=horizontal|timeSeries=true}" + one_liner[counter] + "{chart}{expand}"    
    counter += 1

x = json.dumps({
        "id": "87198483",
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
# var = 'xxx'
# x.update({"test": f"{var}"})
# sorting result in asscending order by keys:
#sorted_string = json.dumps(x, indent=4, sort_keys=True)
print(x)