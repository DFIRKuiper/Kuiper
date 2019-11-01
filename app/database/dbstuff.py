#!/usr/bin/python

from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import uuid
from datetime import datetime
import hashlib
from bson import ObjectId
import sys
import json
import ast


from app import *


DB_NAME = app.config['DB_NAME']
DB_IP   = app.config['DB_IP']
DB_PORT = app.config['DB_PORT']



# =================================================
#               Database Cases
# =================================================
MClient = MongoClient(DB_IP + ":" + str(DB_PORT) )

class DB_Cases:

    mongo_db = None
    def __init__(self):

        # if cases collection not exists, add it to mongoDB
        db_m = MClient[DB_NAME]
        if 'cases' not in db_m.collection_names():
            db_m.create_collection('cases')

        self.mongo_db = MClient[DB_NAME]["cases"]

    # ======================= Machines ==========================

    # ================================ get all machines for case
    # take case id and return all machines for this case
    def get_machines(self, case_id):
        machines = []
        for d in self.mongo_db["machines"].find({'main_case': case_id}).sort([['creation_time', -1]]):
            machines.append(d)

        return machines

    # ================================ get specific machines by id
    def get_machine_by_id(self , machine_id):
        for i in self.mongo_db["machines"].find({"_id" : machine_id}):
            return i
        return None


    
    # ================================ add machine
    def add_machine(self, machine_details):
        try:
            # Connect to the DB
            collection = self.mongo_db["machines"]

            machine_details['_id'] = machine_details['main_case'] + "_" + machine_details['machinename']
            machine_details['creation_time']= str( datetime.now() ).replace(' ' , 'T')
            # insert into collection
            collection.insert(machine_details)
            return [True, machine_details['_id'] ]

        except DuplicateKeyError:
            return [False , "Machine already exists"] 
        except Exception as e:
            return [False, "Error: " + str(e)]
    
    
    # ================================ delete machine
    def delete_machine(self, machine_id):
        collection = self.mongo_db['machines']
        data = collection.remove({"_id":machine_id})

        collection = MClient[DB_NAME]['files']
        data = collection.remove({"_id":machine_id})

        return data



    # ======================= Cases ==========================

    # ================================ get specific case by id
    def get_case_by_id(self, case_id):
        for d in self.mongo_db.find({'casename' : case_id}):
            return d

    
    # ================================ get all cases
    def get_cases(self):
        try:
            data = self.mongo_db.find({})
            d = []
            for x in data:
                d.append(x)
            return [True , d]

        except Exception as e:
            return [False , str(e)]


    # ================================ Delete case
    # delete case by its id
    def delete_case(self, case_id):
        try:
            data = self.mongo_db.remove({"casename":case_id})
            data = self.mongo_db['machines'].remove({"main_case":case_id})
            return [True, "Case ["+case_id+"] deleted"]
        except Exception as e:
            return [False, str(e)]

    # ================================ Update case
    # update case details information
    def update_case(self, case_id , case_details):
        try:
            up = self.mongo_db.update({'casename':case_id}, {'$set': case_details },upsert=False)
            return [True, up]
        except Exception as e:
            return [False, "Error: " + str(e)]

    # ================================ Create case
    # create new case
    def create_case(self, case_details):
        try:
            # get the UUID for casename as case id
            idtest = str(uuid.uuid4())
            idtestfilter = idtest.replace('-','')
            case_id = idtestfilter

            data = {
                '_id'                   :case_details['casename'],
                'casename'              :case_details['casename'],
                'status'                :case_details['status'],
                'date'                  :case_details['date']
            }


            # insert into collection
            self.mongo_db.insert(data)
            return [True, data]

        except DuplicateKeyError:
            return [False, "Case ["+case_details['casename']+"] already present in DB"]
        except Exception as e:
            return [False , "Error:" + str(e)]

# generate the db class object
def get_db_cases():
    return DB_Cases()


# =================================================
#               End Database Cases
# =================================================








# =================================================
#               Database Rules
# =================================================

# ===================================== DB rules
# this class contain the rules
class DB_Rules():
    MongoClient = None
    def __init__(self):

        # if rules collection not exists, add it to mongoDB
        db_m = MClient[DB_NAME]
        
        if 'rules' not in db_m.collection_names():
            db_m.create_collection('rules')

        self.MongoClient = MClient[DB_NAME]["rules"]


    # ===================================== Get rules
    # get a list of all rules
    def get_rules(self):
        try:
            data = self.MongoClient.find({})
            datax = []
            for x in data:
                datax.append(x)
            return [True, datax]
        except Exception as e:
            return [False, str(e)]


    # ===================================== Delete rule
    # delete rule
    def delete_rule(self, rule_id):
        try:
            self.MongoClient.remove({"_id":rule_id})
            return [True , "Rule ["+rule_id+"] deleted from mongoDB"]
        except Exception as e:
            return [False , e]

    # ===================================== Update rule
    # update rule
    def update_rule(self, rule_id , new_rule , new_sev , new_desc):
        try:
            up = self.MongoClient.update({'_id':rule_id}, {'$set': {'rule' : new_rule , 'rule_severity' : new_sev , 'rule_description' : new_desc} },upsert=False)
            if up['updatedExisting']:
                return [True , "Rule ["+rule_id+"] updated from mongoDB"]
            else:
                return [False , "Rule ["+rule_id+"] failed updated from mongoDB"]

        except Exception as e:
            print(e)
            return [False , "Error: " + str(e)]

    # ===================================== Add rule
    # add rule to data base
    def add_rule(self, rule_name , rule , rule_severity , rule_description):
        try:
            # insert the rule to mongoDB
            rule_id = hashlib.md5(rule_name).hexdigest() # get md5 hash of rule and use it as rule id to avoid duplication

            self.MongoClient.insert({
                '_id' : rule_id,
                "rule" : rule,
                'rule_name' : rule_name,
                'rule_severity' : rule_severity,
                'rule_description' : rule_description
                })
            return [True , "Rule ["+rule_name+"] added to mongoDB"]

        except DuplicateKeyError:
            return [False , "Rule ["+rule_name+"] already exists"]

        except Exception as e:
            return [False , "Error: " + str(e)]


# generate the db rule object
def get_db_rules():
    return DB_Rules()



# =================================================
#               End Database Rules 
# =================================================








# =================================================
#               Database Parsers
# =================================================

# ===================================== DB Parsers
class DB_Parsers:
    
    collection = None
    def __init__(self):
        # if parsers collection not exists, add it to mongoDB
        db_m = MClient[DB_NAME]
        
        if 'parsers' not in db_m.collection_names():
            db_m.create_collection('parsers')

        self.collection = MClient[DB_NAME]["parsers"]


        # == check the parsers on parsers folder and if parser not on the DB
        # == read the configuration from the parser folder and push it to the DB
        # get all parsers on the parsers folder
        filenames   = os.listdir( app.config['PARSER_PATH'] ) 
        parsers     = []
        for files in filenames:
            if os.path.isdir( app.config['PARSER_PATH'] + "/" + files ):
                parsers.append( [ files ,  app.config['PARSER_PATH'] + "/" + files ] )


        # check if the parser on the DB, if not add it
        for p in parsers:
            # get the configuration file from the parser folder
            conf_path = p[1] + "/configuration.json" 
            if os.path.exists( conf_path ):
                
                with open( conf_path ) as conf_json_file:
                    conf_json = ast.literal_eval(conf_json_file.read())
                    for conf in conf_json:
                        if self.get_parser_by_name( conf['name'] )[0] == False: # if parser not found
                            print "====================="
                            # push the parser information to the DB
                            if self.add_parser( conf ):
                                print "[+] Parser ["+conf['name']+"] added to DB"
                            else:
                                print "[-] Error: dailed to add parser ["+conf['name']+"] - "



    # ===================================== add parser
    def add_parser(self, parser_details):
        try:
            parser_details['_id'] = parser_details['name']
            parser_details['creation_time']= str( datetime.now() ).replace(' ' , 'T')
            # insert into collection
            self.collection.insert(parser_details)
            return [True, parser_details['_id'] ]

        except DuplicateKeyError:
            return [False, "Parser ["+parser_details['name']+"] already present in DB."]
    
    # ===================================== edit parser
    def edit_parser(self, parser_name ,  parser_details):
        try:
            # update into collection
            up = self.collection.update({'_id':parser_name}, {'$set': parser_details},upsert=False)
            if up['updatedExisting']:
                return [True , "Parser ["+parser_details['name']+"] updated from mongoDB"]
            else:
                return [False , "Parser ["+parser_details['name']+"] failed updated from mongoDB"]

        except Exception as e:
            return [False, "Error: " + str(e) ]


    # ===================================== get parsers details
    def get_parser(self):
        parsers = []
        for p in self.collection.find({}).sort([['creation_time', -1]]):
            parsers.append(p)
        
        return parsers
    
    # ===================================== get parser by name
    # get parser details by its name
    def get_parser_by_name(self, parser_name):
        for p in self.collection.find({}):
            if p['name'] == parser_name:
                return [True, p]
        return [False, "Parser ["+parser_name+"] not found"]
    
    # ===================================== Delete parser
    # delete parser by name
    def delete_parser_by_name(self, parser_name):
        try:
            data = self.collection.remove({"_id": parser_name})
            return [True , "Parser ["+parser_name+"] deleted"]
        except Exception as e:
            return [False , "Error: " + str(e)]



# this class contain the parsers
def get_db_parsers():
    return DB_Parsers()

# =================================================
#               End Database Parsers 
# =================================================








# =================================================
#               Database Files
# =================================================

#======================================= Machine files

class DB_Files:
    
    collection = None
    def __init__(self):

        # if files collection not exists, add it to mongoDB
        db_m = MClient[DB_NAME]
        if 'files' not in db_m.collection_names():
            db_m.create_collection('files')

        self.collection = MClient[DB_NAME]["files"]

    # ===================================== Get machine files
    # get all files for specified machine
    def get_by_machine(self, machine_id):
        machine_files = self.add_machine_in_files(machine_id) # if machine not in DB add it
        for p in self.collection.find({'_id' : machine_id}):
            return [True, p]
        return [False, "Machine ["+machine_id+"] not found"]


    # ===================================== add machine in files
    # inside the files collection, if the machine not defined add it
    def add_machine_in_files(self, machine_id):
        # === check if the machine exists in files DB, if not exists create it
        machine_files = None # store the files for specifc machine in DB
        for m in self.collection.find({'_id': machine_id}):
            machine_files = m 
        # if machine not exists, add it
        if machine_files is None:
            self.collection.insert({"_id" : machine_id , "files" : []})
            for m in self.collection.find({'_id': machine_id}):
                machine_files = m
            
        return machine_files 


    # ===================================== Disable/Enable file processing
    # this function will disable a file from being parsed by specific parser
    def disable_enable_file(self, machine_id , file_path, parser , disable):
        try:
            machine = self.get_by_machine(machine_id)
            # if file not exists
            if machine[0] == False:
                return [False , machine[1]]
            
            files = machine[1]['files']
            # add field disable as True on the files json
            for f in range(len(files)):
                if files[f]['file_path'] == file_path:
                    for p in range(len(files[f]['parsers'])):
                        if files[f]['parsers'][p]['parser_name'] == parser:
                            files[f]['parsers'][p]['disable'] = str(disable)
            
            up = self.collection.update({'_id':machine_id}, {'$set': {'files' : files}})
            
            if up:
                s = "disabled" if disable else "enabled"
                return [True , "File ["+file_path+"] "+s+" on parser ["+parser+"]" ]
            else:
                return [False , "Failed to update the record"]

        except Exception as e:
            return [False , "Failed to update the record: " + str(e)]

    # ===================================== Add file
    # add files to the database
    def add_file(self, machine_id , file_details):
        try:
            machine_files = self.add_machine_in_files(machine_id)

            # === merge the file_details with the files from the database
            # check if the file in DB, if yes get its information
            file_in_db = False
            for i in range(0 , len(machine_files['files']) ):
                if machine_files['files'][i]['file_path'] == file_details['file_path']:
                    file_in_db = True # if file in database
                    parser_in_file = False
                    # check if parser already exists, edit the parser details
                    for p in range( 0 , len(machine_files['files'][i]['parsers'])):
                        if machine_files['files'][i]['parsers'][p]['parser_name'] == file_details['parsers']['parser_name']:
                            machine_files['files'][i]['parsers'][p] = file_details['parsers']
                            parser_in_file = True
                            break

                    # if parser not exists for the file, add the parser
                    if parser_in_file == False:
                        print file_details['parsers']
                        machine_files['files'][i]['parsers'].append( file_details['parsers'] )
                    
                    break
            if file_in_db == False:
                # if file not in DB, the parser should be in list, since there is no parsers before
                file_details['parsers'] = [file_details['parsers']]
                machine_files['files'].append(file_details)
            
            # delete record id
            del machine_files['_id']
            
            # === edit the database with the new list of files
            up = self.collection.update({'_id':machine_id}, {'$set': machine_files},upsert=False)
            if up:
                return [True , "File added to database"]
            else:
                return [False , "Failed to update the record"]

        except DuplicateKeyError:
            return [False , "Machine already present in DB." ]
        except Exception as e:
            return [False , "Error: " + str(e)]

    
    # ===================================== Get file details
    # get parsers details for all parsers by the file path
    def get_by_file_path(self, machine_id , file_path):
        
        machine_files = self.add_machine_in_files(machine_id) # if machine not in DB add it

        for p in self.collection.find({'_id' : machine_id}):
            for f in p['files']:
                if f['file_path'] == file_path:
                    return [True , f]

        return [False , "Error: File ["+file_path+"] not in DB"]
    
    # ===================================== Get parsing progress
    # get the status of parsers for specific machine
    def get_parsing_progress(self, machine_id):
        machine_files = self.add_machine_in_files(machine_id) # if machine not in DB add it
        parsers_progress = {}
        for db_f in self.collection.find({'_id' : machine_id}):
            for f in db_f['files']:
                for p in f['parsers']:
                    if p['parser_name'] not in parsers_progress.keys():
                        parsers_progress[ p['parser_name'] ] = []
                    parsers_progress[ p['parser_name'] ].append( {'file' : f['file_path'] , 'status' : p['status']} )
                    
        return [True, parsers_progress]


# this class contain the files
def get_db_files():
    return DB_Files()

# =================================================
#               End Database Files 
# =================================================





db_cases    = get_db_cases()    # get case database
db_rules    = get_db_rules()    # get rule database
db_files    = get_db_files()    # get files databse
db_parsers  = get_db_parsers()  # get parser database