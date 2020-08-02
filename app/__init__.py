import os 
import yaml

import inspect
from datetime import datetime

from flask import Flask
from flask import request, redirect, url_for


from celery import Celery
from celery.bin import worker

#from flask.ext.celery import Celery

app = Flask(__name__)


y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )


app.config['APP_FOLDER']				= os.path.abspath( ''.join(y['Directories']['app_folder']) )				# app folder
app.config['UPLOADED_FILES_DEST'] 		= os.path.abspath( ''.join(y['Directories']['artifacts_upload']) )		# uploaded artifacts files
app.config['UPLOADED_FILES_DEST_RAW'] 	= os.path.abspath( ''.join(y['Directories']['artifacts_upload_raw']) )	# uploaded artifacts raw files
app.config['PARSER_PATH'] 				= os.path.abspath( ''.join(y['Directories']['app_parsers']) )			# parser folder


app.config['CELERY_BROKER_URL'] 	    = y['CELERY']['CELERY_BROKER_URL']
app.config['CELERY_RESULT_BACKEND']     = y['CELERY']['CELERY_RESULT_BACKEND']
app.config['CELERY_TASK_ACKS_LATE']     = y['CELERY']['CELERY_TASK_ACKS_LATE']
app.config['CELERY_IGNORE_RESULT']      = False
app.config['celery_task_name']          = y['CELERY']['celery_task_name']

celery_app = Celery(app , backend =app.config['CELERY_RESULT_BACKEND'] , broker  =app.config['CELERY_BROKER_URL'])

celery_app.conf.worker_max_tasks_per_child=1 # terminate celery worker when done and re-initilize other one to free memory

# the worker name format is "<node>@<worker-name>", if the node not specified it will use "celery@<worker-name>"
if "@" not in y['CELERY']['CELERY_WORKER_NAME']:
    y['CELERY']['CELERY_WORKER_NAME'] = "celery@" + y['CELERY']['CELERY_WORKER_NAME']


app.config['DB_NAME']                   = y['MongoDB']['DB_NAME']
app.config['DB_IP']                   	= y['MongoDB']['DB_IP']
app.config['DB_PORT']                   = y['MongoDB']['DB_PORT']

app.config['SIDEBAR_OPEN']              = y['adminlte']['SIDEBAR_OPEN']



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

        

        self.logfile_handle = open(log_file , 'a')

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
        print msg
        self.logfile_handle.write(msg + "\n")
        self.logfile_handle.flush()


if y['Kuiper']['logs_level'] == 'DEBUG':
    log_level = Logger.DEBUG
elif y['Kuiper']['logs_level'] == 'INFO':
    log_level = Logger.INFO
elif y['Kuiper']['logs_level'] == 'WARNING':
    log_level = Logger.WARNING
else:
    log_level = Logger.ERROR
    
logger = Logger(os.path.join(y['Logs']['log_folder'] , y['Logs']['kuiper_log']) , log_level )

# ===================== Logger - END ===================== # 





from controllers import case_management,admin_management



# redirector to the actual home page 
@app.route('/')
def home():
    return redirect(url_for('home_page'))