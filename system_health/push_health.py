# ========================== Descrption
# This script used to push the system health to kuiper flask service
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime

def push_kuiper(url_api, api_token, service,health):

    json_request = {
        'api_token'     :api_token,
        'service'       : service,
        'health'        : health,
        'datetime'      : str(datetime.now())
    }
    json_string     = json.dumps({'data': json_request})
    response        = requests.post(url_api + "/api/system_health/update", data=json_string , verify=False)
    response_json 	= json.loads(response.content)

    return response_json['result']