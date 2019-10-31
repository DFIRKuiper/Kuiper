import os 
import yaml

from flask import Flask
from flask import request, redirect, url_for


from celery import Celery
from flask.ext.celery import Celery

app = Flask(__name__)

y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )


app.config['APP_FOLDER']				= os.path.abspath( ''.join(y['Directories']['app_folder']) )				# app folder
app.config['UPLOADED_FILES_DEST'] 		= os.path.abspath( ''.join(y['Directories']['artifacts_upload']) )		# uploaded artifacts files
app.config['UPLOADED_FILES_DEST_RAW'] 	= os.path.abspath( ''.join(y['Directories']['artifacts_upload_raw']) )	# uploaded artifacts raw files
app.config['PARSER_PATH'] 				= os.path.abspath( ''.join(y['Directories']['app_parsers']) )			# parser folder


app.config['CELERY_BROKER_URL'] 	    = y['CELERY']['CELERY_BROKER_URL']
app.config['CELERY_RESULT_BACKEND']     = y['CELERY']['CELERY_RESULT_BACKEND']
app.config['CELERY_TASK_ACKS_LATE']     = y['CELERY']['CELERY_TASK_ACKS_LATE']
celery = Celery(app)

app.config['DB_NAME']                   = y['MongoDB']['DB_NAME']

app.config['SIDEBAR_OPEN']              = y['adminlte']['SIDEBAR_OPEN']


from controllers import case_management,admin_management




@app.route('/')
def home():
    return redirect(url_for('home_page'))