
# -*- coding: utf-8 -*-

import os
import subprocess
import json 
import sys
import uuid



def Events_interface(file , parser):

    try:
        CurrentPath    =os.path.dirname(os.path.abspath(__file__))
        output_path = CurrentPath + "/" + str(uuid.uuid4())
        cmd = CurrentPath + '/evtx_dump "'+file+'" --no-indent  --format json --ansi-codec utf-8 --dont-show-record-number --output ' + output_path
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        dd , err = proc.communicate()
        if err != "":
            raise Exception(err.split("\n")[-2])


        return open(output_path , 'r')


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)



def Events_interface_pull(file, num_lines):
    try:
        res = []
        for i in range(0 , num_lines):
            l = file.readline().rstrip()
            if l != '':            
                rec = json.loads(l)
                rec['@timestamp'] = rec['Event']['System']['TimeCreated']['#attributes']['SystemTime']

                # fix the event id issue
                if type(rec['Event']['System']['EventID']) == int:
                    rec['Event']['System']['EventID'] = {'#text' : rec['Event']['System']['EventID']}

                # fix the correlation issue
                if 'Correlation' in rec['Event']['System'].keys():
                    if rec['Event']['System']['Correlation'] is None:
                        del rec['Event']['System']['Correlation']

                # fix the EventData null value 
                if 'EventData' in rec['Event']:
                    
                    if rec['Event']['EventData'] is None:
                        del rec['Event']['EventData']

                # if the Data field string, change the field name to DataText
                # some records have Data as json and some has text, which confuse elasticsearch
                if 'EventData' in rec['Event']:
                    if 'Data' in rec['Event']['EventData']:
                        if isinstance(rec['Event']['EventData']['Data'] , str):
                            rec['Event']['EventData']['DataText'] = rec['Event']['EventData']['Data']
                            del rec['Event']['EventData']['Data']

                # this will delete all fields of null value to avoid issue on data field mapping 
                delete_null(rec['Event'])


                
                remove_attributes_field(rec)
                res.append(rec)
        return res
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

def delete_null(json):
    
    if isinstance( json , dict ):
        for j in json.keys():
            if json[j] is None:
                del json[j]
                continue
            delete_null(json[j])


    
def remove_attributes_field(json):
    if not isinstance(json , dict):
        return json

    if "#text" in json.keys() and isinstance(json['#text'] , list):
        try:
            json['#text'] = '\n'.join(  json['#text'] )
        except Exception as e:
            pass
    # rename  the #attributes to @ + attr name 
    if "#attributes" in json.keys():
        for attr in json["#attributes"].keys():
            json["@"+attr] = json["#attributes"][attr]
        del json["#attributes"]
    
    for i in json.keys():
        # if there is a . in the field name, replace it with "_"
        remove_attributes_field(json[i])
        if i.find(".") != -1:
            json[i.replace("." , "_")] = json[i]
            del json[i]
    return json
            
