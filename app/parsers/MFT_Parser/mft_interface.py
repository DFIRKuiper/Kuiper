
#!/usr/bin/python

import os
import sys
import json
from datetime import datetime
import sys
import uuid 
import subprocess

reload(sys)
sys.setdefaultencoding('utf-8')


def MFT_interface(file , parser):
    file = file.replace("$" , "\$")
    try:
        CurrentPath     = os.path.dirname(os.path.abspath(__file__))
        output_path     = CurrentPath + "/" + str(uuid.uuid4())
        cmd = CurrentPath + '/mft_dump "'+file+'" --output-format csv --no-confirm-overwrite --output ' + output_path
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        dd , err = proc.communicate()
        if err != "":
            raise Exception(err.split("\n")[-2])

        output_file = open(output_path , 'r')
        output_file.readline() # this used to skip the first line from the file
        return output_file


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)



def MFT_interface_pull(file, num_lines):
    try:
        real_path = os.path.realpath(file.name)
        real_file = open(real_path , 'r')
        columns = real_file.readline().replace("StandardInfo" , "SI").replace("FileName" , "FN").rstrip().split(',')
        real_file.close()


        res = []
        for i in range(0 , num_lines):
            record = file.readline().rstrip()
            if record != '':            
                record = record.split(',' , len(columns)-1)
                record_json = {}
                if len(columns) != len(record):
                    continue


                for i in range(0 , len(record)):
                    record_json[columns[i]] = record[i]
                

                for fn in ['SILastModified' , 'SILastAccess' , 'SICreated' , 'FNLastModified' , 'FNLastAccess' , 'FNCreated']:
                    if fn in record_json.keys() and record_json[ fn ] in ['NoFNRecord' , '']: 
                        record_json[ fn ] = '1700-01-01T00:00:00'

                record_json['@timestamp'] = record_json['SICreated']

                record_json['FullPath'] = record_json['FullPath'].replace("/" , "\\")

                res.append(record_json)
        return res
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)



