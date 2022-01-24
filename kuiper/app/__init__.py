import os 
import yaml

import inspect
from datetime import datetime, timedelta

from flask import Flask, g , session, render_template, Blueprint, send_from_directory, send_file
from flask import request, redirect, url_for
 
import urllib, json
from celery import Celery
from celery.bin import worker
from jinja2 import TemplateNotFound
 
#from flask.ext.celery import Celery

# ldap authentication
from utils.flask_simpleldap import LDAP, LDAPException
from utils.build_timeline import buildTimeline
 
app = Flask(__name__)
  
y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )


app.config['APP_FOLDER']				= os.path.abspath( ''.join(y['Directories']['app_folder']) )			# app folder
app.config['UPLOADED_FILES_DEST'] 		= os.path.abspath( ''.join(y['Directories']['artifacts_upload']) )		# uploaded artifacts files
app.config['UPLOADED_FILES_DEST_RAW'] 	= os.path.abspath( ''.join(y['Directories']['artifacts_upload_raw']) )	# uploaded artifacts raw files

app.config['PARSER_PATH'] 				= os.path.abspath( ''.join(y['Directories']['app_parsers']) )			# parser folder
app.config['SYSTEM_HEALTH_PATH']    	= os.path.abspath( ''.join(y['Directories']['system_health']) )			# system health folder


# ======================= Celery configuration
redis_ip                                = os.getenv('REDIS_IP' , '')
redis_port                              = os.getenv('REDIS_PORT' , '')

celery_broker_url                       = "redis://%s:%s/" %(redis_ip , redis_port) if redis_ip != "" and redis_port !="" else y['CELERY']['CELERY_BROKER_URL']
celery_result_backend                   = "redis://%s:%s/" %(redis_ip , redis_port) if redis_ip != "" and redis_port !="" else y['CELERY']['CELERY_RESULT_BACKEND']

app.config['CELERY_BROKER_URL'] 	    = celery_broker_url
app.config['CELERY_RESULT_BACKEND']     = celery_result_backend
app.config['CELERY_TASK_ACKS_LATE']     = os.getenv('CELERY_TASK_ACKS_LATE', y['CELERY']['CELERY_TASK_ACKS_LATE']).lower() in ("yes", "y", "true",  "t", "1")
app.config['CELERY_IGNORE_RESULT']      = False
app.config['celery_task_name']          = os.getenv('celery_task_name', y['CELERY']['celery_task_name']) 

celery_app = Celery(app , backend =app.config['CELERY_RESULT_BACKEND'] , broker  =app.config['CELERY_BROKER_URL'])

celery_app.conf.worker_max_tasks_per_child=1 # terminate celery worker when done and re-initilize other one to free memory


# ======================== Mongodb configuration
app.config['DB_NAME']                   = os.getenv('MONGODB_DB_NAME', y['MongoDB']['DB_NAME']) 
app.config['DB_IP']                   	= os.getenv('MONGODB_IP', y['MongoDB']['DB_IP'])  
app.config['DB_PORT']                   = os.getenv('MONGODB_PORT', y['MongoDB']['DB_PORT'])  


app.config['SIDEBAR_OPEN']              = y['adminlte']['SIDEBAR_OPEN']

  
# ====================== LDAP configuration 
app.config['LDAP_ENABLED']              = os.getenv('LDAP_ENABLED', y['LDAP_auth']['enabled']).lower() in ("yes", "y", "true",  "t", "1")
app.config['LDAP_HOST']                 = os.getenv('LDAP_HOST', y['LDAP_auth']['LDAP_HOST']) 
app.config['LDAP_PORT']                 = os.getenv('LDAP_PORT', y['LDAP_auth']['LDAP_PORT']) 
app.config['LDAP_SCHEMA']               = os.getenv('LDAP_SCHEMA', y['LDAP_auth']['LDAP_SCHEMA']) 
app.config['LDAP_USE_SSL']              = os.getenv('LDAP_USE_SSL', y['LDAP_auth']['LDAP_USE_SSL']).lower() in ("yes", "y", "true",  "t", "1")
app.config['LDAP_BASE_DN']              = os.getenv('LDAP_BASE_DN', y['LDAP_auth']['LDAP_BASE_DN'])
app.config['LDAP_USERNAME']             = os.getenv('LDAP_USERNAME', y['LDAP_auth']['LDAP_USERNAME'])
app.config['LDAP_PASSWORD']             = os.getenv('LDAP_PASSWORD', y['LDAP_auth']['LDAP_PASSWORD'])
app.config['LDAP_USER_OBJECT_FILTER']   = os.getenv('LDAP_USER_OBJECT_FILTER', y['LDAP_auth']['LDAP_USER_OBJECT_FILTER'])
app.config['LDAP_SESSION_EXPIRATION']   = int(os.getenv('LDAP_SESSION_EXPIRATION', y['LDAP_auth']['session_expiration']))

if app.config['LDAP_ENABLED']:
    ldap = LDAP(app) 

# ======================= Flask configuration
# check whether rhaegal enabled or not
app.config["ENABLE_RHAEGAL"]            = os.getenv('FLASK_ENABLE_RHAEGAL', y['Kuiper']['enable_Rhaegal']).lower() in ("yes", "y", "true",  "t", "1")
app.config['FLASK_LOGS_LEVEL']          = os.getenv('FLASK_LOGS_LEVEL', y['Kuiper']['logs_level']) 
app.config['FLASK_API_TOKEN']           = os.getenv('FLASK_API_TOKEN', y['Kuiper']['api_token']) 
app.config['GIT_URL_RELEASE']           = os.getenv('GIT_URL_RELEASE', y['Git']['git_url_release']) 
app.config['GIT_KUIPER_VERSION']        = os.getenv('GIT_KUIPER_VERSION', y['Git']['k_version']) 
app.config['FLASK_REMOVE_RAW_FILES']    = os.getenv('FLASK_REMOVE_RAW_FILES', y['Kuiper']['RemoveRawFiles']).lower() in ("yes", "y", "true",  "t", "1")
app.config['FLASK_CASE_SIDEBAR']        = y['case_sidebar']

app.config['RHAEGAL_RULES_PATH']        = "./app/utils/Dracarys/Rhaegal/rules/"
app.config['Timeline_Templates']        = "./app/utils/build_timeline/"
app.config['TIMELINE_FOLDER'] 	        = os.path.abspath( ''.join(y['Directories']['artifacts_timeline']) )	    # folder contains the timeline results
app.config['TIMELINE_VIEWS_FOLDER']     = os.path.abspath( ''.join(y['Directories']['artifacts_timeline_views']) )	# folder contains the timeline views


app.config['DOCS_FOLDER'] 	            = os.path.abspath( ''.join(y['Directories']['docs_folder']) )	# doc folder


  
 
app.secret_key = os.getenv('FLASK_SECRET_KEY', y['Kuiper']['secret_key']) 
# ============== logs files
logs_folder                               = y['Logs']['log_folder']


# create of folders
built_in_dirs = [
    app.config['UPLOADED_FILES_DEST'] , 
    app.config['UPLOADED_FILES_DEST_RAW'] , 
    app.config['TIMELINE_FOLDER'],
    logs_folder,
    app.config['SYSTEM_HEALTH_PATH']
    ]
for d in built_in_dirs:
    try:
        os.mkdir(d)
    except:
        pass
 

# ===================== Logger - START ===================== # 
# class Logger to handle all Kuiper logs
class Logger:
    ERROR     = 0
    WARNING   = 1
    INFO      = 2
    DEBUG     = 3
    

    def __init__(self , log_file , level=None):
        self.log_file   = log_file
        self.level      = level if level is not None else self.ERROR
        self.level_names = {
            0 : 'ERROR',
            1 : 'WARNING',
            2 : 'INFO',
            3 : 'DEBUG'
        }

        

        self.logfile_handle = open(log_file , 'a+')

        # if the file not empty write the log header
        if not os.stat(log_file).st_size:
            self.logfile_handle.write('"Timestamp","LogLevel","Reference","Category","Message","Reaspm"\n')

    def logger(self, level , type , message , reason=""):
        if self.level < level:
            return
        ins = inspect.stack()[1]
        caller_function = ins[3]
        caller_line     = ins[2] #inspect.getframeinfo(ins[0].lineno)
        caller_file     = os.path.basename(ins[1])
        msg = '"%s","[%s]","%s","%s","%s","%s"' % (datetime.now() , self.level_names[level] , caller_file + "." + caller_function + "[Lin."+str(caller_line)+"]" , type, message , reason)
        #print msg
        self.logfile_handle.write(msg + "\n")
        self.logfile_handle.flush()

if app.config['FLASK_LOGS_LEVEL'] == 'DEBUG':
    log_level = Logger.DEBUG
elif app.config['FLASK_LOGS_LEVEL'] == 'INFO':
    log_level = Logger.INFO
elif app.config['FLASK_LOGS_LEVEL'] == 'WARNING':
    log_level = Logger.WARNING
else:
    log_level = Logger.ERROR
    
 
logger = Logger(os.path.join(logs_folder , y['Logs']['kuiper_log']) , log_level )

# ===================== Logger - END ===================== # 





from controllers import case_management,admin_management,API_management
   
# redirector to the actual home page 
@app.route('/')
def home():
    return redirect(url_for('home_page'))
 



# ================= ldap authentication 

def is_authenticated():
    return 'last_visit' in session and 'user_id' in session

@app.before_request
def before_request():
    g.user = None
    if request.full_path.startswith('/static') or request.full_path.startswith('/login') or request.full_path.startswith('/logout') or request.full_path.startswith('/error_api'):
        return
    # check if the api token correct
    if request.full_path.lower().startswith('/api'):
        try:
            request_str =  urllib.unquote(request.data).decode('utf8')
        
            # if the request from has the correct token in data field
            request_json = json.loads(request_str)['data']
            if request_json['api_token'] == app.config['FLASK_API_TOKEN']:
                return
        except:
            # if the api token not in the data field, check form field
            if "api_token" in dict(request.form) and request.form["api_token"] == app.config['FLASK_API_TOKEN']:
                return

        return redirect(url_for('error_api', error="invalid token"))

    
    if app.config['LDAP_ENABLED']  == False:
        return

    if is_authenticated():
        session_expired = datetime.now() > session['last_visit'] + timedelta(minutes = app.config['LDAP_SESSION_EXPIRATION'])
        if 'last_visit' not in session or session_expired:
            return redirect(url_for('login', message="Session expired!", url=request.full_path))
        
        if not ( request.full_path.startswith('/case/') and request.full_path.endswith('progress') ):
            session['last_visit'] = datetime.now()

        return 
    

    return redirect(url_for('login', message=None))
    


@app.route('/login', methods=['GET', 'POST'])
def login():
    if app.config['LDAP_ENABLED'] == False:
        return redirect(url_for('home'))

    message = request.args.get('message' , None)
    if is_authenticated() and message != "Session expired!":
        return redirect(url_for('home'))
    if request.method == 'POST':
        user = request.form['user']
        passwd = request.form['passwd']
        try:
            test = ldap.bind_user(user, passwd)
        except LDAPException as e :
            message = str(e)
            return render_template('login.html' , msg=message )

        if test is None or passwd == '':
            
            logger.logger(level=logger.ERROR , type="login", message="Failed to login" , reason="invalid credentials")
            return render_template('login.html' , msg='Invalid credentials')
        else:
            session['user_id'] = request.form['user']
            session['last_visit'] = datetime.now()

            url = request.args.get('url' , None)
            if url is None:
                return redirect(url_for('home'))
            else:
                return redirect(url)

    message = request.args.get('message' , None)
    return render_template('login.html' , msg=message )

@app.route('/logout', methods=['GET'])
def logout():

    if app.config['LDAP_ENABLED'] == False:
        return redirect(url_for('home'))
        
        
    try:
        del session['user_id']
        del session['last_visit']
    except: 
        pass
    
    message = request.args.get('message' , None)
    url     = request.args.get('url' , None)
    if message is not None and url is not None:
        return redirect(url_for('login', message=message, url=request.full_path)) 
    return redirect(url_for('login')) 




@app.route('/error_api' , methods=['GET'])
def error_api():
    error = request.args.get('error' , None)
    return {'API_ERROR' : error}


# ================== docs page
@app.route('/docs/', defaults={'filename': 'index.html'})
@app.route('/docs/<path:filename>')
def documentation(filename):
    return send_from_directory(
        app.config['DOCS_FOLDER'],
        filename
    )
  
