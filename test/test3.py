import json, ssl
from urllib.request import urlopen

#url='https://confluence.corp.server.ca/rest/api/content/87198483'
url='https://confluence.corp.server.ca/rest/api/content/87198483?expand=body.storage.value'
with urlopen(f'{url}',context=ssl._create_unverified_context()) as response:
    x = response.read()

print(x)