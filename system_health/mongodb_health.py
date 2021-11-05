# ========================== Descrption
# this script used to collect and push the redis system health
import resources, push_health
import os
import json 
from pymongo import MongoClient


def get_mongodb_info(DB_NAME, DB_IP , DB_PORT):
    
    MClient = MongoClient(DB_IP + ":" + str(DB_PORT) )

    
    health = {}
    if MClient is None:
        health['connected'] = False
    else:
        health['connected'] = True
        health['alive'] = MClient.alive()
        health['databases_exists'] = True if DB_NAME in MClient.database_names() else False
        
    mongodb_details = {
        'mongodb_db_IP'     :  DB_IP,
        'mongodb_db_name'   :  DB_NAME,
        'mongodb_db_port'   :  DB_PORT,
        'mongo_health'      :  health,
        'service_status'    :  'active' if health['connected'] else 'inactive'
    }
    return mongodb_details


info        = get_mongodb_info(DB_NAME= os.getenv("MONGODB_NAME" , "Kuiper"), DB_IP= os.getenv("MONGODB_IP" , "0.0.0.0") , DB_PORT=os.getenv("MONGODB_PORT" , 27017))
resources   = resources.get_system_resources()
url_api     = "http://%s:%s" % (os.getenv("FLASK_IP") , os.getenv("FLASK_PORT") )
api_token   = os.getenv("FLASK_API_TOKEN" , "")

push_health.push_kuiper(url_api=url_api ,api_token=api_token , service='mongodb' , health={'resources': resources , 'info': info})
