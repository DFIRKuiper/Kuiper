#/usr/bin/env python2


import shutil
import os
import urllib
import importlib
from datetime import datetime
import binascii
import json
from bson import json_util
from bson.json_util import dumps

from flask import Flask
from flask import request, redirect, render_template, url_for, flash
from flask import jsonify

from app.database.dbstuff import *
from app.database.elkdb import *

from app import app

from  app import celery


# =================================================
#               Helper Functions
# =================================================

# ================================ convert fields values to string
# convert all data types (int, float, bool, etc.) to string to be pushed to elasticsearch
# some parsers returns fields in a record as a int, but if not exists return it bool...
def convert_json_fields_to_str(json_data):
    # if list
    if isinstance(json_data , list):
        # convert list to dict
        return { str(v) : convert_json_fields_to_str( json_data[v] ) for v in range( 0 , len(json_data) ) }
    
    # if dict
    elif isinstance(json_data , dict):
        d = {}
        for k , v in json_data.iteritems():
            d[k] = convert_json_fields_to_str(v)
        return d
    
    else:
        return str(json_data).replace('"' , "'") # replace all (") with ('), elasticsearch does not support it

# ================================ Fix values issues 
# convert the data received from the parser to string
# solve other issues with elasticsearch
def fix_issues_with_parsed_data(data):
    if data == None or len(data) == 0:
        return data
    for d in range(0 , len(data)):
        # convert the provided data to string, instead of integers
        data[d] = convert_json_fields_to_str( data[d] )
        #print data[d]

        # if timestamp contain space " " replace it with "T" to meet the ISO format
        if '@timestamp' not in data[d] or data[d]['@timestamp'] is None:
            data[d]['@timestamp'] = '1700-01-01T00:00:00'

        if '@timestamp' in data[d]:
            data[d]['@timestamp'] = data[d]['@timestamp'].replace(' ' , 'T')
        
    return data

# ================================ check if files belong to the parser
# check if the provided file is for the provided parser
def verifiy_file_for_parser(file , parser_details):

    cat_type = parser_details['parser_files_categorization_type']
    cat_values = parser_details['parser_files_categorization_values'].split(',')
    filename = file.split('/')[-1]
    
    try:
        # if file extension
        if cat_type == 'extension':
            for c in cat_values:
                if file.endswith(c):
                    return True

        # if file name match
        elif cat_type == 'file_name':
            if filename in cat_values:
                return True
        
        # if file name starts with
        elif cat_type == 'startswith':
            for c in cat_values:
                if filename.startswith(c):
                    return True

        
        # if file magic number match the value
        elif cat_type == 'magic_number':

            cont = open(file,'rb')
            for v in cat_values:
                conx = cont.read( len(v)/2 )
                header = str(binascii.hexlify(conx))
                header2 = str(v.lower())
                if header == header2:
                    return True


    except Exception as exc:
        print exc
    
    return False

# ================================ check if the file already parsed
# check if the provided file already has been parsed by the provided parser
def is_file_parsed(machine_id , file , parser_name):
    db_file = db_files.get_by_file_path(machine_id , file ) # get file details
    # if file not in DB then not parsed 
    if db_file[0] == False:
        return [False , db_file[1] ]

    # check if the parser_name in the parser list of the file in DB 
    for p in db_file[1]['parsers']:
        if parser_name == p['parser_name'] and p['status'] in ['done','parsing']:
            return [True,  'skip']

    return [False , 'dont skip']


# ================================ check if the parsing for the file is disabled
# check if the file parsing is disabled on this file or not
def is_file_parsing_disabled(machine_id , file , parser_name):
    db_file = db_files.get_by_file_path(machine_id , file ) # get file details
    # if file not in DB then not parsed 
    if db_file[0] == False:
        return [False , db_file[1] ]

    # check if the parser_name in the parser list of the file in DB 
    for p in db_file[1]['parsers']:
        if parser_name == p['parser_name'] and 'disable' in p.keys() and p['disable'] == 'True':
            return [True,  'disabled']

    return [False , 'enabled']


# ================================ get not parsed filse
# this will get all files need to be parsed by the parser (files not parsed and not parsing currently)
def get_files_not_parsed(case_id, machine_id , parser_details):
    files_folder = app.config["UPLOADED_FILES_DEST"] + "/" + case_id + "/" + machine_id + "/"

    print "[+] files_folder: " + files_folder
    files_folder = files_folder.encode('utf-8')
    # get list of all files in the machine folder
    files = []
    for r, d, f in os.walk(files_folder):
        for file in f:
            files.append(os.path.join(r, file))
    

    files_to_be_parsed = [] # list of files that needs to be parsed

    # identify the files for the specified parser_name
    for f in files:
        if verifiy_file_for_parser(f, parser_details):
            
            # === check if the file parsed or not by the parser
            is_parsed = is_file_parsed( machine_id , f , parser_details['name'])
            if is_parsed[0]:
                print "[+] File " + f + " parsed"
                continue
            
            
            # === check if the file parsing disabled on this file
            is_disabled = is_file_parsing_disabled( machine_id , f , parser_details['name'])
            if is_disabled[0]:
                print "[+] File " + f + " parsing disabled"
                continue

            # === add the files as parsing for the provided parser in database
            start_time = str(datetime.now())
            add_file = edit_db_file_status(machine_id, f , parser_details , start_time , "pending" )
            if not add_file[0]:
                print "Error: " + add_file[1]
                continue
            

            files_to_be_parsed.append(f)
    
    print "[+] Parser ["+parser_details['name']+"] will parse ["+str(len(files_to_be_parsed))+"] files"
    return files_to_be_parsed


# ================================ change file status
# change file status (pending, parsing, done, error)
def edit_db_file_status(machine_id , file , parser_details , start_time , status , message ="", end_time=""):
    file_details = {
        "file_path" : file,
        "parsers" : {"parser_name" : parser_details['name'] , "start_time" : start_time , "status" : status , "message" : message },
        "file_size" : os.path.getsize( file )
        }
    add_file = db_files.add_file(machine_id , file_details)
    if add_file[0]:
        return [True, "Changed ["+file+"] for parser ["+parser_details['name']+"] to: " + status]
    else:
        return [ False,  add_file[1]] 

# ================================ call the parser interface function
# return list of files for specific parser
def start_parsing_files(case_id, machine_id, parser_details , files_to_be_parsed):
    
    # import the parser module
    parser_folder = parser_details['parser_folder']
    parser_file = parser_details['interface_function'].split('.')[0]
    parser_func = parser_details['interface_function'].split('.')[1]
    print "[+] Parser Mudole: " + 'app.parsers.' + parser_folder + '.' + parser_file
    parser_module = importlib.import_module('app.parsers.' + parser_folder + '.' + parser_file )

    
    for f in files_to_be_parsed:
        f = f.encode('utf-8')
        print "[+] File ["+f+"] -> " + parser_details['name']

        # === add the files as parsing for the provided parser in database
        start_time = str(datetime.now())
        add_file = edit_db_file_status( machine_id, f , parser_details , start_time , "parsing" )
        if not add_file[0]:
            print "Error: " + add_file[1]
            continue
        
        
        # === call parser to parse the file
        json_res = getattr(parser_module , parser_func)( file=f , parser = parser_details['name'] )
        if isinstance(json_res , tuple) and json_res[0] is None: # if parser failed stop the processing for the parser
            add_file = edit_db_file_status(machine_id, f , parser_details , start_time , "error" , message=json_res[1] )
            if not add_file[0]:
                print "Error: " + add_file[1]
            
            continue

        # === fix data type issue with received data
        json_res = fix_issues_with_parsed_data(json_res)
        # === push result to database 
        pushed = True
        chunks_size = 20000
        if json_res is not None and len(json_res) != 0:
            for i in range( 0 , len(json_res) , chunks_size):
                print parser_details['name']
                p = db_es.bulk_queue_push(json_res[ i : (i+chunks_size) ] ,case_id, source = parser_details['name'] , machine = machine_id , data_type=parser_details['name'] , data_path = f)
                if p[0] == False:
                    pushed = False
                    print "Error: " + str(p[1])
                    add_file = edit_db_file_status(machine_id, f , parser_details , start_time , "error" , message="Error: " + str(e) , end_time=str(datetime.now()) )
                    if not add_file[0]:
                        print "Error: " + add_file[1]
                    break
        
        if not pushed:
            continue
                    

        # === add the file as parsed for the provided parser in database
        add_file = edit_db_file_status(machine_id, f , parser_details , start_time , "done" , message="" , end_time=str(datetime.now()) )
        if not add_file[0]:
            print "Error: " + add_file[1]
            continue

    
    print "[+] Done running all parsers for specified files"

# =================================================
#               Celery Functions
# =================================================
# run parsers  
@celery.task(bind=True)
def run_parserss(self,main_case_id,machine_case_id,parsers_list):
    print "[+] Case: " + main_case_id
    print "[+] Machine: " + machine_case_id
    print "[+] Parsers: " + str(parsers_list)
    
    parser_files_mapping = {}

    for parser_name in parsers_list:

        # === get parser details
        parser_details = db_parsers.get_parser_by_name(parser_name)
        if parser_details[0] == False:
            print '[-] Error: Parser [' + parser_name + '] not found'
            continue
        # === get files will be parsed for the parser
        parser_files_mapping[parser_name] = {
            'parser_details': parser_details[1] , 
            'files_to_be_parsed' : get_files_not_parsed(main_case_id , machine_case_id , parser_details[1]) 
        }

    for parser in parser_files_mapping.keys():
        # === parse the unparsed files
        start_parsing_files(main_case_id , machine_case_id , parser_files_mapping[parser]['parser_details'] , parser_files_mapping[parser]['files_to_be_parsed'])


