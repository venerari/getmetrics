import json

nsrange=["ns-lt","ns-dev"]
dcl = {}
dcl['mydata'] = []
dcl['mydata'].append({
			"ns": "ns-dev",
			"dc": "ns-dev",
			"getmetric": "x"
})
dcl['mydata'].append({
			"ns": "ns-dev",
			"dc": "cs-dev",
			"getmetric": "y"
})
        
# with open('/tmp/metrics.json', 'w') as outfile:
#     json.dump(dcl, outfile)

# x=json.dumps(dcl, indent=4)
# print(x)

# for _dat in dcl['mydata']:
#     if _dat["ns"] == 'bcs-dev':
#        print('got it')

#print(dcl["mydata"][1]["ns"])
for item in dcl['mydata']:
    print(item['ns'])



'''
{
	"mydata": [{
		"name": "Scott",
		"website": "stackabuse.com",
		"from": "Nebraska"
	}, {
		"name": "Larry",
		"website": "google.com",
		"from": "Michigan"
	}, {
		"name": "Tim",
		"website": "apple.com",
		"from": "Alabama"
	}]
}
'''
