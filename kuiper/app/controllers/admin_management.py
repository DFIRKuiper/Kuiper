
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
import uuid

from flask import request, redirect, render_template, url_for, flash,send_file,session
from flask import jsonify
from app import app

from redis import StrictRedis


from werkzeug.utils import secure_filename

from app.database.elkdb import *
from app.database.dbstuff import *




from app import celery_app as celery_app_controller

from io import StringIO
import re

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


# get the list of file paths for rules
def rhaegal_get_rules_files(path):
    res = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".gh"):
                res.append( os.path.join(root , f) )
        
        for d in dirs:
            res += rhaegal_get_rules_files(os.path.join(root , d ))
    return res



# this function parse the rhaegal rules
def rhaegal_parser(path=None , content=None):
    ruleSet = []
    if content is not None:
        string_rules = content.split("\n")
    else:

        with open(path , 'r') as r:
            string_rules = r.readlines()
    
    rules_set = []
    rules = ""
    for line in string_rules:
        if line.startswith("#"):
            pass
        else:
            rules+=line 

    rex = re.compile('((public|private) .*(\n){0,1}\{(.*|\s)+?\})')
    
    ruleSetStr = rex.findall(rules)
    for rule in ruleSetStr:
        rule_info = {}
        ruleDateStr = ""
        typeAndName = re.match("((public|private) (.*)+)",rule[0]).group(0).split()
        rule_info['type'] = typeAndName[0].lower()
        rule_info['name'] = typeAndName[1]


        for line in re.findall("(\s+(.*:)(\s+.*[^\}])+)",rule[0])[0][0].split("\n"):
            if re.match("[\s]+#",line):
                pass
            else:
                ruleDateStr+=line+"\n"
        ruleData = yaml.safe_load(ruleDateStr)
        rule_info['data'] = ruleData

        ruleSet.append(rule_info)

    return ruleSet



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
            casename_accepted_char = 'abcdefghijklmnopqrstuvwxyz0123456789_'
            casename = ''.join( [ e for e in request.form['casename'].lower() if e in casename_accepted_char ] )
            casename = casename.lstrip('_')
            #get paramters from the UI query
            case_details = {
                "casename"  : casename,
                "status"    : request.form['status'],
                'date'      : str(datetime.now() ).split('.')[0]
            }
            if request.form['update_or_create_case'] == "create":
                # ===================== Create case

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
                # ===================  update case 
                retn_cre = db_cases.update_case( case_details['casename'] ,  case_details )
                # if failed to create case
                if retn_cre[0] == False:
                    logger.logger(level=logger.ERROR , type="admin", message="Failed updating case ["+casename+"]" , reason=retn_cre[1])
                    return redirect(url_for('home_page', err_msg="Error: " + retn_cre[1] ))

                if request.form['status'] == "not_active":
                    retn_cre = db_es.close_index(case_details['casename'])
                    if retn_cre[0] == False:    
                        print "Failed closing elasticsearch index ["+casename+"]: " + retn_cre[1]
                        logger.logger(level=logger.ERROR , type="admin", message="Failed closing elasticsearch index ["+casename+"]" , reason=retn_cre[1])
                        return redirect(url_for('home_page', err_msg="Error: " + retn_cre[1] ))
                elif request.form['status'] == "active":
                    retn_cre = db_es.open_index(case_details['casename'])
                    if retn_cre[0] == False:
                        print "Failed opening elasticsearch index ["+casename+"]: " + retn_cre[1]
                        logger.logger(level=logger.ERROR , type="admin", message="Failed opening elasticsearch index ["+casename+"]" , reason=retn_cre[1])
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


@app.route('/admin/config/add_timeline_view' , methods=["POST"])
def add_timeline_view():
    if request.method == "POST":  
        try:
            logger.logger(level=logger.DEBUG , type="admin", message="Start adding/editing timeline view")
            ajax_str =  urllib.unquote(request.data).decode('utf8')
            ajax_j = json.loads(ajax_str)['data']
            logger.logger(level=logger.DEBUG , type="admin", message="Timeline view details: ", reason=json.dumps(ajax_j))
  
            action = ajax_j['action'] # add or edit
            if action == "edit": 
                path                = ajax_j['path']  
                content             = ajax_j['content']   
                
                t                   = buildTimeline.BuildTimeline(views_folder=app.config['TIMELINE_VIEWS_FOLDER'] , fname= None)
                views_folder        = app.config['TIMELINE_VIEWS_FOLDER'] 
                # check if view schema correct
                content_validation  = t.validate_view(content)
                if not content_validation[0]: 
                    return json.dumps({'result' : 'failed' , 'msg' : content_validation[1]})

                views               = t.set_views(content , os.path.join( views_folder , path ) )
  
                if views[0] == False: 
                    logger.logger(level=logger.ERROR , type="admin", message="Failed edting timeline view", reason=views[1])
                    return json.dumps({'result' : 'failed' , 'msg' : views[1]})
                else: 
                    return json.dumps({'result' : 'success'})




            if action == "add":
                path                = str(uuid.uuid4()) + ".yaml"
                content             = ajax_j['content']    
                t                   = buildTimeline.BuildTimeline(views_folder=app.config['TIMELINE_VIEWS_FOLDER'] ,fname=  None) 
                views_folder        = app.config['TIMELINE_VIEWS_FOLDER'] 


                # check if view schema correct
                content_validation  = t.validate_view(content)
                if not content_validation[0]:
                    return json.dumps({'result' : 'failed' , 'msg' : content_validation[1]})

                views               = t.set_views(content , os.path.join( views_folder , path ) )
                
                if views[0] == False:   
                    logger.logger(level=logger.ERROR , type="admin", message="Failed adding timeline view", reason=views[1])
                    return json.dumps({'result' : 'failed' , 'msg' : views[1]})
                else: 
                    return json.dumps({'result' : 'success'})


            return json.dumps({'failed' : 'success' , 'msg' : 'no action specified'})
        except Exception as e:
            logger.logger(level=logger.ERROR , type="admin", message="Failed adding/editing parser", reason=str(e))
            return json.dumps({'result' : 'failed' , 'msg' : str(e)})
    else:
        return redirect(url_for('home_page'))


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




# get parser information
@app.route('/admin/config/get_timeline_views_ajax', methods=["GET"])
def get_timeline_views_ajax():
    if request.method == "GET":  
        try:
            t                   = buildTimeline.BuildTimeline(views_folder=app.config['TIMELINE_VIEWS_FOLDER'] , fname= None)
            views               = t.get_views(app.config['TIMELINE_VIEWS_FOLDER'])
            ajax_res            = {'result' : 'successful' , 'data' : views}
        except Exception as e:
            logger.logger(level=logger.ERROR , type="admin", message="Failed getting timeline views details", reason=str(e))
            ajax_res = {'result' : 'failed' , 'data' : str(e)}
        
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



 
# delete timeline view
@app.route('/admin/config/delete_timeline_view_ajax', methods=["POST"])
def delete_timeline_view_ajax():
    if request.method == "POST":
        try:
            ajax_str =  urllib.unquote(request.data).decode('utf8')
            ajax_data = json.loads(ajax_str)['data']  
            logger.logger(level=logger.DEBUG , type="admin", message="Delete timeline view ["+ajax_data['name']+"]")

            path = ajax_data['path'] 
            name = ajax_data['name']
            views_folder        = app.config['TIMELINE_VIEWS_FOLDER']
              
            t                   = buildTimeline.BuildTimeline(views_folder=views_folder , fname= None)    
            views               = t.delete_views(name , os.path.join( views_folder , path ) )  
            if views[0] == False: 
                logger.logger(level=logger.ERROR , type="admin", message="Failed deleting timeline view", reason=views[1])
                return json.dumps({'result' : 'failed' , 'msg' : views[1]})
            else: 
                return json.dumps({'result' : 'success'})

        except Exception as e: 
            return json.dumps({'result' : 'failed' , 'msg' : str(e)})

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

    rules = []
    # get rhaegal rules 
    rules_path = rhaegal_get_rules_files(app.config['RHAEGAL_RULES_PATH'])
    for f in rules_path:
        try:
            rules_file = rhaegal_parser(path=f)
            for r in range(len(rules_file)):
                rules_file[r]['path'] = f
                rules.append(rules_file[r])
                
        except Exception as e:
            logger.logger(level=logger.ERROR , type="admin", message="Failed getting the rhaegal rules ["+f+"]" , reason=str(e))                
            return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , message="Failed getting the rhaegal rules ["+f+"]:" + str(e) , page_header="Rules")
        
            

            
    logger.logger(level=logger.DEBUG , type="admin", message="Rhaegal rules" , reason=str(len(rules)) + " Rules")

    if all_rules[0]: 
        return render_template('admin/display_rules.html',SIDEBAR=SIDEBAR , all_rules=all_rules[1] , page_header="Rules" , rhaegal_rules=rules)
    else:
        logger.logger(level=logger.ERROR , type="admin", message="Failed getting the rules" , reason=all_rules[1])
        return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , message=all_rules[1] , page_header="Rules")
 

# edit rhaegal rule page 
@app.route('/admin/rules_rhaegal/edit' , methods=['GET' , 'POST'])
def admin_rhaegal_edit():
    # view edit request
    if request.method == "GET":
        path = request.args.get('path' , None)
        rule = request.args.get('rule' , None)
        if path is None or rule is None:
            logger.logger(level=logger.DEBUG , type="admin", message="Rhaegal rules: Create new rule" , reason="")
            return render_template('admin/rhaegal_edit.html',SIDEBAR=SIDEBAR , page_header="Create Rule")            

        logger.logger(level=logger.DEBUG , type="admin", message="Rhaegal rules: Edit" , reason=rule + " - " + path)
        try:
            with open(path) as r:
                ruleStr = r.read()
        except Exception as e:
            logger.logger(level=logger.DEBUG , type="admin", message="Failed to open the rule file ["+path+"]" , reason=str(e))
            return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , message="Failed to open the rule file ["+path+"] - " + str(e)  , page_header="Rhaegal rules")

        return render_template('admin/rhaegal_edit.html',SIDEBAR=SIDEBAR , page_header="Edit Rule" , rulePath=path , ruleName=rule , ruleStr=ruleStr)

    # submit edit request
    elif request.method == "POST":

        ajax_str =  urllib.unquote(request.data).decode('utf8')
        
        ajax_data = json.loads(ajax_str)['data']

        # if create new rule
        if ajax_data['ruleName'] == "":
            path = os.path.join( app.config['RHAEGAL_RULES_PATH'] , ajax_data['rulePath'] ) 
            logger.logger(level=logger.DEBUG , type="admin", message="Create rhaegal file ["+path+"]" )
        
        # if edit rule
        else:
            path = ajax_data['rulePath'] 
            logger.logger(level=logger.DEBUG , type="admin", message="Update rhaegal file ["+path+"]" )

        try:  
            with open(path + ".gh" , 'w') as f:
                f.write(ajax_data['ruleStr'])
            
        except Exception as e:
            logger.logger(level=logger.ERROR , type="admin", message="Failed updating rhaegal file ["+path+"]" , reason=str(e))
            return json.dumps({"result" : 'failed' , 'message' : str(e)})

        return json.dumps({"result" : 'success'})
        

    else:
        return json.dumps({"result" : 'failed' , 'message' : "use GET/POST request"})


@app.route('/admin/rules_rhaegal/delete' , methods=['POST'])
def admin_rhaegal_delete():
    
    if request.method == "POST":

        ajax_str =  urllib.unquote(request.data).decode('utf8')
        
        ajax_data = json.loads(ajax_str)['data']

        logger.logger(level=logger.DEBUG , type="admin", message="Remove rhaegal file ["+ajax_data['rulePath']+"]" )

        os.remove(ajax_data['rulePath'])

        return json.dumps({"result" : 'success'})
        

    else:
        return json.dumps({"result" : 'failed' , 'message' : "use POST request"})



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




# request to pull current system health information, return json
@app.route('/admin/system_health_pull/', methods=["GET"])
def system_health_pull2():
    logger.logger(level=logger.DEBUG , type="admin", message="System health" )
    services = ["redis" , "flask" , "celery" , "mongodb" , "es"]
    system_health = {}
    # read services system health
    for service in services:
        with open(os.path.join( app.config['SYSTEM_HEALTH_PATH'] , service ) , 'r' ) as sys_health:
            system_health[service] = json.load(sys_health)
            if 'datetime' in system_health[service].keys():
                date_obj = datetime.strptime(system_health[service]['datetime'] , "%Y-%m-%d %H:%M:%S.%f")
                date_now = datetime.now()
                system_health[service]["datetime_diff"] = (date_now - date_obj).total_seconds()


    return json.dumps({"result" : 'success' , 'data' : system_health})





