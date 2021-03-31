
import subprocess
import json
from bson.json_util import dumps
import os
import shutil
import zipfile
import urllib
import yaml 
import psutil
from ast import literal_eval as make_tuple

from flask import request, redirect, render_template, url_for, flash,send_file,session
from flask import jsonify
from app import app

from redis import StrictRedis


from werkzeug.utils import secure_filename

from app.database.elkdb import *
from app.database.dbstuff import *


from app import celery_app as celery_app_controller



SIDEBAR = {
    "sidebar"           : y['admin_sidebar'],
    "open"              : app.config['SIDEBAR_OPEN'],
    'current_version'   : y['Git']['k_version']
}


# =================================================
#               Helper Functions
# =================================================
# return json in a beautifier
def json_beautifier(js):
    return json.dumps(js, indent=4, sort_keys=True)


# ================================ create folder
# create folder if not exists, used to create case upload folder 
def create_folders(path):
    try:
        os.makedirs(path)
        return [True, "Folder ["+path+"] created"]
    except OSError as e:
        if "File exists" in str(e):
            return [True , "Folder ["+path+"] already exists" ]
        else:
            return [False , str(e) ]
    except Exception as e:
        return [False , str(e) ]


# ================================ unzip file
# unzip the provided file to the dst_path
def unzip_file(zip_path,dst_path):
    try:
        createfolders = create_folders(dst_path)
        if createfolders[0] == False:
            return createfolders
        
        with zipfile.ZipFile(zip_path , mode='r') as zfile:
            zfile.extractall(path=dst_path )
        return [True , "All files of ["+zip_path+"] extracted to ["+dst_path+"]"]

    except UnicodeDecodeError as e:
        #handle unicode errors, like utf-8 codec issues
        return [True , "All files of ["+zip_path+"] partialy extracted to ["+dst_path+"]"]
    except Exception as e:
        return [False, "Error extract the zip content: " + str(e)]
    



def process_details(pid):
    proc = psutil.Process(pid)

    # children - workers
    workers = []
    for worker_proc in proc.children():
        worker_details = worker_proc.as_dict()
        # count number of connections per worker
        worker_connections = 0
        if 'connections' in worker_details.keys() and worker_details['connections'] is not None:
            for con in worker_details['connections']:
                dict_conn = dict(con._asdict())
                if dict_conn['status'] == "ESTABLISHED" and dict_conn['laddr'][0] != dict_conn['raddr'][0]:
                    worker_connections += 1
    
        
        workers.append( {
            'status': worker_details['status'],
            'wpid' : worker_details['pid'],
            'cpu_percent' : worker_proc.as_dict()['cpu_percent'],
            'memory_percent' : worker_details['memory_percent'],
            'create_time' : datetime.fromtimestamp(worker_details['create_time']).strftime("%Y-%m-%d %H:%M:%S"),
            'connections' : worker_connections
        } )

    # memory
    proc_mem = dict(proc.memory_info()._asdict())

    # connections
    proc_connection = {}
    if len(proc.connections()) > 0:
        proc_conn = dict(proc.connections()[0]._asdict())
        proc_connection = {
            'status'     : proc_conn['status'],
            'IP'         : proc_conn['laddr'][0],
            'Port'         : proc_conn['laddr'][1]
        }

    proc_dict = proc.as_dict()
    proc_details = {
        'cmdline'         : ' '.join(proc_dict['cmdline']),
        'cpu_num'         : proc_dict['cpu_num'],
        'cpu_percent'     : proc.as_dict()['cpu_percent'],
        'create_time'     : datetime.fromtimestamp(proc_dict['create_time']).strftime("%Y-%m-%d %H:%M:%S"),
        'memory_percent': proc_dict['memory_percent'],
        'name'            : proc_dict['name'],
        'pid'             : proc_dict['pid'],
        'ppid'             : proc_dict['ppid'],
        "status"        : proc_dict['status'],
        'username'        : proc_dict['username'],
        'connection'    : proc_connection,
        'memory'         : proc_mem,
        'workers'        : workers
    }

    return proc_details


# restart service by name
def restart_service(service_name):
    if service_name not in ['elasticsearch' , 'redis-server']:
        return [False , 'invalid service name']


    cmd = './kuiper_install.sh -restart_service ' + service_name
    try:
        p =  subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE)
        (output, p_err) = p.communicate()
        if output.strip().split("\n")[-1].startswith("[+]"):
            return [True , "success"]
        else:
            return [False , "Failed: " + output]
        return output.decode('utf-8').strip()
    except Exception as e:
        return [False , "Failed: " + str(e)]
        

# this function return the status of the provided service name
def get_service_status(service_name):
    try:
        p =  subprocess.Popen(["systemctl", "is-active",  service_name], stdout=subprocess.PIPE)
        (output, p_err) = p.communicate()
        return [True, output.decode('utf-8').strip()]
    except Exception as e:
        return [False , str(e)]



# get the total size of the content of the provided folder path
def get_folder_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += (os.path.getsize(fp) if os.path.isfile(fp) else 0)
    return total_size

# =================================================
#               Flask Functions
# =================================================





# =================== Cases =======================
#call admin page will all content from content_management
@app.route('/admin/')
def home_page():

    
    # check messages or errors 
    message = None if 'message' not in request.args else request.args['message']
    err_msg = None if 'err_msg' not in request.args else request.args['err_msg']

    all_cases = db_cases.get_cases()
    if all_cases[0]:
        return render_template('admin/display_cases.html',SIDEBAR=SIDEBAR,all_cases=all_cases[1] , page_header="Cases" , message = message , err_msg=err_msg)
    else:
        message = all_cases[1]
        return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , page_header="Cases" , message = message , err_msg=err_msg)



# ================================ create case
#create users called from dbstuff
@app.route('/admin/create_case', methods=['GET', 'POST'])
def admin_create_case():
    try:
        if request.method == 'GET':
            return redirect(url_for('home_page', err_msg="Invalid HTTP request method" ))

        if request.method == 'POST':
            casename_accepted_char = 'abcdefghijklmnopqrstuvwxy0123456789_'
            casename = ''.join( [ e for e in request.form['casename'].lower() if e in casename_accepted_char ] )
            casename = casename.lstrip('_')
            #get paramters from the UI query
            case_details = {
                "casename"  : casename,
                "status"    : request.form['status'],
                'date'      : str(datetime.now() ).split('.')[0]
            }
            if request.form['update_or_create_case'] == "create":

                retn_cre = db_cases.create_case( case_details )
                # if failed to create case
                if retn_cre[0] == False:
                    logger.logger(level=logger.ERROR , type="admin", message="Failed creating case ["+casename+"]" , reason=retn_cre[1])
                    return redirect(url_for('home_page', err_msg="Error: " + retn_cre[1] ))
                

                create_indx = db_es.create_index(case_details['casename'])
                
                if create_indx[0] == False:
                    logger.logger(level=logger.ERROR , type="admin", message="Failed creating case index ["+casename+"]" , reason=create_indx[1])
                    return redirect(url_for('home_page', err_msg="Error: " + create_indx[1] ))
                

                logger.logger(level=logger.INFO , type="admin", message="Case ["+casename+"] Created")
                return redirect(url_for('home_page' , message="Case ["+case_details['casename']+"] created  "))

            else:
                retn_cre = db_cases.update_case( case_details['casename'] ,  case_details )
                # if failed to create case
                if retn_cre[0] == False:
                    logger.logger(level=logger.ERROR , type="admin", message="Failed updating case ["+casename+"]" , reason=retn_cre[1])
                    return redirect(url_for('home_page', err_msg="Error: " + retn_cre[1] ))

                logger.logger(level=logger.INFO , type="admin", message="Case ["+casename+"] information updated")
                return redirect(url_for('home_page' , message="Case ["+case_details['casename']+"] updated "))

    except Exception as e:
        logger.logger(level=logger.ERROR , type="admin", message="Exception create/update case" , reason=str(e))
        return redirect(url_for('home_page', err_msg="Error: " + str(e) ))





#create users called from dbstuff
@app.route('/admin/delete_case/<casename>')
def admin_delete_case(casename):

    retn_cre = db_cases.delete_case( casename )
    if retn_cre[0] == False:
        logger.logger(level=logger.ERROR , type="admin", message="Failed deleting case ["+casename+"]" , reason=retn_cre[1])
        return redirect(url_for('home_page', err_msg="Error: [From MongoDB] " + retn_cre[1] ))
    
    retn_cre = db_es.delete_index(casename) # delete case index from elasticsearch 

    if retn_cre[0] == False:
        logger.logger(level=logger.ERROR , type="admin", message="Failed deleting case index ["+casename+"]" , reason=retn_cre[1])
        return redirect(url_for('home_page', err_msg="Error: [From ES] " + retn_cre[1] ))

    logger.logger(level=logger.INFO , type="admin", message="Case ["+casename+"] deleted")
    return redirect(url_for('home_page'))



# =================== Config =======================

# =================== Kuiper Update =======================


@app.route('/admin/check_update')
def config_check_update():

    
    release_url = y['Git']['git_url_release']
    logger.logger(level=logger.INFO , type="admin", message="Start getting latest release from Github: " + release_url)
    try:
        request = urllib.urlopen(release_url)
        response = request.read()
        data = json.loads(response)

        if 200 == request.getcode():
            return json.dumps({'results' : 'true' , 'msg' : data['tag_name']})
        else:
            logger.logger(level=logger.ERROR , type="admin", message="Failed to connect with [" + release_url + "]", reason=data['message'])
            return json.dumps({'results' : 'false' , 'msg' : 'Connection issue: ' + str(request.getcode()) + "<br />" + data['message']})
    except Exception as e:
        logger.logger(level=logger.ERROR , type="admin", message="Failed getting the update", reason=str(e))
        return json.dumps({'results' : 'false' , 'msg' : "Network connection issue: <br />" + str(e)})
    



# =================== Parsers =======================


# show the main config page
@app.route('/admin/config')
def config_page():
    # get all cases 
    all_cases = [] # will not be used
    
    return render_template('admin/configuration.html',SIDEBAR=SIDEBAR, page_header="Configuration")





# add parser information
@app.route('/admin/config/add_parser', methods=["POST"])
def admin_add_parser():
    if request.method == "POST":
        try:
            logger.logger(level=logger.DEBUG , type="admin", message="Start upload parser")
            ajax_j =  request.form.to_dict()
            action = ajax_j['action'] # add or edit
            
            # upload and unzip parser file
            file = request.files['parser_file_field']
            logger.logger(level=logger.DEBUG , type="admin", message="Parser file: " + str(file))

            # if file not selected
            if file.filename == '' and action == 'add':
                logger.logger(level=logger.ERROR , type="admin", message="Parser file not selected")
                return json.dumps({'result' : 'failed' , 'msg' : 'Parser file not selected'})

            # if there is uploaded parser file, unzip it 
            if file.filename != '':
                # remove the old parser folder
                old_parser_folder = db_parsers.get_parser_by_name(ajax_j['name'])
                if old_parser_folder[0] == False:
                    logger.logger(level=logger.ERROR , type="admin", message="Failed retriving parser information ["+ajax_j['name']+"]", reason=old_parser_folder[1])
                    return json.dumps({'result' : 'failed' , 'msg' : 'Failed retriving parser information ['+ajax_j['name']+']'})
                
                
                # getting the uploaded file 
                file_name   = secure_filename(file.filename)
                tmp_path    = app.config['PARSER_PATH'] + "/temp/" +  file_name


                # if the parser found, delete its files
                if old_parser_folder[1] is not None:
                    old_parser_path = os.path.join(app.config['PARSER_PATH'],  old_parser_folder[1]['parser_folder'])
                    try:
                        shutil.rmtree(old_parser_path)
                        
                        logger.logger(level=logger.DEBUG , type="admin", message="Old parser files removed ["+old_parser_path+"]")
                    except Exception as e:
                        logger.logger(level=logger.ERROR , type="admin", message="Failed removing the old parser files ["+old_parser_path+"]", reason=str(e))
                        return json.dumps({'result' : 'failed' , 'msg' : 'Failed removing old parser files'})
                
                # unzip the uploaded parser to the parser folder 
                file.save( tmp_path )
                unzip_fun = unzip_file( tmp_path  , app.config['PARSER_PATH'] + "/" + file_name.split(".")[0] )
                if unzip_fun[0] == True:
                    logger.logger(level=logger.INFO , type="admin", message="unziped the file ["+tmp_path+"]")
                else:
                    logger.logger(level=logger.ERROR , type="admin", message="Failed to unzip file ["+tmp_path+"]", reason=unzip_fun[1])
                    return json.dumps( {'result' : 'failed' , 'msg' : 'Failed to unzip the file'} )
            
                ajax_j['parser_folder'] = file_name.split(".")[0] # this will store the parser folder in parsers/
                
                # if __init__.py file not in the parser folder, create one
                if not os.path.exists(app.config['PARSER_PATH'] + "/" + ajax_j['parser_folder'] + '/__init__.py'):
                    f= open(app.config['PARSER_PATH'] + "/" + ajax_j['parser_folder'] + '/__init__.py',"w+")
                    f.close()


            logger.logger(level=logger.DEBUG , type="admin", message="Parser details: ", reason=json.dumps(ajax_j))

            # reformat the parser important fields into json
            imp_fields_json = []
            imp_fields = ajax_j['important_field'].split('|')
            for i in imp_fields:
                i = i.split(',')
                if len(i) != 2:
                    continue
                imp_fields_json.append({
                    'name' : i[0],
                    'path' : i[1],
                })
            ajax_j['important_field'] = imp_fields_json


            # add parser to database mongoDB
            if action == 'add':
                add_parser = db_parsers.add_parser(ajax_j)
            else:
                add_parser = db_parsers.edit_parser(ajax_j['name'] , ajax_j)

            if add_parser[0] == False:
                logger.logger(level=logger.ERROR , type="admin", message="Failed adding parser to database", reason=add_parser[1])
                ajax_res = {'result' : 'failed' , 'msg' : add_parser[1]}
            else:
                logger.logger(level=logger.INFO , type="admin", message="Parser added to database")
                ajax_res = {'result' : 'success'}


            return json.dumps(ajax_res)



        except Exception as e:
            logger.logger(level=logger.ERROR , type="admin", message="Failed adding/editing parser", reason=str(e))
            return json.dumps({'result' : 'failed' , 'msg' : str(e)})
    else:
        return redirect(url_for('home_page'))



# get parser information
@app.route('/admin/config/get_parsers_ajax', methods=["POST"])
def get_parsers_ajax():
    if request.method == "POST":
        
        parsers = db_parsers.get_parser()
        if parsers[0] == False:
            logger.logger(level=logger.ERROR , type="admin", message="Failed getting parsers details", reason=parsers[1])
            ajax_res = {'result' : 'failed' , 'data' : parsers[1]}
        else:
            ajax_res = {'result' : 'successful' , 'data' : parsers[1]}
        return json.dumps(ajax_res)
    else:
        return redirect(url_for('home_page'))

# delete parser
@app.route('/admin/config/delete_parsers_ajax', methods=["POST"])
def delete_parsers_ajax():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        ajax_data = json.loads(ajax_str)['data']

        logger.logger(level=logger.DEBUG , type="admin", message="Delete parser ["+ajax_data['parser']+"]")
        parser_details = db_parsers.get_parser_by_name(ajax_data['parser'])
        if parser_details[0] == False:
            logger.logger(level=logger.ERROR , type="admin", message="Failed retriving parser information ["+ajax_data['name']+"]", reason=parser_details[1])
            return json.dumps({'result' : 'false' , 'msg' : 'Failed retriving parser information ['+ajax_data['name']+']'})
        

        res = db_parsers.delete_parser_by_name(ajax_data['parser'])
        if res[0]:
            logger.logger(level=logger.INFO , type="admin", message="Parser ["+ajax_data['parser']+"] deleted")
            return json.dumps({'result' : 'true'})
        else:
            logger.logger(level=logger.ERROR , type="admin", message="Failed deleting parser ["+ajax_data['parser']+"]" , reason=res[1])
            return json.dumps({'result' : 'false'})
    else:
        return redirect(url_for('home_page'))





# =================== Rules and Alerts =======================

# add tag to a specifc record
@app.route('/admin/add_rule', methods=["POST"])
def admin_add_rule():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')

        ajax_data = json.loads(ajax_str)['data']

        logger.logger(level=logger.DEBUG , type="admin", message="Add rule ["+ajax_data['rule_name']+"]" )
        res = db_rules.add_rule(ajax_data['rule_name'] , ajax_data['rule'] , ajax_data['rule_severity'] , ajax_data['rule_description'])
        if res[0] == True:
            logger.logger(level=logger.INFO , type="admin", message="Rule ["+ajax_data['rule_name']+"] added" , reason=json.dumps(ajax_data) )
            return json.dumps({"result" : 'success'})
        else:
            logger.logger(level=logger.ERROR , type="admin", message="Failed adding rule ["+ajax_data['parser']+"]" , reason=res[1])
            return json.dumps({"result" : 'failed' , 'message' : res[1]})

    else:
        return json.dumps({"result" : 'failed' , 'message' : res[1]})



# delete rule
@app.route('/admin/delete_rule', methods=["POST"])
def admin_delete_rule():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')

        ajax_data = json.loads(ajax_str)['data']
        logger.logger(level=logger.DEBUG , type="admin", message="Delete rule ["+ajax_data['rule_id']+"]" )

        res = db_rules.delete_rule(ajax_data['rule_id'])
        if res[0] == True:
            logger.logger(level=logger.INFO , type="admin", message="Rule ["+ajax_data['rule_id']+"] deleted")
            return json.dumps({"result" : 'success'})
        else:
            logger.logger(level=logger.ERROR , type="admin", message="Failed deleting rule ["+ajax_data['rule_id']+"]" , reason=res[1])
            return json.dumps({"result" : 'failed' , 'message' : res[1]})

    else:
        return json.dumps({"result" : 'failed' , 'message' : "use POST request"})


# delete rule
@app.route('/admin/update_rule', methods=["POST"])
def admin_update_rule():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')

        ajax_data = json.loads(ajax_str)['data']
        logger.logger(level=logger.DEBUG , type="admin", message="Update rule ["+ajax_data['rule_id']+"]" )

        res = db_rules.update_rule(ajax_data['rule_id'] , ajax_data['new_rule'], ajax_data['new_sev'] , ajax_data['new_desc'])
        if res[0] == True:
            logger.logger(level=logger.INFO , type="admin", message="Rule ["+ajax_data['rule_id']+"] updated" , reason=json.dumps(ajax_data))
            return json.dumps({"result" : 'success'})
        else:
            logger.logger(level=logger.ERROR , type="admin", message="Failed updating rule ["+ajax_data['rule_id']+"]" , reason=res[1])
            return json.dumps({"result" : 'failed' , 'message' : res[1]})

    else:
        return json.dumps({"result" : 'failed' , 'message' : "use POST request"})



#call admin page will all content from content_management
@app.route('/admin/rules', methods=["GET"])
def admin_rules():
    all_rules = db_rules.get_rules()

    if all_rules[0]:
        return render_template('admin/display_rules.html',SIDEBAR=SIDEBAR , all_rules=all_rules[1] , page_header="Rules")
    else:
        logger.logger(level=logger.ERROR , type="admin", message="Failed getting the rules" , reason=all_rules[1])
        return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , message=all_rules[1] , page_header="Cases")




# =================== System haelth =======================




# restart service
@app.route('/admin/system_health/restart_service/<service_name>', methods=["GET"])
def system_health_restart_service(service_name):
    output = restart_service(service_name)
    if output[0] == True:
        logger.logger(level=logger.INFO , type="admin", message="Service ["+service_name+"] has been restarted")
        return json.jumps({'result' : 'success' , 'data': output[1]})
    else:
        logger.logger(level=logger.ERROR , type="admin", message="Failed restarting the service ["+service_name+"]" , reason=output[1])
        return json.jumps({'result' : 'failed' , 'data': output[1]})
    
    




# the system health page
@app.route('/admin/system_health/', methods=["GET"])
def system_health():
    return render_template('admin/system_health.html',SIDEBAR=SIDEBAR, page_header="System Health")








# download files (used to download log files)
@app.route('/admin/system_health/download_logs/<log_type>', methods=["GET"])
def system_health_download_logs(log_type):
    if request.method == "GET":
        log_path = ""
        if log_type == 'Kuiper':
            log_path = y['Logs']['kuiper_log']
        elif log_type == 'Gunicorn':
            log_path = y['Logs']['access_log']
        elif log_type == 'Celery':
            log_path = y['Logs']['celery_log']
        elif log_type == 'Flask':
            log_path = y['Logs']['app_log']
        elif log_type == 'Install':
            log_path = y['Logs']['install_log']
        elif log_type == 'Update':
            log_path = y['Logs']['update_log']
        else:
            return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , page_header="Cases" , message = 'Invalid file requested')

        log_directory =  os.path.join(os.getcwd() , y['Logs']['log_folder']) if y['Logs']['log_folder'].startswith('./') else y['Logs']['log_folder']
        path = os.path.join( log_directory , log_path)
        if os.path.exists(path):
            return send_file(path , as_attachment=True)
        else:
            return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , page_header="Cases" , message = 'File ['+path+'] not found')
    else:
        return redirect(url_for('home_page'))







# request to pull current system health information, return json
@app.route('/admin/system_health_pull/', methods=["GET"])
def system_health_pull():

    logger.logger(level=logger.DEBUG , type="admin", message="System health" )
    # ====================== Gunicorn ========================= # 
    gunicorn_pid             = None
    proc_guni_details         = {
        'status' : 'inactive'
    }
    # get the gunicorn process id 
    try:
        with open( os.path.abspath(y['Logs']['log_folder'] + y['Logs']['gunicorn_pid']), 'r') as f_gunicorn_pid:
            gunicorn_pid = int(f_gunicorn_pid.read())
    except:
        logger.logger(level=logger.WARNING , type="admin", message="Gunicorn file [" + y['Logs']['log_folder'] + y['Logs']['gunicorn_pid'] + "] not exists")
        for proc in psutil.process_iter(['pid' , 'name']):
            if 'gunicorn: master' in proc.info['name']:
                gunicorn_pid = proc.info['pid']


    # if gunicorn process exists, collect its information
    if gunicorn_pid is not None:
        if psutil.pid_exists(gunicorn_pid):
            proc_guni_details['status']     = 'active'
            proc_guni_details['details']    = process_details(gunicorn_pid)
        else:
            logger.logger(level=logger.WARNING , type="admin", message="Gunicorn process id ["+str(gunicorn_pid)+"] not found")
    else:
        logger.logger(level=logger.WARNING , type="admin", message="Gunicorn process not found")
    
    # ====================== Redis ========================= # 
    Redis_details   = {
        'url' : app.config['CELERY_BROKER_URL']
    }

    # get the service status of redis
    redis_service_status = get_service_status("redis-server")
    if redis_service_status[0] == False:
        logger.logger(level=logger.WARNING , type="admin", message="Failed getting the service [redis-server] status" , reason=redis_service_status[1])
        Redis_details['service_status'] = None
    else:
        Redis_details['service_status'] = redis_service_status[1]

     
    if Redis_details['service_status'] == 'active':
        try:
            redisClient     = StrictRedis.from_url(app.config['CELERY_BROKER_URL'])
            list_name       = 'celery'
            redis_tasks     = []
            redis_info      = redisClient.info()
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
        except Exception as e:
            logger.logger(level=logger.WARNING , type="admin", message="Failed getting Redis information" , reason=str(e))

    else:
        logger.logger(level=logger.WARNING , type="admin", message="Redis is not active")

    
    # ====================== Celery ========================= # 
    celery_details  = {}
    worker          = y['CELERY']['CELERY_WORKER_NAME']
    inspect         = celery_app.control.inspect([worker])
    inspect_stats   = None
    if Redis_details['service_status'] == 'active':
        inspect_stats   = inspect.stats() 
    
    if inspect_stats is not None :
        celery_details['status'] = "active"
        inspect_stats   = inspect_stats[worker]
        task_name       = app.config['celery_task_name']

        tasks_details   = {}

        active_tasks    = inspect.active()
        reserved_tasks  = inspect.reserved()
        scheduled_tasks = inspect.scheduled()

        inspect_tasks   = {}

        inspect_tasks['active']    = active_tasks[worker] if active_tasks is not None else []
        inspect_tasks['reserved']  = reserved_tasks[worker] if reserved_tasks is not None else []
        inspect_tasks['scheduled'] = scheduled_tasks[worker] if scheduled_tasks is not None else []
        

        # get celery process information
        celery_details['process'] = None if not psutil.pid_exists(inspect_stats['pid']) else process_details(inspect_stats['pid'])


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
        if Redis_details['service_status'] != 'active':
            celery_details['status'] = "redis not active"
            logger.logger(level=logger.WARNING , type="admin", message="Redis service not working")
        else:
            celery_details['status'] = "inactive"
            logger.logger(level=logger.WARNING , type="admin", message="Celery is not active")
    
    
    # ====================== Disk Space ========================= # 
    try:
        hdd             = {}
        hdd['hdd']                  = dict(psutil.disk_usage('/')._asdict())
        hdd['artifacts_upload']     = get_folder_size(y['Directories']['artifacts_upload'][0] + y['Directories']['artifacts_upload'][1])
        hdd['artifacts_upload_raw'] = get_folder_size(y['Directories']['artifacts_upload_raw'][0] + y['Directories']['artifacts_upload_raw'][1])    
    except Exception as e:
        logger.logger(level=logger.WARNING , type="admin", message="Failed getting disk space health" , reason=str(e))

    # ====================== CPU ========================= # 
    try:
        cpu_percent     = psutil.cpu_percent(interval=None, percpu=True)
        num_cores         = psutil.cpu_count(logical=False)
        num_cpu_thrd    = psutil.cpu_count()
    except Exception as e:
        logger.logger(level=logger.WARNING , type="admin", message="Failed getting CPU health" , reason=str(e))


    # ====================== Memory / Swap ========================= # 
    try:
        memory             = dict(psutil.virtual_memory()._asdict())
        swap            = dict(psutil.swap_memory()._asdict())
    except Exception as e:
        logger.logger(level=logger.WARNING , type="admin", message="Failed getting memory health" , reason=str(e))

    # ====================== ElasticSearch ========================= #
    # get the service status of ElasticSearch
    elasticsearch_details = {}
    elasticsearch_service_status = get_service_status('elasticsearch')
    if elasticsearch_service_status[0] == False:
        logger.logger(level=logger.WARNING , type="admin", message="Failed getting the service [elasticsearch] status" , reason=elasticsearch_service_status[1])
        elasticsearch_details['service_status'] = None
    else:
        elasticsearch_details['service_status'] = elasticsearch_service_status[1]



    # if elasticsearch service active, get more details of it
    if elasticsearch_details['service_status'] == 'active':
        
        # collect nodes info
        es_nodes = db_es.get_nodes_info()
        if es_nodes[0] == False:
            logger.logger(level=logger.WARNING , type="admin", message="Failed getting [elasticsearch] information" , reason=es_nodes[1])

        else:
            elasticsearch_details['nodes'] = {
                'nodes_total'       : es_nodes[1]['_nodes']['total'],
                'nodes_successful'  : es_nodes[1]['_nodes']['successful'],
                'nodes_failed'      : es_nodes[1]['_nodes']['failed'],
                'nodes_details'     : []
            } 

            for node in es_nodes[1]['nodes'].keys():
                elasticsearch_details['nodes']['nodes_details'].append({
                    'name' : node,
                    'host' : es_nodes[1]['nodes'][node]['host'],
                    'processors' : {
                        'allocated' : es_nodes[1]['nodes'][node]['os']['allocated_processors'] , 
                        'avaliable': es_nodes[1]['nodes'][node]['os']['available_processors']
                    },
                    'pid' : es_nodes[1]['nodes'][node]['process']['id'],
                    'version' : es_nodes[1]['nodes'][node]['version'],
                    'paths' : {
                        'data' : ','.join(es_nodes[1]['nodes'][node]['settings']['path']['data']),
                        'home' : es_nodes[1]['nodes'][node]['settings']['path']['home'],
                        'logs' : es_nodes[1]['nodes'][node]['settings']['path']['logs']
                    }

                })
            
            

        # collect indices info and stats info
        elasticsearch_details['indices'] = {}
        es_indices  = db_es.get_indices_settings()
        es_stats    = db_es.get_indices_stats()
        
        if es_indices[0] == False:
            logger.logger(level=logger.WARNING , type="admin", message="Failed getting [elasticsearch] indices" , reason=es_indices[1])
        
        if es_stats[0] == False:
            logger.logger(level=logger.WARNING , type="admin", message="Failed getting [elasticsearch] stats" , reason=es_stats[1])
        
        if es_indices[0] and es_stats[0]:
            # indices info 
            
            for indx_name in es_indices[1].keys():
                
                elasticsearch_details['indices'][indx_name] = {
                    'creation_date'         : datetime.fromtimestamp(float(es_indices[1][indx_name]['settings']['index']['creation_date']) / 1000.).strftime("%Y-%m-%d %H:%M:%S"),
                    'uuid'                  : es_indices[1][indx_name]['settings']['index']['uuid'],
                    'total_fields_limit'    : db_es.get_total_fields_limit(indx_name),
                    'max_result_window'     : es_indices[1][indx_name]['settings']['index']['max_result_window'] if 'max_result_window' in es_indices[1][indx_name]['settings']['index'].keys() else None,
                }

                if indx_name in es_stats[1]['indices']:
                    elasticsearch_details['indices'][indx_name]['total_docs'] = es_stats[1]['indices'][indx_name]['total']['docs']['count']
                    elasticsearch_details['indices'][indx_name]['disk_size']  = es_stats[1]['indices'][indx_name]['total']['store']['size_in_bytes']
                else:
                    elasticsearch_details['indices'][indx_name]['total_docs'] = 0
                    elasticsearch_details['indices'][indx_name]['disk_size']  = 0

            # stats info 
            if 'docs' in es_stats[1]['_all']['total']:
                elasticsearch_details['stats'] = {
                    'total_docs' : es_stats[1]['_all']['total']['docs']['count'],
                    'disk_size' : es_stats[1]['_all']['total']['store']['size_in_bytes'],
                }
            else:
                elasticsearch_details['stats'] = {
                    'total_docs' : 0,
                    'disk_size' : 0,
                }

        elasticsearch_details['elasticsearch_ip'] = y['ElasticSearch']['IP']
        elasticsearch_details['elasticsearch_port'] = y['ElasticSearch']['PORT']
    else:
        logger.logger(level=logger.WARNING , type="admin", message="Elasticsearch service not active")


    # ====================== MongoDB ========================= #    
    mongodb_details = {
        'mongodb_db_IP'     :  y['MongoDB']['DB_IP'],
        'mongodb_db_name'   :  y['MongoDB']['DB_NAME'],
        'mongodb_db_port'   :  y['MongoDB']['DB_PORT'],
        'mongo_health'      : db_health.health

    }

    # get the service status of mongodb
    mongodb_service_status = get_service_status('mongodb')
    if mongodb_service_status[0] == False:
        logger.logger(level=logger.WARNING , type="admin", message="Failed getting the service [mongodb] status" , reason=mongodb_service_status[1])
        mongodb_details['service_status'] = None
    else:
        mongodb_details['service_status'] = mongodb_service_status[1]



    
    # ====================== Build the json result ========================= # 
    system_health     = {
        'disk'                : hdd,
        'Gunicorn'            : proc_guni_details,
        'Celery'            : celery_details,
        'redis'             : Redis_details,
        'CPU': {
            'utilization'     : cpu_percent,
            'cpus_num'         : num_cores,
            'thrds_num'        : num_cpu_thrd
        },
        'memory'            : memory,
        'swap'                 : swap,
        'elasticsearch'     : elasticsearch_details,
        'mongodb'           : mongodb_details
    }
    
    return json.dumps({"result" : 'success' , 'data' : system_health})
