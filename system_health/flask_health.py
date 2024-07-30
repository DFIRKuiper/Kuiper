# ========================== Descrption
# this script used to collect and push the flask system health
import resources, push_health
import os
import json 
import psutil

def get_gunicorn_info():
    
    gunicorn_pid              = None
    proc_guni_details         = {
        'status' : 'inactive'
    }
    for proc in psutil.process_iter(['pid' , 'name' , 'cmdline' ,'ppid']):
        if proc.info['ppid'] == 1 and proc.info['name'] == 'gunicorn':
            gunicorn_pid = proc.info['pid'] 

    # if gunicorn process exists, collect its information
    if gunicorn_pid is not None:
        proc_guni_details['status']     = 'active'
        proc_guni_details['details']    = resources.process_details(gunicorn_pid)
    else:
        proc_guni_details['status']     = 'in-active'

    return proc_guni_details

def get_flask_info():
    flask_details   = {}

    return flask_details


info        = get_flask_info()
gunicorn    = get_gunicorn_info()
resources   = resources.get_system_resources(disk_path="/app/")
url_api     = "http://%s:%s" % (os.getenv("FLASK_IP") , os.getenv("FLASK_PORT") )
api_token   = os.getenv("FLASK_API_TOKEN" , "")


push_health.push_kuiper(url_api=url_api ,api_token=api_token , service='flask' , health={'resources': resources , 'info': info , 'gunicorn' : gunicorn})
