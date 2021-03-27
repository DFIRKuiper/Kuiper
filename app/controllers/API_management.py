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







# retrive all artifacts records using ajax
@app.route('/api/get_artifacts/<case_id>', methods=["POST"])
def api_get_artifacts(case_id):
    if request.method == "POST":

        request_str =  urllib.unquote(request.data).decode('utf8')
        request_json = json.loads(request_str)['data']
        logger.logger(level=logger.DEBUG , type="api", message="Case["+case_id+"]: get artifacts request", reason=json.dumps(request_json))

        # == from - to
        body = {
                "from": request_json['seq_num'] * 20000,
                "size":20000,

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
            body['_source'] = request_json['fields'].split(",")
        
        logger.logger(level=logger.DEBUG , type="api", message="Case["+case_id+"]: Query artifacts", reason=json.dumps(body))



        # request the data from elasticsearch
        res = db_es.query( case_id, body )
        if res[0] == False:
            logger.logger(level=logger.ERROR , type="api", message="Case["+case_id+"]: Failed query artifacts from dataabase", reason=res[1])
            return json.dumps({'res_total' : 0 , 'res_records' : [] , 'aggs' : []})



        return json.dumps({'data': res[1] , 'total': res[1]['hits']['total']['value']})

