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


import case_management





# retrive all artifacts records using ajax
@app.route('/api/get_artifacts', methods=["POST"])
def api_get_artifacts():
    if request.method == "POST":

        request_str =  urllib.unquote(request.data).decode('utf8')
        request_json = json.loads(request_str)['data']
        case_id = request_json['case_id']

        logger.logger(level=logger.DEBUG , type="api", message="Case["+case_id+"]: get artifacts request", reason=json.dumps(request_json))

        # == from - to
        body = {
                "from": request_json['seq_num'] * request_json['chunk_size'],
                "size": request_json['chunk_size'],

            }

        # == query
        if request_json['query'] != None:
            request_json['query'] = request_json['query'].strip()
            query = '*' if request_json['query'] == "" or request_json['query'] is None else request_json['query']
            body["query"] = {
                "query_string" : {
                    "query" : '!(data_type:\"tag\") AND ' + query,
                    "default_field" : "catch_all"
                }
            }

        # == sort 
        if request_json['sort_by'] != None:
            order = "asc" if request_json['sort_by']['order'] == 0 else "desc"
            body["sort"] = {request_json['sort_by']['name'] : {"order" : order}}
        else:
            body["sort"] = {'Data.@timestamp' : {"order" : 'asc'}}
        

        # == fields
        if request_json['fields'] != None :
            body['_source'] = {}
            body['_source']['includes'] = request_json['fields'].split(",")
        
        logger.logger(level=logger.DEBUG , type="api", message="Case["+case_id+"]: Query artifacts", reason=json.dumps(body))



        # request the data from elasticsearch
        try:
            res = db_es.query( case_id, body )
        except Exception as e:
            res = [False, str(e)]
        
        if res[0] == False:
            logger.logger(level=logger.ERROR , type="api", message="Case["+case_id+"]: Failed query artifacts from dataabase", reason=res[1])
            return json.dumps({'success' : False  , 'message' : res[1]} )



        return json.dumps({'success': True, 'data': res[1] , 'total': res[1]['hits']['total']['value']})


# retrive all artifacts records using ajax
@app.route('/api/upload_machine/<case_id>', methods=["POST"])
def api_case_upload_machine(case_id):
    # upload the machine files ajax
    if request.method == 'POST':

        # get file
        file = request.files['files']
        # if there is a file to upload
        if file:
            logger.logger(level=logger.DEBUG , type="api", message="Case["+case_id+"]: Upload file to Kuiper", reason="")
            base64_name = None if 'base64_name' not in request.form else request.form['base64_name']
            # start handling uploading the file
            uf = case_management.upload_file(file , case_id , base64_name=base64_name)
            return json.dumps(uf[1])

        return json.dumps({'result' : False , 'filename' : '' , 'message' : 'There is no file selected'})


@app.route('/api/system_health/update', methods=["POST"])
def api_system_health_update():

    if request.method == 'POST':

        request_str =  urllib.unquote(request.data).decode('utf8')
        request_json = json.loads(request_str)['data']
        
        logger.logger(level=logger.DEBUG , type="api", message="System health ["+request_json['service']+"]", reason="")

        with open(os.path.join( app.config['SYSTEM_HEALTH_PATH'] , request_json['service'] ) , 'w' ) as sys_health:
            data = {
                'datetime'  : request_json['datetime'],
                'health'    : request_json['health']
            }
            sys_health.write(json.dumps(data))
        



        return json.dumps({'result' : True, 'message' : 'Done'})