# ========================== Descrption
# this script used to collect and push the celery system health
import resources, push_health
import os
import json 
from celery import Celery
import psutil 
from ast import literal_eval as make_tuple

redis_ip                                = os.getenv('REDIS_IP' , '')
redis_port                              = os.getenv('REDIS_PORT' , '')

celery_broker_url                       = "redis://%s:%s/" %(redis_ip , redis_port) if redis_ip != "" and redis_port !="" else "localhost"
celery_result_backend                   = "redis://%s:%s/" %(redis_ip , redis_port) if redis_ip != "" and redis_port !="" else "6379"

def get_celery_info(backend , broker):
    celery_details   = {}
    worker          = None #app.config['CELERY_WORKER_NAME']
    celery_app      = Celery(backend =backend , broker  =broker)
    inspect         = celery_app.control.inspect(timeout=1) 
    
    inspect_stats   = inspect.stats() 
    # get kuiper worker
    for w in inspect_stats.keys():
        if w.startswith("kuiper"):
            worker = w 

    if inspect_stats is not None and  worker is not None:
        celery_details['status'] = "active"
        inspect_stats   = inspect_stats[worker]
        task_name       = os.getenv('celery_task_name' , "N/A") 

        tasks_details   = {}

        active_tasks    = inspect.active()
        reserved_tasks  = inspect.reserved()
        scheduled_tasks = inspect.scheduled()

        inspect_tasks   = {}

        inspect_tasks['active']    = active_tasks[worker] if active_tasks is not None else []
        inspect_tasks['reserved']  = reserved_tasks[worker] if reserved_tasks is not None else []
        inspect_tasks['scheduled'] = scheduled_tasks[worker] if scheduled_tasks is not None else []
        

        # get celery process information
        celery_details['process'] = None if not psutil.pid_exists(inspect_stats['pid']) else resources.process_details(inspect_stats['pid'])


        # get tasks information from celery
        for task_state in inspect_tasks.keys():
            if task_state not in tasks_details.keys():
                tasks_details[task_state] = []

            # get details of each task
            for task in inspect_tasks[task_state]:
                task_args = make_tuple(task['args'])
                tasks_details[task_state].append({
                    'task_id'           : task['id'],
                    'task_case'         : task_args[0],
                    'task_machine'      : task_args[1],
                    'task_arguments'    : str(task_args[2]),
                    'task_ach'          : task['acknowledged'],
                    'task_start_time'   : datetime.fromtimestamp(task['time_start']).strftime("%Y-%m-%d %H:%M:%S"),
                    'worker_pid'        : task['worker_pid']
                })


        celery_details['tasks'] = {
            'total'         : inspect_stats['total'][task_name] if task_name in inspect_stats['total'].keys() else 0, # get the total tasks from stats
            'tasks_details' : tasks_details
        }
    else:
        celery_details['status'] = "inactive"

    return celery_details


info        = get_celery_info(celery_result_backend , celery_broker_url)
resources   = resources.get_system_resources(disk_path="/app/")
url_api     = "http://%s:%s" % (os.getenv("FLASK_IP") , os.getenv("FLASK_PORT") )
api_token   = os.getenv("FLASK_API_TOKEN" , "")


push_health.push_kuiper(url_api=url_api ,api_token=api_token , service='celery' , health={'resources': resources , 'info': info})
