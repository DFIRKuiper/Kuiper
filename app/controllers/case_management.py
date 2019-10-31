#/usr/bin/env python2
# -*- coding: utf-8 -*-

import json
import os
import urllib
import shutil
import yaml 
import zipfile
import hashlib

from flask import Flask
from flask import request, redirect, render_template, url_for, flash
from flask import jsonify

from app import app

import parser_management

from app.database.dbstuff import *
from app.database.elkdb import *

from werkzeug.utils import secure_filename
from bson import json_util
from bson.json_util import dumps


# get configuration
y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )

SIDEBAR = {
    "sidebar"   : y['case_sidebar'],
    "open"      : app.config['SIDEBAR_OPEN']
}

RemoveRawFiles = y['Kuiper']['RemoveRawFiles'] # remove the uploaded raw files after unzip it to the machine files

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
            return [False , "Folder ["+path+"] already exists" ]
        else:
            return [False , str(e) ]

# ================================ remove folder
def remove_folder(path):
    try:
        shutil.rmtree(path)
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
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# ================================ unzip file
# unzip the provided file to the dst_path
def unzip_file(zip_path,dst_path):
    try:
        create_folders(dst_path)
        with zipfile.ZipFile(zip_path , 'r') as zfile:
            for name in zfile.namelist():
                p_encoded = (dst_path + name).encode('utf-8')
                if name.endswith('/'):
                    create_folders(p_encoded)
                    continue
                with zfile.open(name) as file:
                    f = open((dst_path + name).encode('utf-8'), 'w')
                    f.write(file.read())
                    f.close()
            return [True , "All files of ["+zip_path+"] extracted to ["+dst_path+"]"]
        
        
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
        return zip_content
    except Exception as e:
        print "Error: " + str(e)


# ================================ json beautifier
# return json in a beautifier
def json_beautifier(js):
    return json.dumps(js, indent=4, sort_keys=True)


# ================================ get important fields
# return json of all parsers and the important fields (field , json path)
def get_CASE_FIELDS():
    parsers_details = db_parsers.get_parser()
    case_fields = {}
    for p in parsers_details:
        case_fields[ p['name'] ] = []
        if 'important_field' in p.keys():
            for f in p['important_field']:
                case_fields[ p['name'] ].append( [ f['name'] , "_source.Data." + f['path'] ] )
    return case_fields



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

    # get rules information
    all_rules = db_rules.get_rules()
    if all_rules[0] == False:
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message=all_rules[0])


    alerts = {
        "Critical" : 0,
        "High" : 0,
        "Medium" : 0,
        "Low" : 0,
        "Whitelist" : 0
    }

    # for each rule get total count of each rule and increament the severity of it
    for rule in all_rules[1]:
        body = {
                "query":{
                    "query_string":{
                        "query" : rule['rule']
                    }
                },
                "size":0
        }
        res = db_es.query( case_id, body )
        if res['result'] == False:
            print res['data']
            continue

        alerts[rule['rule_severity']] += res['data']['hits']['total']


    # get machines information
    machines = db_cases.get_machines(case_id)

    # dashboard info to be pushed
    dashboard_info = {
        'alerts' : alerts,
        'machines' : machines
    }


    return render_template('case/dashboard.html',case_details=case ,SIDEBAR=SIDEBAR , dashboard_info=dashboard_info)



# =================== Machines =======================

# ================================ list machines
# list all machines in the case
@app.route("/case/<case_id>")
def all_machines(case_id):

    # check messages or errors 
    message = None if 'message' not in request.args else request.args['message']
    err_msg = None if 'err_msg' not in request.args else request.args['err_msg']

    machines = db_cases.get_machines(case_id)
    case = db_cases.get_case_by_id(case_id)
    parsers_details = db_parsers.get_parser()

    return render_template('case/machines.html',case_details=case , all_machines=machines,SIDEBAR=SIDEBAR ,parsers_details =parsers_details , message = message , err_msg=err_msg)

# ================================ get processing progress
@app.route("/case/<case_id>/<machine_id>/progress")
def all_machines_progress(case_id , machine_id):
    machines = db_files.get_parsing_progress(machine_id)
    if machines[0]:
        return json.dumps(machines[1])
    else:
        return redirect(url_for('all_machines',case_id=case_id , err_msg=machine[1]))


# ================================ machine files status 
# this will list all files and their parser and show their status (done, parsing, pending, etc)
@app.route("/case/<case_id>/machine_files/<machine_id>" , methods=['GET'])
def case_machine_files_status(case_id , machine_id):
    # upload machine page
    if request.method == 'GET':

        case = db_cases.get_case_by_id(case_id)
        CASE_FIELDS = get_CASE_FIELDS()

        # if there is no case exist
        if case is None:
            print "[-] Error: ["+case_id+"] not exists"
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message="Case not found")

        # get files
        files = db_files.get_by_machine(machine_id)
        
        machine_files_status = []
        if files[0]:
            
            for f in files[1]['files']:
                for p in f['parsers']:
                    message = p['message'] if 'message' in p.keys() else ''
                    badge_class = {
                        'pending'   : 'bg-red' if message != '' else 'bg-gray',
                        'done'      : 'bg-green',
                        'parsing'   : 'bg-light-blue'
                    }
                    badge = 'bg-gray'
                    if p['status'] in badge_class.keys(): badge = badge_class[p['status']]

                    status = '<span class="badge badge-pill '+badge+'" style="padding:5px">'+p['status']+'</span>'
                    machine_files_status.append([ f['file_path'] ,str(f['file_size'])+"B" , p['parser_name'] , status , p['start_time'].split('.')[0] , message ])

        return render_template('case/machine_file_status.html',case_details=case ,SIDEBAR=SIDEBAR, machine_id=machine_id , db_files=files[1]['files'] )




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
        if case is None:
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message="Error: "+case_id+" Case not found")
        
        disable = True
        if ajax_data['action'] == 'enable':
            disable = False
        up = db_files.disable_enable_file(machine_id , ajax_data['path'] , ajax_data['parser'] , disable)
        
        if up[0]:
            ajax_data['result'] = True 
        else:
            ajax_data['result'] = False
            
        return jsonify(ajax_data)


# ================================ Upload machines
# upload machine page to upload files to the artifacts file upload,
# this is the page allow to upload multiple zip file, each considered as machine
@app.route("/case/<case_id>/upload_machine" , methods=['POST' , 'GET'])
def case_upload_machine(case_id):
    # upload machine page
    if request.method == 'GET':

        case = db_cases.get_case_by_id(case_id)
        CASE_FIELDS = get_CASE_FIELDS()
        if case is None:
            print "[-] Error: ["+case_id+"] not exists"
            return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message="There is no parsed artifacts, please upload and parse some artifacts to show this page")


        return render_template('case/upload_machines.html',case_details=case ,SIDEBAR=SIDEBAR )

    # upload the machine files ajax
    elif request.method == 'POST':
        # get file
        file = request.files['files[]']
        # if there is a file to upload
        if file:
            
            filename        = secure_filename(file.filename)
            file_name       = str(datetime.now() ).split('.')[0].replace(' ' , 'T') + "-" + filename
            machine_name    = filename.rstrip('.zip')
            machine_id      = case_id + "_" + machine_name
            
            # check if machine already exists
            if db_cases.get_machine_by_id(machine_id) is not None:
                return jsonify({'result' : False , 'filename' : filename , 'message' : 'Machine already exists'})
            

            # create the machine folder in files folder
            files_folder = app.config["UPLOADED_FILES_DEST"] + "/" + case_id + "/" + machine_id + "/"
            raw_folder = app.config["UPLOADED_FILES_DEST_RAW"] + "/" + case_id + "/" + machine_id + "/"
                
            create_folders( files_folder )  # create the folder for the case in files if not exists
            create_folders( raw_folder )    # create the folder for the case in raw folder if not exists
            
            # save the file to the raw data
            file.save(raw_folder + file_name)   

            zip_file_list = []  # contain the zip file list content
            
            # unzip the file to machine files
            try:
                unzip_fun = unzip_file(raw_folder + file_name ,  files_folder + file_name + "/")
                
                if unzip_fun[0] == True:
                    
                    zip_file_list = list_zip_file(raw_folder + file_name)
                    
                    if RemoveRawFiles:
                        remove_file(raw_folder + file_name) # remove the raw file

                else:
                    remove_file(raw_folder +  file_name) # remove file if exists
                    remove_folder(files_folder + file_name + "/") # remove file if exists
                    return jsonify({'result' : False , 'filename' : filename , 'message' : unzip_fun[1]})
            
            # if unzip failed
            except Exception as e:
                if 'password required' in str(e):
                    return jsonify({'result' : False , 'filename' : filename , 'message' : 'File require password'})
                else:
                    return jsonify({'result' : False , 'filename' : filename , 'message' : 'Failed to unzip the file'})

            f = {
                'name': filename,
                'zip_content' : zip_file_list
            }
            machine_details = {
                'main_case' : case_id,
                'machinename' : machine_name
            }
            
            create_m = db_cases.add_machine(machine_details)
            if create_m[0] == False:
                remove_file(raw_folder +  file_name) # remove file if exists
                remove_folder(files_folder + file_name + "/") # remove file if exists
                return jsonify({'result' : False , 'filename' : filename , 'message' : create_m[1]}) 
            return jsonify({'result': True , 'filename' : filename, 'data': f})


        return json.dumps({'result' : False , 'filename' : filename , 'message' : 'There is no file selected'})


# ================================ Upload Artifacts
# upload artifacts for specific machine
@app.route('/case/<main_case_id>/uploadartifacts/<machine_case_id>', methods=['GET', 'POST'])
def main_upload_artifacts(main_case_id,machine_case_id):
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']

        # if there is no file selected, return error
        if request.files['file'].filename == '':
            return jsonify({'results':'error' , 'data' : 'No file has been selected'})

        files_folder = app.config["UPLOADED_FILES_DEST"] + "/" + main_case_id + "/" + machine_case_id + "/"
        raw_folder = app.config["UPLOADED_FILES_DEST_RAW"] + "/" + main_case_id + "/" + machine_case_id + "/"
        
        
        create_folders( files_folder )  # create the folder for the case in files if not exists
        create_folders( raw_folder )    # create the folder for the case in raw folder if not exists
        
        # save the file to raw folder
        file_name       = str(datetime.now() ).split('.')[0].replace(' ' , 'T') + "-" + secure_filename(file.filename)
        file_content    = file.read()
        file_hash       = hashlib.md5(file_content).hexdigest() 

        # get hash values for all files for this machine
        exists_files = []
        for (dirpath, dirnames, filenames) in os.walk(raw_folder):
            for f in filenames:
                exists_files.append( [ f , md5(dirpath + f) ] )
        
        # check if file exists by hash
        for i in exists_files:
            if file_hash == i[1]:
                return jsonify({'results':'error' , 'data' : 'The following two files has same MD5 hash<br > - Uploaded: ' + file_name + '<br > - Exists: '+i[0]})

        # save the file to raw folder
        f = open(raw_folder +  file_name , 'wb')
        f.write(file_content)
        f.close()
        
        # unzip the file if it is zip file, else juwst copy the files to machine folder
        if file_name.endswith(".zip"):
            unzip_fun = unzip_file(raw_folder + file_name ,  files_folder + file_name + "/" )
            if unzip_fun[0] == True:
                files = list_zip_file(raw_folder + file_name)
                
                if RemoveRawFiles:
                        remove_file(raw_folder + file_name) # remove the raw file
            else:
                remove_file(raw_folder +  file_name) # remove file if exists
                remove_folder(files_folder + file_name + "/") # remove file if exists
                return jsonify({'results':'error' , 'data' : unzip_fun[1]})
        else:
            shutil.copy(raw_folder + file_name, files_folder + file_name)  
            files = [file_name]

        for f in range(0 , len(files) ):
            files[f] = main_case_id + "/" + machine_case_id + "/" + files[f]
        return jsonify({'data':files})



# ================================ add machine
# add a machine to the case
@app.route("/case/<case_id>/add_machine/" , methods=['POST','GET'])
def add_machine(case_id):
    if request.method == 'POST':
        machine_details = {
            'machinename':request.form['machinename'],
            'main_case':case_id,
            'ip':request.form['ip'],

        }

        machine = db_cases.add_machine(machine_details)
        if machine[0]:
            return redirect(url_for('all_machines',case_id=case_id , message= "Machine [" + machine[1].lstrip(case_id + "_") + "] created"))
        else:
            return redirect(url_for('all_machines',case_id=case_id , err_msg=machine[1]))


    else:
        return redirect(url_for('home_page'))

# ================================ delete machine
# delete machine from case
@app.route("/case/<case_id>/delete_machine/<machines_list>" , methods=['GET'])
def delete_machine(case_id , machines_list):
    if request.method == 'GET':
        print machines_list

        # delete machine from mongo db
        for machine in machines_list.split(','):
            db_machine = db_cases.delete_machine(machine)
            
            # delete machines records from elasticsearch
            q = {"query": {
                    "query_string": {
                        "query": "(machine.keyword:\""+machine.replace('-' , '\\-')+"\")"
                    }
                }
            } 
            es_machine = db_es.del_record_by_query(case_id , q)
            if es_machine:
                print "[+] Machine ["+machine+"] records removed"

        # delete all records for the machines
        
        return redirect(url_for('all_machines',case_id=case_id))



# ================================ process artifacts
# run the selected parser for the machines specified
@app.route('/case/<main_case_id>/processartifacts/<machine_case_id>/<parser_name>', methods=['GET'])
def main_process_artifacts(main_case_id,machine_case_id,parser_name):
    parsers = parser_name.split(',')

    task = parser_management.run_parserss.apply_async((main_case_id,machine_case_id,parsers))
    
    return jsonify({'data': 'started processing'})


# =================== Artifacts =======================


# ================================ get artifacts data types
# get all the list of artifacts for this case
@app.route('/case/<case_id>/browse_artifacts_list_ajax', methods=['POST'])
def browse_artifacts_list_ajax(case_id):

    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        print ajax_str
        ajax_data = json.loads(ajax_str)['data']
        print ajax_data['query']

        body = {
            "query":{
                "query_string":{
                    "query" : ajax_data['query']
                }
            },
            "aggs":{
                  "data_type": {
                      "terms" : {
                          "field" : "data_type.keyword",
                          "size" : 500
                      }

                  }
              },

            "size":0
        }

        res = db_es.query( case_id, body )
        if res['result'] == False:
            return json.dumps( {'res' : res['data']} )


        res = res['data']["aggregations"]["data_type"]["buckets"]
        print res


        return json.dumps({'res' : res})


# ================================ get artifacts records ajax
# retrive all artifacts records using ajax
@app.route('/case/<case_id>/browse_artifacts_ajax', methods=["POST"])
def case_browse_artifacts_ajax(case_id):
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        ajax_data = json.loads(ajax_str)['data']
        body = {
            "from": int(ajax_data["wanted_page"]) * 30,
            "size":30,

        }
        if ajax_data['query'] != "None":
            body["query"] = {
                "query_string" : {
                    "query" : ajax_data['query']
                }
            }

        if ajax_data['sort_by'] != "None":
            order = "asc" if ajax_data['sort_by']['order'] == 0 else "desc"
            body["sort"] = {
                ajax_data['sort_by']['name'] : {"order" : order}
            }

        res = db_es.query( case_id, body )

        if res['result'] == False:
            return json.dumps( {'res_total' : 0 , "res_records" : res['data']} )

        res_records = res['data']['hits']['hits']
        res_total = res['data']['hits']['total']
        for i in range( 0  , len(res_records) ):
            if "machine" in res_records[i]['_source'].keys():
                machine = db_cases.get_machine_by_id(res_records[i]['_source']['machine'])
                if machine is not None:
                    res_records[i]['_source']['machinename'] = machine['machinename']

        ajax_res = {"res_total" : res_total , "res_records" : res_records}

        return json.dumps(ajax_res)


# ================================ get artifacts data types
# get all artifacts for case
@app.route('/case/<case_id>/browse_artifacts', methods=['GET'])
def case_browse_artifacts(case_id):
    case = db_cases.get_case_by_id(case_id)

    
    CASE_FIELDS = get_CASE_FIELDS()

    # get all fields from elasticsearch
    # used for advanced search to list all fields when searching
    try:
        fields_mapping = db_es.get_mapping_fields(case_id)
    except Exception as exc:
        print "[-] Error: ["+case_id+"] - " + str(exc)
        return render_template('case/error_page.html',case_details=case ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message="There is no parsed artifacts, please upload and parse some artifacts to show this page")
    
    query = {
            "AND" : []
            }

    # check if the channel exists add it to the query
    if 'machine' in request.args:
        query["AND"].append({'machine' : request.args['machine']})

    if 'rule' in request.args:
        query['AND'].append({'rule' : request.args['rule']})

    # get all rules
    all_rules = db_rules.get_rules()
    if all_rules[0] == False:
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message=all_rules[0])


    q = json.dumps(query)
    return render_template('case/browse_artifacts.html',case_details=case ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , search_query = q , fields_mapping=fields_mapping , rules = all_rules[1])






# =================== Timeline =======================

# ================================ timeline page
# get the time line page
@app.route('/case/<case_id>/timeline', methods=['GET'])
def case_timeline(case_id):
    case = db_cases.get_case_by_id(case_id)
    
    CASE_FIELDS = get_CASE_FIELDS()

    if case is None:
        print "[-] Error: ["+case_id+"] not exists"
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message="There is no parsed artifacts, please upload and parse some artifacts to show this page")

    return render_template('case/timeline.html',case_details=case ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS )


# ================================ get tags ajax
# get all tags for the case via ajax
@app.route('/case/<case_id>/timeline_ajax', methods=['POST'])
def case_timeline_ajax(case_id ):
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        ajax_data = json.loads(ajax_str)['data']


        body = {
            "query": {
                "query_string" : {
                    "query" : 'data_type:"tag"'
                }
            },
            "sort":{
                "Data.@timestamp" : {"order" : "asc"}
            },
            "size": 200
        }
        res = db_es.query( case_id, body )

        if res['result'] == False:
            return json.dumps( {'tags' : res['data']} )


        #print res
        total_tags = res['data']['hits']['total']
        tags =  res['data']['hits']['hits']


        for t in range(0 , len(tags)):
            if 'record_id' in tags[t]['_source']['Data'].keys():
                record_id = tags[t]['_source']['Data']['record_id']
                rec = db_es.get_record_by_id(case_id , record_id)
                if rec != False:
                    tags[t]['_source']['Data']['record_details'] = rec


        return json.dumps({"tags" : tags})


# ================================ delete tag ajax
# delete a specific tag by its ID
@app.route('/case/<case_id>/timeline_delete_tag_ajax', methods=['POST'])
def case_timeline_delete_tag(case_id ):
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        print ajax_str
        ajax_data = json.loads(ajax_str)['data']

        tag_id =  ajax_data['tag_id']
        record_id = ajax_data['record_id']
        print record_id
        print tag_id

        delete = db_es.del_record_by_id( case_id = case_id , record_id = tag_id)
        print delete
        if(delete):

            if record_id is not None:
                if not db_es.update_field( {"script": "ctx._source.remove(\"tag_id\")"}  , record_id , case_id):
                    return json.dumps({"result" : 'failed1'})

            return json.dumps({"result" : 'successful'})
        else:
            return json.dumps({"result" : 'failed'})

# ================================ add tag ajax
# add tag to a specifc record
@app.route('/case/<case_id>/add_tag_ajax', methods=["POST"])
def case_add_tag_ajax(case_id):
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        record_id = None
        ajax_data = json.loads(ajax_str)['data']
        Data = {
            "tag" : ajax_data['time'] ,
            "@timestamp" : ajax_data['time']
        }

        if 'doc_id' in ajax_data.keys():
            Data['record_id']   = ajax_data['doc_id']
            record_id           = ajax_data['doc_id']
        if 'message' in ajax_data.keys():
            Data['message']     = ajax_data['message']

        up = db_es.es_add_tag(data = { "Data" : Data  , "data_type" : 'tag' } , case_id = case_id )
        #up = db_es.update_field(tag ={"tag" : ajax_data["tag"]} , doc_id = ajax_data["doc_id"], indx=case_id)
        if up['_shards']['successful'] == True:
            if record_id is not None:
                if db_es.update_field( {'doc': {'tag_id' : up['_id'] }}  , record_id , case_id):
                    return json.dumps({"result" : 'successful'})
                else:
                    return json.dumps({'result' : 'created'})
            else:
                #return redirect(url_for('case_timeline' , case_id = case_id))
                return json.dumps({"result" : 'successful' , 'id' : up['_id']})
        else:
            return json.dumps({"result" : 'failed'})



# =================== Alerts =======================


# ================================ get all artifacts for case
@app.route('/case/<case_id>/alerts', methods=['GET'])
def case_alerts(case_id):
    case = db_cases.get_case_by_id(case_id)
    CASE_FIELDS = get_CASE_FIELDS()


    if case is None:
        print "[-] Error: ["+case_id+"] - No index "
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message="There is no parsed artifacts, please upload and parse some artifacts to show this page")


    all_rules = db_rules.get_rules()
    if all_rules[0] == False:
        return render_template('case/error_page.html',case_details=case_id ,SIDEBAR=SIDEBAR , CASE_FIELDS=CASE_FIELDS , message=all_rules[0])

    for rule in all_rules[1]:
        body = {
                "query":{
                    "query_string":{
                        "query" : rule['rule']
                    }
                },
                "size":0
        }

        res = db_es.query( case_id, body )
        if res['result'] == False:
            print res['data']

        rule['hits'] = res['data']['hits']['total']



    return render_template('case/alerts.html',case_details=case ,SIDEBAR=SIDEBAR , all_rules= all_rules[1] )



# =================== Graph =======================


# ================================ show the graph page
@app.route('/case/<case_id>/graph/<record_id>')
def graph_display(case_id , record_id):
    case = db_cases.get_case_by_id(case_id)
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
        print json_beautifier( record )
        if record['result'] == False:
            print record['data']
            return {'result' : False , 'data' : record['data']}
        record = record['data']['hits']['hits']

    return render_template('case/graph.html',SIDEBAR=SIDEBAR,case_details=case , init_records = record , page_header="Graph")





# ================================ expand the graph nodes (search)
# retrive requested nodes to be added to the graph
@app.route('/case/<case_id>/expand_graph', methods=["POST"])
def graph_expand(case_id):
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        print ajax_str
        ajax_data = json.loads(ajax_str)['data']
        field = ajax_data['field']
        value = ajax_data['value']

        special_chars = [ '\\' , '/' , ':' , '-' , '{' , '}' , '(', ')' , ' ' , '@' ]
        for sc in special_chars:
            value = value.replace(sc , '\\' + sc)

        body = {
            "query": {
                "query_string":{
                        "query" : '"' + str(value) + '"'
                    }
            },
            "size": 500
        }

        print json_beautifier( body)
        try:
            res = db_es.query( case_id, body )
            if res['result'] == False:
                print "[-] Error: "  + str(res['data'])
                ajax_res = {'response' : 'error' , 'data' : str(res['data'])}

            res_total = res['data']['hits']['total']
            res_records = res['data']['hits']['hits']
            ajax_res = {'response' : 'OK' , "res_total" : res_total , "res_records" : res_records}
        except:
            ajax_res = {'response' : 'error'}
            pass



        return json.dumps(ajax_res)
