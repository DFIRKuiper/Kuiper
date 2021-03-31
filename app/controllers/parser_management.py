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
import time
import sys 
import psutil
import random

from flask import Flask
from flask import request, redirect, render_template, url_for, flash
from flask import jsonify

from app.database.dbstuff import *
from app.database.elkdb import *

from app import app

from  app import celery_app

from celery import Task



# ================================ json beautifier
# return json in a beautifier
def json_beautifier(js):
    return json.dumps(js, indent=4, sort_keys=True)



# =================================================
#               Parser Management Class
# =================================================

class Parser_Manager:

    tmp_total_files = 0 # the total number of files to be parsed
    files_parsed    = 0 # number of files already parsed
    files_failed    = 0 # number of files failed
    es_chunks_size  = 20000


    # this initializer used by the task processor
    # if update_state not provided:
    # this initializer used when handling worker errors, which will be used for updating the files status
    def __init__(self, main_case_id , machine_case_id , parsers_list , task_id , update_state=None):
        
        self.case_id        = main_case_id
        self.machine_id     = machine_case_id
        self.parsers_list   = parsers_list
        self.update_state   = update_state
        self.task_id        = task_id

        if update_state is not None:
            self.set_task_state("STARTED")

    



    # this function will trace all files and collect the files that needs to be parsed
    def specify_files_to_be_parser(self):
        try:
            logger.logger(level=logger.DEBUG , type="parser", message="Start parsing: case[" + self.case_id + "] - machine[" + self.machine_id + "] - Parsers["+','.join(self.parsers_list)+"]")
            
            self.parser_files_mapping = {}

            # ==== get files to be parsed for each parser 
            for parser_name in self.parsers_list:

                # === get parser details
                db_parser_details = db_parsers.get_parser_by_name(parser_name)
                if db_parser_details[0] == False:
                    logger.logger(level=logger.ERROR , type="parser", message="Failed getting parser information ["+parser_name+"]" , reason=db_parser_details[1])
                    continue
                elif db_parser_details[0] == True and db_parser_details[1] is None:
                    logger.logger(level=logger.ERROR , type="parser", message="Failed getting parser information ["+parser_name+"]" , reason='Parser not exists')
                    continue
                
                # === get files will be parsed for the parser
                files_list_to_be_parsed = self.get_files_not_parsed(db_parser_details[1]) 

                # if failed getting the files to be parsed then stop the parsing
                if files_list_to_be_parsed == False:
                    raise Exception("Failed collecting the list of files to be parsed")

                self.parser_files_mapping[parser_name] = {
                    'db_parser_details'        : db_parser_details[1] , 
                    'files_list_to_be_parsed'  : files_list_to_be_parsed    
                }
                self.tmp_total_files += len(files_list_to_be_parsed)


            # ==== Get Kjson files
            kjson_details = {
                "name"                                  : 'kjson',
                'parser_files_categorization_type'      : 'extension',
                'parser_files_categorization_values'    : 'kjson'
            }
            files_list_to_be_parsed = self.get_files_not_parsed(kjson_details) 

            # if failed getting the files to be parsed then stop the parsing
            if files_list_to_be_parsed == False:
                raise Exception("Failed collecting the list of files to be parsed")

            self.parser_files_mapping[kjson_details['name']] = {
                'db_parser_details'        : kjson_details , 
                'files_list_to_be_parsed'  : files_list_to_be_parsed    
            }
            self.tmp_total_files += len(files_list_to_be_parsed)


            
            # === set the status of the task
            self.set_task_state("STARTED")
            logger.logger(level=logger.DEBUG , type="parser", message="Files to be parsed ["+str(self.tmp_total_files)+"]")
            return True


        except Exception as e:
            logger.logger(level=logger.ERROR , type="parser", message="Failed getting the files" , reason=str(e))
            return False
    

    # this function will start parsing all the collected files from the specified parsers
    def start_parsing(self):
        try:
            # ===== Start parsing the files
            for parser in self.parser_files_mapping.keys():

                
                parser_details      = self.parser_files_mapping[parser]['db_parser_details']
                parser_name         = self.parser_files_mapping[parser]['db_parser_details']['name']
                files_to_be_parsed  = self.parser_files_mapping[parser]['files_list_to_be_parsed']

                start_time          = str(datetime.now())
                
                # if any parser other than jkson, then collect the parser function information
                if parser_name != 'kjson':
                    parser_folder       = parser_details['parser_folder']
                    parser_file         = parser_details['interface_function'].split('.')[0]
                    parser_func         = parser_details['interface_function'].split('.')[1]
                
                    # import the parser module
                    logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: Parser Mudole [app.parsers." + parser_folder + "." + parser_file + "]")

                    try:
                        parser_module = importlib.import_module('app.parsers.' + parser_folder + '.' + parser_file )
                    except Exception as e:
                        # if failed getting the parser modules, then set all files message
                        self.files_failed += len(files_to_be_parsed)
                        for f in files_to_be_parsed:
                            logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed getting parser module to parse ["+f+"]" , reason=str(e))
                            add_file = self.edit_db_file_status(f , parser_name , start_time , "error" , message=str(e) , end_time=str(datetime.now()) )
                            if not add_file[0]:
                                logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed editing file status ["+f+"] to failed" , reason=add_file[1])
                        
                        continue


                num_files_to_be_parsed  = len(files_to_be_parsed)
                num_files_parsed        = 0
                # loop over the files to parse them one by one 
                while len(files_to_be_parsed):
                    try:
                        # randomly pick on of the files
                        pos         = random.randint(0,len(files_to_be_parsed)-1)
                        f           = str(files_to_be_parsed[pos]).encode('utf-8')
                        file_size   = os.path.getsize( f )
                        if self.wait_memory_free(file_size):
                            logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: Wait to parse file ["+f+"]" , reason="Wait for avaliable memory to start parsing the file")
                            time.sleep(5)
                            continue
                        
                        del files_to_be_parsed[pos]

                        logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: Start parsing the file: " , reason=f)
                        
                        # === add the files as parsing for the provided parser in database
                        start_time = str(datetime.now())
                        add_file = self.edit_db_file_status( f , parser_name , start_time , "parsing" )
                        if not add_file[0]:
                            logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed editing file ["+f+"] status" , reason=add_file[1])
                            continue
                        
                        
                        
                        # === push the results to elasticsearch
                        pushed          = True
                        pushed_records  = 0
                        failed_records  = 0
                        message         = ''
                        
                        # ===== call the parser function and push the results to database
                        if parser_name == 'kjson':
                            # ===== collect and push the kjson file results
                            kjson_records = []
                            with open(f , 'r') as kjson_handle:
                                for rec in kjson_handle:
                                    json_res = json.loads(rec)
                                    kjson_records.append(json_res) 

                                    # if the collect lines match the chunk size, then push the data to elasticsearch
                                    if len(kjson_records) == self.es_chunks_size:
                                        pushing_results = self.fix_and_push_parsed_data(kjson_records , parser_name , f , start_time)
                                        pushed          = pushing_results[0]
                                        pushed_records  += pushing_results[1]
                                        failed_records  += pushing_results[2]
                                        message         = pushing_results[3]

                                        if pushed == False:
                                            break
                                        
                                        kjson_records = []
                                

                                # if there are data not pushed yet, then push it to elasticsearch
                                if len(kjson_records):
                                    pushing_results = self.fix_and_push_parsed_data(kjson_records , parser_name , f , start_time)
                                    pushed          = pushing_results[0]
                                    pushed_records  += pushing_results[1]
                                    failed_records  += pushing_results[2]
                                    message         = pushing_results[3]

                                    if pushed == False:
                                        break

                                    kjson_records = []


                        else:
                            # if used parser, not kjson results

                            # === call parser to parse the file
                            json_res = getattr(parser_module , parser_func)( file=f , parser = parser_name )
                            

                            if isinstance(json_res , tuple) and json_res[0] is None: # if parser failed, continue to next file

                                logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed parsing file ["+f+"]" , reason=json_res[1])


                                add_file = self.edit_db_file_status(f , parser_name , start_time , "error" , message=json_res[1] )
                                if not add_file[0]:
                                    logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed editing file status ["+f+"] to failed" , reason=add_file[1])
                                
                                continue
                            
                            if isinstance(json_res , file):
                                json_res_path = os.path.realpath(json_res.name)
                                while True:
                                    res = getattr(parser_module , parser_func + "_pull")( json_res , self.es_chunks_size )
                                    
                                    # if exception found in the function
                                    if isinstance(res , tuple) and res[0] == False :
                                        pushed  = False 
                                        message = res[1]
                                        break 
                                    
                                    # if there is a results to push
                                    if len(res):
                                        pushing_results =  self.fix_and_push_parsed_data(res , parser_name , f , start_time)
                                        pushed          =  pushing_results[0]
                                        pushed_records  += pushing_results[1]
                                        failed_records  += pushing_results[2]
                                        message         =  pushing_results[3]
                                        if pushed == False:
                                            break
                                    else:
                                        # if there is no more results to push
                                        break


                                # get the real path of the temp file and delete it
                                json_res.close()
                                os.remove(json_res_path)

                            else:
                                pushing_results = self.fix_and_push_parsed_data(json_res , parser_name , f , start_time)
                                pushed          = pushing_results[0]
                                pushed_records  = pushing_results[1]
                                failed_records  = pushing_results[2]
                                message         = pushing_results[3]
                                
                        

                        logger.logger(level=logger.INFO , type="parser", message="Parser["+parser_name+"]: Total pushed records ["+str(pushed_records)+"] and failed ["+str(failed_records)+"]")

                        # === add the file as parsed for the provided parser in database
                        if pushed:
                            add_file = self.edit_db_file_status(f , parser_name , start_time , "done" , message="Pushed ["+str(pushed_records)+"] / Failed ["+str(failed_records)+"]" , end_time=str(datetime.now()) )
                            if not add_file[0]:
                                logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed editing file status ["+f+"] to parsed" , reason=add_file[1])
                                continue

                            self.files_parsed += 1 # this counter for total files parsed from all parsers
                            num_files_parsed  += 1 # this counter for current parser files done 
                            self.update_state("PROCESSING" , self.files_parsed)
                        else:
                            logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed pushing ["+f+"]" , reason=message)
                            add_file = self.edit_db_file_status(f , parser_name , start_time , "error" , message=message + " - pushed rec. " + str(pushed_records) , end_time=str(datetime.now()) )
                            if not add_file[0]:
                                logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed editing file status ["+f+"] to failed" , reason=add_file[1])
                            
                    except Exception as e:
                        add_file = self.edit_db_file_status(f , parser_name , start_time, "error" , message="Failed: " + str(e) , end_time=str(datetime.now()) )
                        if add_file[0] == False:
                            logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: Failed editing file status ["+f+"] to parsed" , reason=add_file[1])
                            continue
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        
                        logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: failed parsing file ["+f+"]" , reason=str(e) + " - Line" + str(exc_tb.tb_lineno))

                self.files_failed += num_files_to_be_parsed - num_files_parsed
                logger.logger(level=logger.INFO , type="parser", message="Parser["+parser_name+"]: Done parsing ["+str(num_files_to_be_parsed)+"], ["+str(num_files_to_be_parsed - num_files_parsed)+"] failed")

            logger.logger(level=logger.INFO , type="parser", message="Done processing all files" , reason="Files: [" + str(self.files_parsed) + "] Parsed, [" + str(self.files_failed) + "] Failed")
            return True
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            logger.logger(level=logger.ERROR , type="parser", message="Failed to parse the files" , reason="Line No. " + str(exc_tb.tb_lineno) + " - " + str(e))
            return False



    def fix_and_push_parsed_data(self, json_res , parser_name , file_path , start_time):
        pushed          = True
        pushed_records  = 0
        failed_records  = 0
        
        try:
            # === fix data type issue with received data
            is_kjson = True if parser_name == 'kjson' else False 
            fixed , failed_records = self.fix_issues_with_parsed_data(json_res , is_kjson)


            logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: fixed issues with parsed data")

            # === push result to database 
            if json_res is not None and len(json_res) != 0:
                for i in range( 0 , len(json_res) , self.es_chunks_size):
                    
                    logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: Pushing result of file ["+file_path+"] to elasticsearch")

                    if parser_name == 'kjson':
                        p = db_es.bulk_queue_push(json_res[ i : (i+self.es_chunks_size) ] ,self.case_id, machine = self.machine_id , chunk_size=self.es_chunks_size , kjson=True)
                    else:
                        p = db_es.bulk_queue_push(json_res[ i : (i+self.es_chunks_size) ] ,self.case_id, source = parser_name , machine = self.machine_id , data_type=parser_name , data_path = file_path , chunk_size=self.es_chunks_size, kjson=False)

                    if p[0] == False:
                        return [False, pushed_records , failed_records , p[1]]
                        

                    logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: Pushed records ["+str(len(json_res[ i : (i+self.es_chunks_size) ]) - len(p[2]))+"] and failed ["+str(len(p[2]))+"]" , reason=p[1])
                    pushed_records+=len(json_res[ i : (i+self.es_chunks_size) ]) - len(p[2])
                    failed_records+=len(p[2])

            return [pushed, pushed_records , failed_records , 'pushed']

        except Exception as e:
            return [False, pushed_records , failed_records , str(e)]


    # =================================================
    #               Helper Functions
    # =================================================
    
    # ================================ get not parsed filse
    # this will get all files need to be parsed by the parser (files not parsed and not parsing currently)
    def get_files_not_parsed(self, parser_details):
        try:
            parser_name = parser_details['name']

            logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: Collect files to be parsed")
            
            files_folder = app.config["UPLOADED_FILES_DEST"] + "/" + self.case_id + "/" + self.machine_id + "/"
            files_folder = files_folder.encode('utf-8')


            # get list of all files in the machine folder
            files = []
            for r, d, f in os.walk(files_folder):
                for file in f:
                    files.append(os.path.join(r, file))
            

            files_to_be_parsed = [] # list of files that needs to be parsed
            # identify the files for the specified parser_name
            for f in files:
                if self.verifiy_file_for_parser(f, parser_details):
                    
                    # === check if the file parsed or not by the parser
                    is_parsed = self.is_file_parsed( f , parser_name)
                    if is_parsed[0] == False:
                        continue 
                    elif is_parsed[0] == True and is_parsed[1] == True:
                        logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: File ["+f+"] already parsed")
                        continue
                    
                    
                    # === check if the file parsing disabled on this file
                    is_disabled = self.is_file_parsing_disabled( f , parser_name)
                    if is_disabled[0] == False:
                        continue
                    elif is_disabled[0] == True and is_disabled[1] == True:
                        logger.logger(level=logger.DEBUG , type="parser", message="Parser["+parser_name+"]: File ["+f+"] parsing disabled")
                        continue
                    
                    # === add the files as parsing for the provided parser in database
                    start_time = str(datetime.now())
                    add_file = self.edit_db_file_status(f , parser_name , start_time , "queued" )
                    if add_file[0] == False:
                        logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: File ["+f+"] failed chaning status to queued" , reason=add_file[1])
                        continue
                    
                    files_to_be_parsed.append(f)
            
            logger.logger(level=logger.INFO , type="parser", message="Parser["+parser_name+"]: Total ["+str(len(files_to_be_parsed))+"] file to be parsed")
            return files_to_be_parsed

        except Exception as e:
            logger.logger(level=logger.ERROR , type="parser", message="Failed processing the parsers" , reason=str(e))
            return False
            
    



    # ================================ check if files belong to the parser
    # check if the provided file is for the provided parser
    def verifiy_file_for_parser(self, file , parser_details):

        try:
            cat_type    = parser_details['parser_files_categorization_type']
            cat_values  = parser_details['parser_files_categorization_values'].split(',')
            filename    = os.path.basename(file)
            
            
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
            logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_details['name']+"]: File ["+f+"] Failed verify whether the file need to be parsed or not" , reason=exc)
        
        return False


    
    # ================================ check if the file already parsed
    # check if the provided file already has been parsed by the provided parser
    def is_file_parsed(self , file , parser_name):
        db_file = db_files.get_by_file_path(self.machine_id , file ) # get file details
        # if file not in DB then not parsed 
        if db_file[0] == False:
            logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: File ["+file+"] Failed checking if parsed or not" , reason=db_file[1])
            return [False ,  None]

        # if the file not found in DB, then it has not been parsed yet
        if db_file[0] and db_file[1] is None:
            return [True, False]


        # check if the parser_name in the parser list of the file in DB 
        for p in db_file[1]['parsers']:
            if parser_name == p['parser_name'] and p['status'] in ['queued','done','parsing']:
                return [True,  True] # True it is parsed, done, or queued

        return [True , False] # False: not parsed

    
    # ================================ check if the parsing for the file is disabled
    # check if the file parsing is disabled on this file or not
    def is_file_parsing_disabled(self , file , parser_name):
        db_file = db_files.get_by_file_path(self.machine_id , file ) # get file details
        # if file not in DB then not parsed 
        if db_file[0] == False:
            logger.logger(level=logger.ERROR , type="parser", message="Parser["+parser_name+"]: File ["+file+"] Failed checking if disabled or not" , reason=db_file[1])
            return [False , None ]

        # if the file not found in DB, then it is not disabled
        if db_file[0] and db_file[1] is None:
            return [True, False]

        # check if the parser_name in the parser list of the file in DB 
        for p in db_file[1]['parsers']:
            if parser_name == p['parser_name'] and 'disable' in p.keys() and p['disable'] == 'True':
                return [True,  True] # True means it is disabled

        return [True , False]# False means it is enabled




    # ================================ change file status
    # change file status (pending, parsing, done, error)
    def edit_db_file_status(self, file , parser_name , start_time , status , message ="", end_time=""):
        file_details = {
            "file_path" : file,
            "parsers"   : {
                "parser_name"   : parser_name , 
                "start_time"    : start_time , 
                "status"        : status , 
                "message"       : message,
                'task_id'       : self.task_id
                },
            "file_size" : os.path.getsize( file )
            }
        add_file = db_files.add_file(self.machine_id , file_details)
        if add_file[0]:
            return [ True, "Changed ["+file+"] for parser ["+parser_name+"] to: " + status]
        else:
            return [ False,  add_file[1]] 


    # =============================== update the files status
    # update the files status for files that are processed via the specified task_id
    def update_db_files_status(self, status, message):
        update_files_by_task = db_files.update_files_by_task_id(self.machine_id , self.task_id , status , message)
        if update_files_by_task[0]:
            return [ True, "updated all files from task ["+self.task_id+"] to " + status + " - message ["+message+"]"]
        else:
            return [ False,  update_files_by_task[1]] 
    
    # ================================ Fix values issues 
    # convert the data received from the parser to string
    # solve other issues with elasticsearch
    def fix_issues_with_parsed_data(self, data , kjson=False):
        fixed       = 0    # this store the number of fixed records, or even if does not need to be fixed
        not_fixed   = 0    # this store the number of records failed to be fixed
        if data is not None and len(data) > 0:
            d = 0
            while d < len(data):
                try:
                    # convert the provided data to string, instead of integers
                    if kjson:
                        self.convert_json_fields_to_str( data[d]['Data'] )
                        
                        # if timestamp contain space " " replace it with "T" to meet the ISO format
                        if '@timestamp' not in data[d]['Data'] or data[d]['Data']['@timestamp'] is None:
                            data[d]['Data']['@timestamp'] = '1700-01-01T00:00:00'

                        if '@timestamp' in data[d]['Data']:
                            data[d]['Data']['@timestamp'] = data[d]['Data']['@timestamp'].replace(' ' , 'T')

                    else:
                        self.convert_json_fields_to_str( data[d] )

                        # if timestamp contain space " " replace it with "T" to meet the ISO format
                        if '@timestamp' not in data[d] or data[d]['@timestamp'] is None:
                            data[d]['@timestamp'] = '1700-01-01T00:00:00'

                        if '@timestamp' in data[d]:
                            data[d]['@timestamp'] = data[d]['@timestamp'].replace(' ' , 'T')
                    
                    fixed +=1 
                    d += 1
                except Exception as e:
                    logger.logger(level=logger.ERROR , type="parser", message="failed fixing the record and will be skipped - " + str(e) , reason=data[d])
                    del data[d]
                    not_fixed+=1


        return [fixed, not_fixed]

            




    # ================================ Celery task state
    # set celery task state
    def set_task_state(self, status, total_parsed_files=0):
        self.update_state(status=status , meta={
            'case'          : self.case_id,
            'machine'       : self.machine_id,
            'parsers'       : ','.join(self.parsers_list),
            'files_done'    : total_parsed_files,
            'total_files'   : self.tmp_total_files
        })


    # ================================ convert fields values to string
    # convert all data types (int, float, bool, etc.) to string to be pushed to elasticsearch
    # some parsers returns fields in a record as a int, but if not exists return it bool...
    def convert_json_fields_to_str(self, json_data):
        # if list
        if isinstance(json_data , list):
            # convert list to dict
            return dict(map(lambda x: (str(x[0]) , self.convert_json_fields_to_str(x[1])) , enumerate(json_data)))
        
        # if dict
        elif isinstance(json_data , dict):
            for k in json_data.keys():
                # if the key type is int, then replace it with str
                if type(k) == int:
                    json_data[str(k)] = json_data[k]
                    del json_data[k]
                    k = str(k)

                # replace "." and " " in field name with "_" (to avoid elasticsearch issue)
                if "." in k or " " in k or '/' in k:
                    k_tmp = k.replace("." , "_").replace(" " , "_").replace("/" , "_")
                    json_data[k_tmp] = json_data[k]
                    del json_data[k]
                    k = k_tmp
                    

                json_data[k] = self.convert_json_fields_to_str(json_data[k])
            return json_data
        else:
            return str(json_data).replace('"' , "'") # replace all (") with ('), elasticsearch does not support it



    
    # =============================== Check avaliable memory
    # this function check the files size in parsing status and the avaliable memory space
    # then check if the following file can be parsed on the memory or not
    def wait_memory_free(self, needed_size):
        files = db_files.get_by_status('parsing')
        if not files[0]:
            return [False, files[1]]

        # get files of all parsing files
        parsing_files_size = 0
        for f in files[1]:
            parsing_files_size += f['file_size']

        available_memory    = dict(psutil.virtual_memory()._asdict())['available']
        
        if (available_memory - (parsing_files_size*1.5)) > needed_size*1.5:
            return False
        else:
            return True
    



# =================================================
#               Celery Functions
# =================================================

# run parsers  
@celery_app.task(name=app.config['celery_task_name'] , bind=True)
def run_parsers(self, main_case_id,machine_case_id,parsers_list):
    
    parser_manager = Parser_Manager(main_case_id , machine_case_id , parsers_list , self.request.id , self.update_state )
    
    try:

        if parser_manager.specify_files_to_be_parser():
            if parser_manager.start_parsing():
                parser_manager.update_state("SUCCESS" , parser_manager.files_parsed)
                logger.logger(level=logger.INFO , type="parser", message="Done processing the task case[" + main_case_id + "] - machine[" + machine_case_id + "] - Parsers["+','.join(parsers_list)+"]")
            else:
                parser_manager.update_state("FAILURE" , parser_manager.files_parsed)
        else:
            parser_manager.update_state("FAILURE" )
        

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        
        parser_manager.update_state(status='FAILURE')
        logger.logger(level=logger.ERROR , type="parser", message="Failed starting the task to process ["+main_case_id+">"+machine_case_id+"] the artifacts" , reason="Line No. " + str(exc_tb.tb_lineno) + " - " + str(e))

# this will handle error hapen in the task parser 
@celery_app.task()
def task_error_handler(request, exc , res):
    
    task_args   =  request.args
    task_id     = request.id 
    logger.logger(level=logger.ERROR , type="parser", message="[Worker] Failed processing task ["+task_id+"] with arg["+task_args[0] +"," + task_args[1] + "," + str(task_args[2])+"] unexpectly" , reason=str(exc))
    parser_manager = Parser_Manager(task_args[0] , task_args[1] , task_args[2]  ,task_id)
    update_files = parser_manager.update_db_files_status('error' , str(exc) )
    if update_files[0]:
        logger.logger(level=logger.INFO , type="parser", message="[Worker] All status of files for task ["+task_id+"] changed to 'error'")
    else:
        logger.logger(level=logger.ERROR , type="parser", message="[Worker] Failed to change all status of files for task ["+task_id+"] to 'error'" , reason=update_files[1])