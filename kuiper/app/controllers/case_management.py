#/usr/bin/env python2
# -*- coding: utf-8 -*-

import json
import os
import urllib
import shutil
import yaml 
import zipfile
import hashlib
import base64 

from datetime import datetime

from flask import Flask
from flask import request, redirect, render_template, url_for, flash
from flask import jsonify
from flask import send_file

from app import app

import parser_management

from app.database.dbstuff import *
from app.database.elkdb import *

from werkzeug.utils import secure_filename
from bson import json_util
from bson.json_util import dumps


SIDEBAR = {
    "sidebar"           : app.config['FLASK_CASE_SIDEBAR'],
    "open"              : app.config['SIDEBAR_OPEN'],
    'current_version'   : app.config['GIT_KUIPER_VERSION']
}

RemoveRawFiles = app.config['FLASK_REMOVE_RAW_FILES']  # remove the uploaded raw files after unzip it to the machine files

# =================================================
#               Helper Functions
# =================================================

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

# ================================ remove folder
def remove_folder(path):
    try:
        shutil.rmtree(path)
        return [True, "Folder ["+path+"] removed"]
    except Exception as e:
        return [False, "Error: " + str(e)] 


# ================================ remove file
def remove_file(path):
    try:
        os.remove(path)
        return [True, 'File ['+path+'] removed']
    except Exception as e:
        return [False, "Error: " + str(e)]


# ================================ is file exists
def is_file_exists(path):
    return os.path.isfile(path)


# ================================ MD5 for file
def md5(fname):
    try:
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return [True, hash_md5.hexdigest()]
    except Exception as e:
        return [False, str(e)]

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
    
    
# ================================ list zip file content
# list zip file content
def list_zip_file(zip_path):
    try:
        zip_ref = zipfile.ZipFile(zip_path, 'r')
        zip_content = []
        for z in zip_ref.namelist():
            # skip folders 
            if z.endswith('/'):
                continue
            zip_content.append(z)
        return [True, zip_content]
    except Exception as e:
        return [False, str(e)]


# ================================ json beautifier
# return json in a beautifier
def json_beautifier(js):
    return json.dumps(js, indent=4, sort_keys=True)


# ================================ get important fields
# return json of all parsers and the important fields (field , json path)
def get_CASE_FIELDS():
    parsers_details = db_parsers.get_parser()
    if parsers_details[0] == False:
        return parsers_details # if failed return the error message

    case_fields = {}
    for p in parsers_details[1]:
        case_fields[ p['name'] ] = []
        if 'important_field' in p.keys():
            for f in p['important_field']:
                case_fields[ p['name'] ].append( [ f['name'] , "_source.Data." + f['path'] ] )
    return [True, case_fields]



# ============================= upload files
# this function handle uploaded files, decompress it, create machine if machine uploaded, etc.
def upload_file(file , case_id , machine=None , base64_name=None):
    
    source_filename = secure_filename(file.filename) if base64_name is None else base64.b64decode(base64_name)
    isUploadMachine = True if machine is None else False 
    
    logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Handle uploaded file ["+source_filename+"]")
    # ====== prepare the variables 
    
    temp_filename   = str(datetime.now() ).split('.')[0].replace(' ' , 'T') + "-" + source_filename
    
    if isUploadMachine:
        # if the option is upload machine
        machine_name    = source_filename.rstrip('.zip').replace("/" , "_")
        machine_id      = case_id + "_" + machine_name
    else:
        # if upload artifacts
        machine_id      = machine
    
    
    try: 
        # ======= validate machine exists or not  
        # check if machine already exists
        machine_info = db_cases.get_machine_by_id(machine_id)
        if machine_info[0] == False:
            # if there was exception when checking if the machine exists
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed checking if the machine ["+machine_id+"] already exists", reason=machine_info[1])
            return [False, {'result' : False , 'filename' : source_filename , 'message' : 'Failed checking if the machine already exists: ' + str(machine_info[1])}]


        if isUploadMachine:
            # if upload machine, then make sure there is no other machine already exists
            if machine_info[0] == True and machine_info[1] is not None:
                # if the machine already exists
                logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed uploading machine" , reason="Machine ["+machine_id+"] already exists")
                return [ False, {'result' : False , 'filename' : source_filename , 'message' : 'Machine already exists'}]
        else:
            # if upload artifacts, then make sure there is machine to upload the artifacts to it
            if machine_info[0] == True and machine_info[1] is None:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed uploading artifacts" , reason="Machine ["+machine_id+"] not found")
                return [ False, {'result' : False , 'filename' : source_filename , 'message' : 'Machine not exists'}]


        # ======= create folders 
        # create the machine folder in files folder
        files_folder    = app.config["UPLOADED_FILES_DEST"]     + "/" + case_id + "/" + machine_id + "/"
        raw_folder      = app.config["UPLOADED_FILES_DEST_RAW"] + "/" + case_id + "/" + machine_id + "/"
            
        create_files_folder = create_folders( files_folder )  # create the folder for the case in files if not exists
        create_raw_folder   = create_folders( raw_folder )    # create the folder for the case in raw folder if not exists
        if create_files_folder[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed creating the folder ["+files_folder+"]", reason=create_files_folder[1])
            return [False, {'result' : False , 'filename' : source_filename , 'message' : "Failed creating the folder ["+files_folder+"], " + create_files_folder[1]}]
        if create_raw_folder[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed creating the folder ["+raw_folder+"]", reason=create_raw_folder[1])
            return [False, {'result' : False , 'filename' : source_filename , 'message' : "Failed creating the folder ["+raw_folder+"], " + create_raw_folder[1]}]

        
                

        # ====== save the file
        # save the file to the raw data
        try:
            file.save(raw_folder + temp_filename)   
        except Exception as e:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed saving the file ["+source_filename+"]", reason=str(e))
            return jsonify({'result' : False , 'filename' : source_filename , 'message' : 'Failed saving the file ['+source_filename+']: ' + str(e)})
        

        # ======= check hash if exists        
        file_hash       = md5(raw_folder + temp_filename)
        # get hash values for all files for this machine
        for (dirpath, dirnames, filenames) in os.walk(raw_folder):
            for f in filenames:
                if md5(dirpath + f) == file_hash and f != temp_filename:
                    logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed uploading file ["+temp_filename+"]", reason="Match same hash of file ["+f+"]")
                    return [False, {'result': False , 'filename': source_filename , 'message' : 'The following two files has same MD5 hash<br > - Uploaded: ' + temp_filename + '<br > - Exists: '+f}]
        

        # ====== decompress zip file or move it to files folder
        if temp_filename.endswith(".zip"):
            # if zip file
            # unzip the file to machine files
            try:
                unzip_fun = unzip_file(raw_folder + temp_filename ,  files_folder + temp_filename + "/")

                if unzip_fun[0] == True:
                    
                    
                    if RemoveRawFiles:
                        # remove the raw file
                        remove_raw_files = remove_file(raw_folder + temp_filename)
                        if remove_raw_files[0] == False:
                            logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed removing raw file ["+raw_folder + temp_filename+"]", reason=remove_raw_files[1])


                else:
                    

                    
                    remove_raw_files = remove_file(raw_folder +  temp_filename) # remove file if exists
                    if remove_raw_files[0] == False:
                        logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed removing raw file ["+raw_folder + temp_filename+"]", reason=remove_raw_files[1])

                    remove_files_folder = remove_folder(files_folder + temp_filename + "/") # remove file if exists
                    if remove_files_folder[0] == False:
                        logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed removing files folder ["+files_folder + temp_filename + "/"+"]", reason=remove_files_folder[1])
                    

                    logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed decompressing the file ["+raw_folder + temp_filename+"]", reason=unzip_fun[1])
                    return [False, {'result' : False , 'filename' : source_filename , 'message' : unzip_fun[1]}]
            
            # if unzip failed
            except Exception as e:
                if 'password required' in str(e):
                    logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed decompressing the file ["+raw_folder + temp_filename+"]", reason='password required')
                    return [False, {'result' : False , 'filename' : source_filename , 'message' : 'File require password'}]
                else:
                    logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed decompressing the file ["+raw_folder + temp_filename+"]", reason=str(e))
                    return [False, {'result' : False , 'filename' : source_filename , 'message' : 'Failed to unzip the file: ' + str(e)}]
        else:
            # if not zip file

            try:
                # create folder in files folder to include the file 
                create_files_folder   = create_folders( files_folder + temp_filename + "/" )    # create the folder which will include the uploaded file (we are using folder to keep the original file name untouched)
                if create_files_folder[0] == False:
                    logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed creating the folder ["+files_folder+"]", reason=create_files_folder[1])
                    return [False, {'result' : False , 'filename' : source_filename , 'message' : "Failed creating the folder ["+files_folder+"], " + create_files_folder[1]}]

                shutil.copy(raw_folder + temp_filename, files_folder + temp_filename + "/" + source_filename)  
            except Exception as e:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed moving the file ["+raw_folder + temp_filename+"] to files folder", reason=str(e))
                return [False, {'result' : False , 'filename' : source_filename , 'message' : 'Failed moving the file to files folder: ' + str(e)}]


        # ====== create machine
        if isUploadMachine:
            create_m = db_cases.add_machine({
                'main_case'     : case_id,
                'machinename'   : machine_name.replace("/" , "_")
            })

            if create_m[0] == False: # if creating the machine failed
                remove_file(raw_folder +  temp_filename) # remove file if exists
                remove_folder(files_folder + temp_filename + "/") # remove file if exists

                if remove_file[0] == False:
                    logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed removing files folder ["+raw_folder +  temp_filename + "/"+"]", reason=remove_file[1])

                if remove_folder[0] == False:
                    logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed removing files folder ["+files_folder + temp_filename + "/"+"]", reason=remove_folder[1])

                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed uploading the machine ["+machine_id+"]", reason=create_m[1])
                return jsonify({'result' : False , 'filename' : source_filename , 'message' : create_m[1]}) 

            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: Machine ["+machine_id+"] uploaded")
        else:
            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: File ["+source_filename+"] uploaded to machine ["+machine_id+"]")

        return [True, {'result': True , 'filename' : source_filename, 'message': source_filename}]

    except Exception as e:
        if isUploadMachine:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed uploading the machine", reason=str(e))
        else:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed uploading the artifacts for machine ["+machine_id+"]", reason=str(e))
        return [False, {'result' : False , 'filename' : source_filename , 'message' : "Failed uploading the artifacts for machine ["+machine_id+"]: " + str(e)}]











# export list of results as a response based on the case_id and body, 
# if fields specified the output will be a csv file, if not specified it will be a json file
def export_stream_es(case_id , body, chunk_size , fields = None):
    body['size'] = chunk_size
    body["from"] = 0  
    scroll_id = None
    while True:
        # request the data from elasticsearch
        try:
            if scroll_id is None: 
                res = db_es.query( case_id, body , scroll="5m") 
            else:
                res = db_es.query_scroll( scroll_id=scroll_id, scroll="5m" ) 
 

            if res[0] == False: 
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed export query artifacts from dataabase", reason=res[1])
                yield json.dumps({'success' : False  , 'message' : res[1]} )
 
            buff        = ','.join(fields) if fields is not None and scroll_id is None else ''
            scroll_id   = res[1]['_scroll_id'] 
            results     = res[1]['hits']['hits']
            if len(results):     
                # print the csv header if there is a fields specified
                for rec in results: 
                    if fields is not None:   
                        # if the fields specified, export csv files
                        vals = []   
                        for f in fields:
                            v = json_get_val_by_path(rec['_source'] , f)
                            val = v[1] if v[0] else ""
                            vals.append( val )
                        buff += '\n' + ','.join(vals)
                    else:
                        # if fields not specified, export it is a json
                        buff += json.dumps(rec['_source'])
                    
                yield buff
            else:
                break

        except Exception as e:
            yield json.dumps({'success' : False  , 'message' : str(e)} )


# =================================================
#               Flask Functions
# =================================================
# - Dashboard 
# - Machines
# - Artifacts
# - Timeline
# - Alerts
# - graph


# =================== Dashboard =======================

# ================================ dashboard page
@app.route('/case/<case_id>/dashboard', methods=['GET'])
def case_dashboard(case_id):


    case = db_cases.get_case_by_id(case_id)
    if case[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case details", reason=case[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=case[1])

    
    if case[1] is None:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason='Index not found')
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Case["+case_id+"]: Failed getting case information<br />Index not found")



    # get rules information
    all_rules = db_rules.get_rules()
    if all_rules[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting rules", reason=all_rules[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=all_rules[1])

    
    alerts = {
        "Critical"  : 0,
        "High"      : 0,
        "Medium"    : 0,
        "Low"       : 0,
        "Whitelist" : 0
    }

    # for each rule get total count of each rule and increament the severity of it
    for rule in all_rules[1]:
        body = {
                "query":{
                    "query_string":{
                        "query" : rule['rule'],
                        "default_field": "catch_all"
                    }
                },
                "size":0
        }
        res = db_es.query( case_id, body )
        if res[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting rules", reason=all_rules[1])
            continue

        alerts[rule['rule_severity']] += res[1]['hits']['total']['value']


    # get machines information
    machines = db_cases.get_machines(case_id)
    if machines[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case machines", reason=machines[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=machines[1])

    # dashboard info to be pushed
    dashboard_info = {
        'alerts' : alerts,
        'machines' : machines[1]
    }

    return render_template('case/dashboard.html',case_details=case[1] ,SIDEBAR=SIDEBAR , dashboard_info=dashboard_info)



# =================== Machines =======================

# ================================ list machines
# list all machines in the case
@app.route("/case/<case_id>/" , defaults={'group_name': None})
@app.route("/case/<case_id>/<group_name>")
def all_machines(case_id , group_name):


    # check messages or errors 
    message = None if 'message' not in request.args else request.args['message']
    err_msg = None if 'err_msg' not in request.args else request.args['err_msg']
    # collect information 
    machines        = db_cases.get_machines(case_id , group_name)
    case            = db_cases.get_case_by_id(case_id)
    parsers_details = db_parsers.get_parser()
    groups_list     = db_groups.get_groups(case_id)
    # check if there is error getting the information  
    error = None
    if machines[0] == False:    
        error = ["Case["+case_id+"]: Failed getting case machines" , machines[1]]
    elif case[0] == False:
        error = ["Case["+case_id+"]: Failed getting case information" , case[1]]
    elif case[1] is None:
        error = ["Case["+case_id+"]: Failed getting case information" , 'Index not found']
    elif parsers_details[0] == False:
        error = ["Case["+case_id+"]: Failed getting parsers information" , parsers_details[1]]
    elif groups_list[0] == False:
        error = ["Case["+case_id+"]: Failed getting groups information" , groups_list[1]]


    # add specifiy the selected group in the list
    if group_name is not None:
        for i in groups_list[1]:
            if i['_id'] == case_id + "_" + group_name:
                i['selected'] = True 

 
    if error is not None:
        logger.logger(level=logger.ERROR , type="case", message=error[0], reason=error[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=error[0] + "<br />" + error[1])

    return render_template('case/machines.html',case_details=case[1] , all_machines=machines[1],SIDEBAR=SIDEBAR ,parsers_details =parsers_details[1] , groups_list=groups_list[1] , message = message , err_msg=err_msg)



# ================================ get processing progress
@app.route("/case/<case_id>/progress" , methods=['POST'])
def all_machines_progress(case_id):
    if request.method == 'POST':
        ajax_str            =  urllib.unquote(request.data).decode('utf8')
        machines_list       = json.loads(ajax_str)['machines_list']
        machines_progress   = []
        for machine in machines_list:
            
            machines        = db_files.get_parsing_progress(machine)
            if machines[0]:
                machines_progress.append( {'machine': machine , 'progress' : machines[1] } )
            else:
                logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed getting the process progress for machine ["+machine+"]", reason=machines[1])
                return redirect(url_for('all_machines',case_id=case_id , err_msg=machine[1]))
        return json.dumps(machines_progress)
    else:
        return redirect(url_for('home_page'))

# ================================ machine files status 
# this will list all files and their parser and show their status (done, parsing, pending, etc)
@app.route("/case/<case_id>/machine_files/<machine_id>" , methods=['GET'])
def case_machine_files_status(case_id , machine_id):
    # upload machine page
    if request.method == 'GET':

        case        = db_cases.get_case_by_id(case_id)
        CASE_FIELDS = get_CASE_FIELDS()

        # if there is no case exist
        if case[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason=case[1])
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting case information<br />" + case[1])
        if case[0] == True and case[1] is None:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason='case not found')
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting case information<br />case not found")

        # get files
        files = db_files.get_by_machine(machine_id)
        if files[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting machine files", reason=files[1])
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting machine files<br />" + files[1])
        
        return render_template('case/machine_file_status.html',case_details=case[1] ,SIDEBAR=SIDEBAR, machine_id=machine_id , db_files=files[1]['files'] )




# ================================ disable/enable file processing
# this function disable/enable a selected file on machine for specific parser, so it will exclude it from parsing
# for example disable windows events security file from being parsing
@app.route("/case/<case_id>/disable_enable_selected_files/<machine_id>" , methods=['POST'])
def case_disable_enable_selected_files(case_id , machine_id):
    # upload machine page
    if request.method == 'POST':
        
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        ajax_data = json.loads(ajax_str)['data']
        case = db_cases.get_case_by_id(case_id)
        # if there is no case exist
        if case[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed "+ ajax_data['action']+ " file ["+ajax_data['path']+"]", reason=case[1])
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed "+ ajax_data['action']+ " file ["+ajax_data['path']+"]<br />" + case[1])
        elif case[0] == True and case[1] is None:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed "+ ajax_data['action']+ " file ["+ajax_data['path']+"]", reason='case not found')
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed "+ ajax_data['action']+ " file ["+ajax_data['path']+"]<br />case not found")


        disable = True
        if ajax_data['action'] == 'enable':
            disable = False
        up = db_files.disable_enable_file(machine_id , ajax_data['path'] , ajax_data['parser'] , disable)
        
        if up[0] == True:
            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: File ["+ajax_data['path']+"] "+ ajax_data['action'])
            ajax_data['result'] = True 
        else:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed "+ ajax_data['action']+ " file ["+ajax_data['path']+"]", reason=up[1])
            ajax_data['result'] = False
            
        return jsonify(ajax_data)


# ================================ Upload machines
# upload machine page to upload files to the artifacts file upload,
# this is the page allow to upload multiple zip file, each considered as machine
@app.route("/case/<case_id>/upload_machine" , methods=['POST' , 'GET'])
def case_upload_machine(case_id):
    # upload machine page
    if request.method == 'GET':

        CASE_FIELDS = get_CASE_FIELDS()
        if CASE_FIELDS[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting parsers important fields", reason=CASE_FIELDS[1])
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting parsers important fields<br />" + CASE_FIELDS[1])
            
        case = db_cases.get_case_by_id(case_id)
        if case[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case ["+case_id+"] information", reason=case[1])
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting case information<br />" + case[1])
        elif case[0] == True and case[1] is None:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case ["+case_id+"] information", reason='Index not found')
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting case ["+case_id+"] information<br />Index not found")
        

        return render_template('case/upload_machines.html',case_details=case[1] ,SIDEBAR=SIDEBAR )

    # upload the machine files ajax
    elif request.method == 'POST':
        # get file
        file = request.files['files[]']
        # if there is a file to upload
        if file:
            base64_name = None if 'base64_name' not in request.form else request.form['base64_name'] 
            # start handling uploading the file
            uf = upload_file(file , case_id , base64_name=base64_name)
            return json.dumps(uf[1])

        return json.dumps({'result' : False , 'filename' : '' , 'message' : 'There is no file selected'})
    else:
        return redirect(url_for('home_page'))
        

# ================================ Upload Artifacts
# upload artifacts for specific machine
@app.route('/case/<main_case_id>/uploadartifacts/<machine_case_id>', methods=['POST'])
def main_upload_artifacts(main_case_id,machine_case_id):

    if request.method == 'POST':
        try:
               
            # get file
            file = request.files['files[]']


            # if there is a file to upload
            if file:
                base64_name = None if 'base64_name' not in request.form else request.form['base64_name']       

                # start handling uploading the file
                uf = upload_file(file , main_case_id , machine_case_id , base64_name=base64_name)
                return json.dumps(uf[1])

            return json.dumps({'result' : False , 'filename' : '' , 'message' : 'There is no file selected'})

        except Exception as e:
            logger.logger(level=logger.ERROR , type="case", message="Case["+main_case_id+"]: Failed upload artifacts" , reason=str(e))
            return jsonify({'result':'error' , 'message':str(e)})
            
    else:
        return redirect(url_for('home_page'))
        


# ================================ add machine
# add a machine to the case
@app.route("/case/<case_id>/add_machine/" , methods=['POST','GET'])
def add_machine(case_id):
    if request.method == 'POST':
        machine_details = {
            'machinename'   :request.form['machinename'].replace("/" , "_"),
            'main_case'     :case_id,
            'ip'            :request.form['ip'],

        }

        machine = db_cases.add_machine(machine_details)
        if machine[0]:
            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: Machine ["+machine_details['machinename']+"] created")
            return redirect(url_for('all_machines',case_id=case_id , message= "Machine [" + machine[1].lstrip(case_id + "_") + "] created"))
        else:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed creating machine ["+machine_details['machinename']+"]", reason=machine[1])
            return redirect(url_for('all_machines',case_id=case_id , err_msg=machine[1]))


    else:
        return redirect(url_for('home_page'))

# ================================ delete machine
# delete machine from case
@app.route("/case/<case_id>/delete_machine/<machines_list>" , methods=['GET'])
def delete_machine(case_id , machines_list):
    if request.method == 'GET':

        logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Delete machines" , reason=machines_list)
        # delete machine from mongo db
        for machine in machines_list.split(','):
            db_machine = db_cases.delete_machine(machine)
            if db_machine[0] == False:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed deleting machine ["+machine+"]" , reason=db_machine[1])
                continue

            # delete machines records from elasticsearch
            q = {"query": {
                    "query_string": {
                        "query": "(machine.keyword:\""+machine.replace('-' , '\\-')+"\")"
                    }
                }
            } 
            es_machine = db_es.del_record_by_query(case_id , q)
            if es_machine:
                logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: Machine ["+machine+"] deleted")

            # delete all files
            try:
                files_folder    = app.config["UPLOADED_FILES_DEST"]     + "/" + case_id + "/" + machine + "/"
                raw_folder      = app.config["UPLOADED_FILES_DEST_RAW"] + "/" + case_id + "/" + machine + "/"
                shutil.rmtree(files_folder, ignore_errors=True)
                shutil.rmtree(raw_folder, ignore_errors=True)
                logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: deleted machine folders ["+machine+"]" , reason=files_folder + "," + raw_folder)
            except Exception as e:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed deleting machine folders ["+machine+"]" , reason=str(e))

        return redirect(url_for('all_machines',case_id=case_id))




# ================================ process artifacts
# run the selected parser for the machines specified
@app.route('/case/<main_case_id>/processartifacts/<machine_case_id>/<parser_name>', methods=['GET'])
def main_process_artifacts(main_case_id,machine_case_id,parser_name):
    logger.logger(level=logger.DEBUG , type="case", message="Case["+main_case_id+"]: Start processing machine ["+machine_case_id+"], parsers ["+parser_name+"]")

    parsers = parser_name.split(',')
    task = parser_management.run_parsers.apply_async((main_case_id,machine_case_id,parsers) , link_error=parser_management.task_error_handler.s())
    #task = parser_management.run_parsers.apply_async((main_case_id,machine_case_id,parsers))
    logger.logger(level=logger.DEBUG , type="case", message="Case["+main_case_id+"]: task ID ["+task.id+"]")
    return jsonify({'data': 'started processing'})







# ================================ add group
# add a group to the case
@app.route("/case/<case_id>/add_group" , methods=['POST','GET'])
def add_group(case_id):
    
    if request.method == 'POST':
        group_name  = request.form['group_name']
        group       = db_groups.add_group(case_id , group_name)

        if group[0]:
            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: Group ["+group_name+"] created")
            return redirect(url_for('all_machines',case_id=case_id , message= "Group ["+group_name+"] created"))
        else:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed creating group ["+group_name+"]", reason=group[1])
            return redirect(url_for('all_machines',case_id=case_id , err_msg=group[1]))

    else:
        return redirect(url_for('home_page'))






# ================================ assign to group 
# assign the selected machines to group
@app.route("/case/<case_id>/assign_to_group/" , methods=['POST'])
def assign_to_group(case_id):
    
    if request.method == 'POST':
        ajax_str        =  urllib.unquote(request.data).decode('utf8')
        machines_list   = json.loads(ajax_str)['machines_list']
        group_name      = json.loads(ajax_str)['group_name']
        res       = db_cases.assign_to_group(machines_list , group_name)

        if res[0]:
            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: assigned machines to group ["+group_name+"]" , reason=",".join(machines_list))
            return json.dumps({'result' : 'successful' , 'message' : 'assigned to groups'})
        else:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed assigning  machines to group ["+group_name+"]", reason=res[1])
            return json.dumps({'result' : 'failed' , 'message' : res[1]})

    else:
        return redirect(url_for('home_page'))




# ================================ deassign from group 
# deassign the selected machines from group
@app.route("/case/<case_id>/deassign_from_group/" , methods=['POST'])
def deassign_from_group(case_id):
    
    if request.method == 'POST':
        ajax_str        =  urllib.unquote(request.data).decode('utf8')
        machines_list   = json.loads(ajax_str)['machines_list']
        group_name      = json.loads(ajax_str)['group_name']
        res       = db_cases.deassign_from_group(machines_list , group_name)

        if res[0]:
            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: deassigned machines from group ["+group_name+"]" , reason=",".join(machines_list))
            return json.dumps({'result' : 'successful' , 'message' : 'deassigned from group'})
        else:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed deassigning  machines from group ["+group_name+"]", reason=res[1])
            return json.dumps({'result' : 'failed' , 'message' : res[1]})

    else:
        return redirect(url_for('home_page'))






# ================================ deassign to group 
# deassign the selected machines from group
@app.route("/case/<case_id>/delete_group/<group_name>" , methods=['GET'])
def delete_group(case_id , group_name):
    
    if request.method == 'GET':
        res       = db_groups.delete_group(case_id , group_name)

        if res[0]:
            logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: Group ["+group_name+"] deleted")
            return json.dumps({'result' : 'successful' , 'message' : 'Group deleted'})
        else:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed deleting group ["+group_name+"]", reason=res[1])
            return json.dumps({'result' : 'failed' , 'message' : res[1]})

    else:
        return redirect(url_for('home_page'))












# =================== Artifacts =======================


# ================================ get artifacts data types
# get all the list of artifacts for this case
@app.route('/case/<case_id>/browse_artifacts_list_ajax', methods=['POST'])
def browse_artifacts_list_ajax(case_id):

    if request.method == "POST":
        try:
            ajax_str    =  urllib.unquote(request.data).decode('utf8')
            ajax_data   = json.loads(ajax_str)['data']
            body = {
                "size":30,
 
            }
            body = {
                "query": {
                    "query_string" : {
                        "query" : ajax_data['query'],
                        "default_field" : "catch_all"
                    }
                } ,
                "size":0
            }
            
            body["aggs"] = {
                    "data_type": {
                        "terms" : {
                            "field" : "data_type.keyword",
                            "size" : 500,
                            "order": {
                                "_key": "asc"
                            }
                        }
                    }
                }
            logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Query artifacts list", reason=json.dumps(body))
            res = db_es.query( case_id, body )
            if res[0] == False:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed query artifacts list from dataabase", reason=res[1])
                return json.dumps({'res_total' : 0 , 'res_records' : [] , 'aggs' : []})

            aggs_records = res[1]["aggregations"]["data_type"]["buckets"]
            res_records = res[1]['hits']['hits']
            res_total   = res[1]['hits']['total']['value']
             
            return json.dumps({"res_total" : res_total , "res_records" : res_records , 'aggs' : aggs_records})
  
        except Exception as e:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed query artifacts list from dataabase", reason=str(e))
            return json.dumps({'res_total' : 0 , 'res_records' : [] , 'aggs' : []})
    else:
        return redirect(url_for('home_page'))

# ================================ get artifacts records ajax
# retrive all artifacts records using ajax
@app.route('/case/<case_id>/browse_artifacts_ajax', methods=["POST"])
def case_browse_artifacts_ajax(case_id):
    if request.method == "POST": 
        try:
            records_per_page = 30
            ajax_str =  urllib.unquote(request.data).decode('utf8')
            ajax_data = json.loads(ajax_str)['data']
            body = {
                "from": int(ajax_data["wanted_page"]) * records_per_page,
                "size":records_per_page,
            }
            if "query" in ajax_data.keys() and ajax_data['query'] != "None":
                body["query"] = {
                    "query_string" : {
                        "query" : ajax_data['query'],
                        "default_field" : "catch_all"
                    }
                } 

            if "sort_by" in ajax_data.keys() and ajax_data['sort_by'] != "None":
                order = "asc" if ajax_data['sort_by']['order'] == 0 else "desc"
                body["sort"] = {
                    ajax_data['sort_by']['name'] : {"order" : order}
                } 
               
            if "group_by" in ajax_data.keys() and ajax_data['group_by'] != "None" and "fields" in ajax_data['group_by'].keys() and len(ajax_data['group_by']['fields']):
                body['size'] = 0 # if the data came from aggs, then no need for the actual data
                  
                # specifiy whether it is multi fields or single field 
                isSingleField = len(ajax_data['group_by']["fields"]) == 1
                
                # sort buckets
                sort_by_order = "asc" if "sort_count" in ajax_data['group_by'].keys() and ajax_data['group_by']["sort_count"] == "asc" else "desc"

                # agg terms
                aggs_dict = {
                    "size"                      : 1000 ,    
                    "show_term_doc_count_error" : True , 
                    "order"                     : {"_count" : sort_by_order}
                }
                if isSingleField:
                    terms                   = ajax_data['group_by']["fields"][0] + ".keyword"
                    aggs_type               = "terms"
                    aggs_dict["field"]      = terms
                    aggs_dict["missing"]    = ""
                else: 
                    terms                   = []
                    for t in ajax_data['group_by']["fields"]:
                        terms.append( { "field" : t + ".keyword" , "missing" : ""} )     
                    aggs_type               = "multi_terms" 
                    aggs_dict["terms"]      = terms
                  
                body["aggs"] = {     
                    "group_by" : {
                        aggs_type : aggs_dict,  
                        "aggs" : {
                            "my_buckets" : { 
                                "bucket_sort" : {   
                                    "from" : int(ajax_data["wanted_page"]) * records_per_page,
                                    "size" : records_per_page,
                                }, 
                            }, 
                            "group_by_top_hits": {
                                "top_hits" : {
                                    "size" : ajax_data['group_by']['size'],     
                                },       
                            }, 
                        },  
                    },      
                    "get_total": {
                        aggs_type : aggs_dict
                    },   
                    "get_total_stats": {
                        "stats_bucket": {
                            "buckets_path": "get_total._count" 
                        } 
                    }
                } 
            logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Query artifacts", reason=json.dumps(body))
            res = db_es.query( case_id, body )
            if res[0] == False:
                print res[1]   
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed query artifacts from dataabase", reason=res[1])
                return json.dumps({'res_total' : 0 , 'res_records' : [] , 'aggs' : []})

            res_records = res[1]['hits']['hits']
            res_total   = res[1]['hits']['total']['value']
            aggs_records= res[1]["aggregations"]["group_by"]["buckets"] if "aggregations" in res[1].keys() else []
    
            # this function get the record and retrive the machine name from the database and enrich it
            def get_machine_by_id(record):
                if "machine" in record['_source'].keys():
                    machine = db_cases.get_machine_by_id(record['_source']['machine'])
                    if machine[0] == True and machine[1] is not None:
                        record['_source']['machinename'] = machine[1]['machinename']
                    else:
                        record['_source']['machinename'] = record['_source']['machine']
                        logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed getting the machine name", reason=machine[1])


            for i in range( 0  , len(res_records) ):    
                get_machine_by_id(res_records[i])
            
            if len(aggs_records):   
                res_total = res[1]["aggregations"]["get_total_stats"]['count']
                """
                res_records = []
                for i in range(0 , len(aggs_records)):
                    res_records.append( aggs_records[i]["key"] )
                """    
                res_records = []
                 
                for i in range(0 , len(aggs_records)):
                    for r in range(0 , len(aggs_records[i]['group_by_top_hits']['hits']['hits'])):
                        get_machine_by_id(aggs_records[i]['group_by_top_hits']['hits']['hits'][r])
                    
                    rec = aggs_records[i]['group_by_top_hits']['hits']['hits'][0]
                    rec['group_by'] = {
                        'key'       : aggs_records[i]['key'],
                        'doc_count' : aggs_records[i]['doc_count']
                    } 
 
                    # if used a single field, then include it on a list to match the multi-fields group by
                    if isSingleField:
                        rec['group_by']['key'] = [rec['group_by']['key']]
                    res_records.append( rec )
                


            ajax_res = {"res_total" : res_total , "res_records" : res_records , 'aggs' : ajax_data['group_by']["fields"]}

            return json.dumps(ajax_res)
   
 
        except Exception as e:
            print str(e)
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting the browser artifacts", reason=str(e))
            return json.dumps({"res_total" : 0 , "res_records" : [], 'aggs' : None})

    else:
        return redirect(url_for('home_page'))


# ================================ get artifacts data types
# get all artifacts for case
@app.route('/case/<case_id>/browse_artifacts', methods=['GET'])
def case_browse_artifacts(case_id):  
   
    CASE_FIELDS = get_CASE_FIELDS()
    if CASE_FIELDS[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting parsers important fields", reason=CASE_FIELDS[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting parsers important fields<br />" + CASE_FIELDS[1])
            


    case = db_cases.get_case_by_id(case_id)
    if case[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information" , reason=case[1])
        return render_template('case/error_page.html',case_details=case[1] ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting case information, <br />"+case[1])
    
    if case[1] is None:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason='Index not found')
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Case["+case_id+"]: Failed getting case information<br />Index not found")

    
    # get all fields from elasticsearch
    # used for advanced search to list all fields when searching
    fields_mapping = db_es.get_mapping_fields(case_id)
    if fields_mapping[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting the mapping fields " , reason=fields_mapping[1])
        return render_template('case/error_page.html',case_details=case[1] ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting the mapping fields for case ["+case_id+"], <br />"+fields_mapping[1])
        
    
    query = {
            "AND" : []
            }

    if 'q' in request.args:
        try:
            query = json.loads(urllib.unquote(request.args['q']).decode('utf-8'))
        except Exception as e:
            pass
   
    if 'machine' in request.args:
        query["AND"].append({'==machine' : request.args['machine']})

    if 'rule' in request.args:
        query['AND'].append({'==rule' : request.args['rule']})

 

    group = None 
    if 'group' in request.args:
        try:
            machines        = db_cases.get_machines(case_id , request.args['group'])
            if machines[0] == False:    
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case machines" , reason=machines[1])
            else:  
                group = {
                    'group' : request.args['group'],
                    'machines' : []
                }
                for m in machines[1]:  
                    group['machines'].append(case_id + "_" + m['machinename'])
                      
                    
        except Exception as e:  
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case machines" , reason=machines[1])

  
    # get all rules
    all_rules = db_rules.get_rules()
    if all_rules[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting the rules information" , reason=all_rules[1])
        return render_template('case/error_page.html',case_details=case[1] ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting the rules information, <br />" + all_rules[1])
 
    q = json.dumps(query)   
    return render_template('case/browse_artifacts.html',case_details=case[1] ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , search_query = q , fields_mapping=fields_mapping[1] , rules = all_rules[1] , group=group)



  
@app.route('/case/<case_id>/browse_artifacts_export' , methods=['POST'])
def browse_artifacts_export(case_id):
    if request.method == "POST":
        try:
            
            request_str =  urllib.unquote(request.data).decode('utf8')
            request_json = json.loads(request_str)['data']
                
            logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Browse artifacts export", reason=json.dumps(request_json))

            # == from - to
            body = {}
            # == query   
            query = '*' 
            if 'query' in request_json.keys() and request_json['query'] != None:
                request_json['query'] = request_json['query'].strip()
                query = '*' if request_json['query'] == "" or request_json['query'] is None else request_json['query']
                body["query"] = {
                    "query_string" : {
                        "query" : '!(data_type:\"tag\") AND ' + query,
                        "default_field" : "catch_all"
                    }
                }
            # == sort  
            if 'sort_by' in request_json.keys() and request_json['sort_by'] != None:
                order = "asc" if request_json['sort_by']['order'] == 0 else "desc"
                body["sort"] = {request_json['sort_by']['name'] : {"order" : order}}
            else:
                body["sort"] = {'Data.@timestamp' : {"order" : 'asc'}}
            

            # == fields
            fields = None
            if 'fields' in request_json.keys() and request_json['fields'] != None :
                fields = request_json['fields']
                body['_source'] = {}
                body['_source']['includes'] = fields 
  
   
            logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Export Query artifacts", reason=json.dumps(body))

            from flask import Response  

            # get total number of records
            body['size'] = 0
            res = db_es.query( case_id, body) 

            if res[0] == False: 
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed export query artifacts from dataabase", reason=res[1])
                return json.dumps({"res_total" : 0 , "res_records" : []})
            total_records = res[1]['hits']['total']['value']

            return Response( 
                        export_stream_es(case_id=case_id, body=body , chunk_size=30 , fields=fields),
                        mimetype='text/csv',
                        headers= {"total" : str(total_records)}
                    )
                      
   
        except Exception as e:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed exporting the artifacts", reason=str(e))
            return json.dumps({"res_total" : 0 , "res_records" : []})

    else:
        return redirect(url_for('home_page'))


# =================== Timeline =======================

# ================================ timeline page
# get the time line page
@app.route('/case/<case_id>/timeline', methods=['GET'])
def case_timeline(case_id):

    
    CASE_FIELDS = get_CASE_FIELDS()
    if CASE_FIELDS[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting parsers important fields", reason=CASE_FIELDS[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting parsers important fields<br />" + CASE_FIELDS[1])
            

    case = db_cases.get_case_by_id(case_id)
    if case[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason=case[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting case information<br />" + case[1])
    
    if case[1] is None:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason='Index not found')
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Case["+case_id+"]: Failed getting case information<br />Index not found")

    return render_template('case/timeline.html',case_details=case[1] ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1])


# ================================ get tags ajax
# get all tags for the case via ajax
@app.route('/case/<case_id>/timeline_ajax', methods=['POST'])
def case_timeline_ajax(case_id ):
    if request.method == "POST":
        try:
            ajax_str =  urllib.unquote(request.data).decode('utf8')
            ajax_data = json.loads(ajax_str)['data']


            body = {
                "query": {
                    "query_string" : {
                        "query" : 'data_type:tag'
                    }
                },
                "sort":{
                    "Data.@timestamp" : {"order" : "asc"}
                },
                "size": 2000
            }
            res = db_es.query( case_id, body )

            if res[0] == False:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed retriving timeline from database", reason=res[1])
                return json.dumps( {'result': 'failed' , 'tags' : res[1]} )


            total_tags  = res[1]['hits']['total']['value']
            tags        =  res[1]['hits']['hits']


            for t in range(0 , len(tags)):
                if 'record_id' in tags[t]['_source']['Data'].keys():
                    record_id = tags[t]['_source']['Data']['record_id']
                    rec = db_es.get_record_by_id(case_id , record_id)
                    if rec[0] == False:
                        logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed getting record details in timeline", reason=rec[1])

                    if rec[0] == True and rec[1] != False:
                        tags[t]['_source']['Data']['record_details'] = rec[1]


            return json.dumps({ 'result' : 'successful' , "tags" : tags})

        except Exception as e:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed retriving timeline", reason=str(e))
            return json.dumps( {'result': 'failed' , 'tags' : "Failed retriving timeline" + str(e)} )

    else:
        return redirect(url_for('home_page'))

# ================================ delete tag ajax
# delete a specific tag by its ID
@app.route('/case/<case_id>/timeline_delete_tag_ajax', methods=['POST'])
def case_timeline_delete_tag(case_id ):
    if request.method == "POST":
        ajax_str    =  urllib.unquote(request.data).decode('utf8')
        ajax_data   = json.loads(ajax_str)['data']
        logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Delete tag", reason=json.dumps(ajax_data))

        tag_id      =  ajax_data['tag_id']
        record_id   = None if 'record_id' not in ajax_data.keys() else ajax_data['record_id']

        # delete the tag record
        delete = db_es.del_record_by_id( case_id = case_id , record_id = tag_id)
        if delete[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed deleting tag", reason=delete[1])
            return json.dumps({'result' : 'failed' , 'data': 'Failed:' + delete[1]})
        
        # if the tag associated with artifact record
        if record_id is not None:
            # delete the tag record from record
            update_field = db_es.update_field( {"script": "ctx._source.remove(\"tag_id\");ctx._source.remove(\"tag_type\")"}  , record_id , case_id)
            if update_field[1] == False:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed adding tag_id to artifact record", reason=update_field[1])
                return json.dumps({'result' : 'failed' , 'data': 'Failed deleting tag_id from artifact record: ' + update_field[1]})



        logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: tag ["+tag_id+"] deleted")
        return json.dumps({'result' : 'successful'})
    else:
        return redirect(url_for('home_page'))

# ================================ add tag ajax
# add tag to a specifc record
@app.route('/case/<case_id>/add_tag_ajax', methods=["POST"])
def case_add_tag_ajax(case_id):
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        record_id = None
        ajax_data = json.loads(ajax_str)['data']

        Data = {
            "tag"           : ajax_data['tag'] ,
            "@timestamp"    : ajax_data['time'],
            'tag_type'      : ajax_data['tag_type']
        }

        if 'doc_id' in ajax_data.keys():
            Data['record_id']   = ajax_data['doc_id']
            record_id           = ajax_data['doc_id']
        if 'message' in ajax_data.keys():
            Data['message']     = ajax_data['message']

        logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Add tag", reason=json.dumps(Data))

        # add new record tag
        record = {
            "Data"          :Data, 
            "data_source"   :None, 
            "data_type"     :'tag', 
        }
        up = db_es.bulk_queue_push( [record] , case_id , chunk_size=500) 
        #db_es.es_add_tag(data = { "Data" : Data  , "data_type" : 'tag' } , case_id = case_id )
        if up[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed adding tag", reason=up[1])
            return json.dumps({'result' : 'failed' , 'data': 'Failed adding tag: ' + up[1]})

        # update the tag_id to artifact record
        else:
            
            if record_id is not None and len(up[3]) != 0:
 
                # for each successful tag added
                for tag_id in up[3]: 
                    update_field = db_es.update_field( {'doc': {'tag_id' : tag_id , 'tag_type' : record['Data']['tag_type'] }}  , record_id , case_id)
                    
                    if update_field[0] == False:
                        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed adding tag_id to artifact record", reason=update_field[1])
                        return json.dumps({'result' : 'failed' , 'data': 'Failed adding tag_id to artifact record: ' + update_field[1]})

                logger.logger(level=logger.INFO , type="case", message="Case["+case_id+"]: Tag created")
                return json.dumps({"result" : 'successful' , 'tag_id' : up[3][0] , 'tag_type' : record['Data']['tag_type']})
            return json.dumps({"result" : 'successful' , 'tag_id' : up[3][0] , 'tag_type' : record['Data']['tag_type']})

 

# ================================ generate timeline
# get all tags for the case via ajax
@app.route('/case/<case_id>/timeline_build_ajax', methods=['GET'])
def case_timeline_build_ajax(case_id):
    if request.method == "GET":
        try:
            # create case timeline folder if not exists  
            dest_timeline_folder = os.path.join( app.config['TIMELINE_FOLDER'] , case_id)
            if not os.path.isdir(dest_timeline_folder):
                create_folders(dest_timeline_folder)

            # get if there is a previous version already exists for the case
            src_filename        = 'timeline.xlsx'
            dest_filename       = src_filename.rstrip(".xlsx") + "_v0.xlsx"

            # get the latest timetime version
            latest_version = 0
            for previous_file in os.listdir(dest_timeline_folder): 
                try:
                    if os.path.isfile(os.path.join(dest_timeline_folder, previous_file)) and previous_file.endswith(".xlsx"):    
                        latest_version      = int(previous_file.split("_v")[1].rstrip(".xlsx")) if int(previous_file.split("_v")[1].rstrip(".xlsx")) > latest_version else latest_version
                except Exception as e:
                    pass 

            

            # create instance for timeline builder          
            views_folder        = app.config['TIMELINE_VIEWS_FOLDER']   
            new_version         = latest_version + 1
            dest_filename       = src_filename.rstrip(".xlsx") + "_v"+str(new_version)+".xlsx"
            src_filename        = src_filename.rstrip(".xlsx") + "_v"+str(latest_version)+".xlsx" if latest_version > 0 else src_filename
            dest_timeline       = os.path.join( dest_timeline_folder , dest_filename )
            src_timeline        = os.path.join(dest_timeline_folder , src_filename) if latest_version > 0 else os.path.join( app.config['Timeline_Templates'] , src_filename)
            t                   = buildTimeline.BuildTimeline(views_folder=views_folder , fname= src_timeline)
            export_date         = str(datetime.now())


            # get all yaml views from timeline views
            all_rules           = t.get_views(views_folder)
            requests            = []
            sheet_timeline      ="Timeline"  
            sheet_kuiper_id_col ="KuiperID"


            all_active_rules    = []
            default_rule        = None 

            for rule in range( 0 , len(all_rules)):
                if 'default' in all_rules[rule]['condition'].keys() and all_rules[rule]['condition']['default'] == True:
                    default_rule = all_rules[rule]
                    continue
                if 'active' in all_rules[rule]['condition'].keys() and all_rules[rule]['condition']['active'] == False:
                    continue
                all_active_rules.append(all_rules[rule])  


            for rule in range( 0 , len(all_active_rules)):
                requests.append({
                        "query":{
                            "query_string":{
                                "query" : "tag_id:* AND (" + all_active_rules[rule]["condition"]["query"] + ")",
                                "default_field": "catch_all"
                            }
                        },
                        "size": 2000
                })
            
            requests.append({
                "query":{
                    "query_string":{
                        "query" : "tag_id:*",
                        "default_field": "catch_all"
                    }
                },
                "size": 2000 
            })
            if len(requests):
                res = db_es.multiqueries(case_id, requests)
            else:
                res = [True, []] # if there is no rules

            if res[0] == False:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting timeline generator search", reason=res[1])
                return json.dumps({ 'result' : 'failed' , "message" : res[1]})

            # this list contains the ID of already added records to the sheet, so in the default records will not be added
            added_records           = []
            old_records             = t.get_values_by_column(sheet_timeline , sheet_kuiper_id_col)
            to_be_removed_records   = []



            for r in range(0 , len(res[1])):
                if r < len(res[1])-1:
                    
                    # if the results belongs to a search query
                    for data in res[1][r]['hits']['hits']: 
                        if data['_id'] in old_records:
                            added_records.append(data['_id'])
                        if data['_id'] in added_records: continue 
                        # add extra data related to the record itself
                        data['_source']['_id']              = data['_id']
                        data['_source']['_Export_Version']  = "V_" + str(new_version)
                        data['_source']['_Export_Date']     = export_date 

 
                        fields_data = t.merge_data_and_fields(fields = all_active_rules[r]['fields'].copy(), data= data['_source'])
                        add_res = t.add_data_to_sheet(sheet_timeline, fields_data)
                        if add_res[0]:
                            added_records.append(data['_id']) 
                        else:    
                            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed adding the record ["+data['_id']+"] to xlsx timeline", reason=add_res[1])
                elif default_rule is not None:
                    # if the results does not belongs to a search query 
                    for data in res[1][r]['hits']['hits']:
                        if data['_id'] in old_records:
                            added_records.append(data['_id'])
                        if data['_id'] in added_records: continue
                        
                        # add extra data related to the record itself
                        data['_source']['_id'] = data['_id'] 
                        data['_source']['_Export_Version']  = "V_" + str(new_version)
                        data['_source']['_Export_Date']     = export_date
                        
                        fields_data = t.merge_data_and_fields(fields = default_rule['fields'].copy(), data= data['_source'])
                        t.add_data_to_sheet(sheet_timeline, fields_data) 
            
            # if there is a record on the old version of timeline has been untagged, remove it from the timeline new version
            for r in old_records:
                if r not in added_records:
                    to_be_removed_records.append(r)
            
            for record in to_be_removed_records:
                if not t.delete_row_from_sheet_by_kuiperID(sheet_timeline , record):
                    logger.logger(level=logger.WARNING , type="case", message="Case["+case_id+"]: Failed deleting the record ["+record+"]", reason="")
                    
  
            t.save(dest_timeline)
             
            return send_file(dest_timeline, as_attachment=True) 

        except Exception as e: 
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed retriving timeline", reason=str(e))
            return json.dumps( {'result': 'failed' , 'message' : "Failed retriving timeline: " + str(e)} )

    else:
        return redirect(url_for('home_page'))

 

# =================== Alerts =======================


# ================================ get all alerts for case
@app.route('/case/<case_id>/alerts', methods=['GET'])
def case_alerts(case_id):
    logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Open alerts page")


    CASE_FIELDS = get_CASE_FIELDS()
    if CASE_FIELDS[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting parsers important fields", reason=CASE_FIELDS[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting parsers important fields<br />" + CASE_FIELDS[1])
            

    case = db_cases.get_case_by_id(case_id)
    if case[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason=case[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting case information<br />" + case[1])
    

    if case[1] is None:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason='Index not found')
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Case["+case_id+"]: Failed getting case information<br />Index not found")


    all_rules = db_rules.get_rules()
    if all_rules[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting rules information", reason=all_rules[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=all_rules[1])


    requests = []
    
    for rule in all_rules[1]:
        requests.append({
                "query":{
                    "query_string":{
                        "query" : rule['rule'],
                        "default_field": "catch_all"
                    }
                },
                "size":0
        })
    
    
    if len(requests):
        res = db_es.multiqueries(case_id, requests)
    else:
        res = [True, []] # if there is no rules

    if res[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting total hits of rules from database", reason=res[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=res[1])

    for r in range(0 , len(res[1])):
        all_rules[1][r]['hits'] =  res[1][r]['hits']['total']['value']
    
    # build the query to get all rhaegal hits
    
    
    logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: get Rhaegal hits")
    Rhaegal_query = {
                "query":{
                    "query_string":{
                        "query" : "Data.rhaegal.name:*",
                        "default_field": "catch_all"
                    }
                },
                "size":0,
                "aggs" : {
                        "rhaegal": {
                            "terms" : {
                                "field" : "Data.rhaegal.score.keyword",
                                "size" : 100,
                                "order": {
                                    "_key": "asc"
                                }
                            },
                            "aggs" :{
                                "names" : {
                                    "terms" : {
                                        "field" : "Data.rhaegal.name.keyword",
                                        "size" : 2000,
                                    },
                                    "aggs" : {
                                        "first_record" : {
                                            "top_hits" : {
                                                "size" : 1
                                            },
                                        }
                                    }
                                }
                            }
                        }
                    }
        }

    res = db_es.query(case_id , Rhaegal_query)
    if res[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting the Rhaegal hits", reason=res[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=res[1])


    Rhaegal_hits = {
        "names" : [] , 
        "scores" : []
    }
    for score in res[1]["aggregations"]["rhaegal"]["buckets"]:
        Rhaegal_hits["scores"].append({
            "score" : score["key"],
            "count" : score["doc_count"]
        })
        
        for name in score["names"]["buckets"]:
            tmp_meta = name["first_record"]["hits"]["hits"][0]["_source"]["Data"]["rhaegal"]
            tmp_meta["count"] = name["doc_count"]
            Rhaegal_hits["names"].append(tmp_meta)

    logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: hits ["+str(len(Rhaegal_hits["names"]))+"]")

    return render_template('case/alerts.html',case_details=case[1] ,SIDEBAR=SIDEBAR , all_rules= all_rules[1] , rhaegal_hits=Rhaegal_hits)



# =================== Graph =======================


# ================================ show the graph page
@app.route('/case/<case_id>/graph/<record_id>')
def graph_display(case_id , record_id):
    logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Open graph for record ["+record_id+"]")

    CASE_FIELDS = get_CASE_FIELDS()
    if CASE_FIELDS[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting parsers important fields", reason=CASE_FIELDS[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Failed getting parsers important fields<br />" + CASE_FIELDS[1])
       

    case = db_cases.get_case_by_id(case_id)
    if case[0] == False:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case details", reason=case[1])
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message=case[1])

    if case[1] is None:
        logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting case information", reason='Index not found')
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS[1] , message="Case["+case_id+"]: Failed getting case information<br />Index not found")



    record = []
    if record_id is not None:
        query = {
            "query": {
                "terms": {
                    "_id": [record_id]
                }
            }
        }

        record = db_es.query( case_id, query )
        if record[0] == False:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting record information for graph", reason=record[1])
            return {'result' : False , 'data' : record[1]}
        record = record[1]['hits']['hits']
    
    return render_template('case/graph.html',case_details=case[1] , SIDEBAR=SIDEBAR, init_records = record , page_header="Graph")





# ================================ expand the graph nodes (search)
# retrive requested nodes to be added to the graph
@app.route('/case/<case_id>/expand_graph', methods=["POST"])
def graph_expand(case_id):
    if request.method == "POST":


        ajax_str =  urllib.unquote(request.data).decode('utf8')
        ajax_data = json.loads(ajax_str)['data']
        field = ajax_data['field']
        value = ajax_data['value']
        logger.logger(level=logger.DEBUG , type="case", message="Case["+case_id+"]: Expand search ["+field+":"+value+"]")



        special_chars = [ '\\' , '/' , ':' , '-' , '{' , '}' , '(', ')' , ' ' , '@' ]
        for sc in special_chars:
            value = value.replace(sc , '\\' + sc)

        body = {
            "query": {
                "query_string":{
                        "query" : "*" + str(value) + "*",
                        "default_field" : "catch_all"
                    }
            },
            "size": 500
        }

        try:
            res = db_es.query( case_id, body )
            if res[0] == False:
                logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting record information for graph", reason=res[1])
                ajax_res = {'response' : 'error' , 'data' : str(res[1])}

            res_total = res[1]['hits']['total']['value']
            res_records = res[1]['hits']['hits']
            ajax_res = {'response' : 'OK' , "res_total" : res_total , "res_records" : res_records}
        except Exception as e:
            logger.logger(level=logger.ERROR , type="case", message="Case["+case_id+"]: Failed getting record information for graph", reason=str(e))
            ajax_res = {'response' : 'error'}
            


        return json.dumps(ajax_res)
    else:
        return redirect(url_for('home_page'))
