# ========================== Descrption
# this script used to collect and push the redis system health
import resources, push_health
import os
from redis import StrictRedis
import json 
from ast import literal_eval as make_tuple



def get_redis_info(broker_url):
    Redis_details   = {
        'url' : broker_url
    }
    try:
        redisClient     = StrictRedis.from_url(broker_url)

        list_name       = 'celery'
        redis_tasks     = []
        redis_info      = redisClient.info()
    except Exception as e:
        Redis_details['service_status'] = 'in-active'
        return Redis_details

    Redis_details['redis_version'] = redis_info['redis_version']

    
    redis_list_len = None
    for key in redisClient.keys():
        try:
            redis_list_len  = redisClient.llen(key)
            list_name = key
        except:
            pass 
        
    if redis_list_len is not None:
        for indx in range(0 , redis_list_len):
            Redis_task_details = json.loads(redisClient.lindex(list_name , indx) )

            if 'task' not in Redis_task_details['headers']:
                continue
            redis_tasks.append( {
                'task_name'         : Redis_task_details['headers']['task'] , 
                'task_id'           : Redis_task_details['headers']['id'] , 
                'task_arguments'    : make_tuple(Redis_task_details['headers']['argsrepr'] )
            } )

    Redis_details['tasks'] = redis_tasks
    Redis_details['service_status'] = 'active'


    return Redis_details


redis_port  = int(os.getenv("REDIS_PORT" , 6379))
broker_url  = 'redis://localhost:' + str(redis_port)

info        = get_redis_info(broker_url)
resources   = resources.get_system_resources()
url_api     = "http://%s:%s" % (os.getenv("FLASK_IP") , os.getenv("FLASK_PORT") )
api_token   = os.getenv("FLASK_API_TOKEN" , "")


push_health.push_kuiper(url_api=url_api ,api_token=api_token , service='redis' , health={'resources': resources , 'info': info})
