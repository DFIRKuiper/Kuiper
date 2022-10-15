import os
import sys
import subprocess
import json
import ast
from datetime import datetime
import uuid


def auto_interface(file , parser):
    try:
        CurrentPath = os.path.dirname(os.path.abspath(__file__))

        if not os.path.exists(CurrentPath + "/temp/"):
            os.mkdir(CurrentPath + "/temp/")

        output_path     = CurrentPath + "/temp/" + str(uuid.uuid4()) + '.json'
        cmd = 'ndpiReader -i '+file+' -k '+output_path+' -K json -q'
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        dd , err = proc.communicate()
        if err != "":
            raise Exception(err.split("\n")[-2])

        output_file = open(output_path , 'r')
        return output_file


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)




def auto_interface_pull(file, num_lines):
    try:
        res = []
        for i in range(0 , num_lines):
            l = file.readline().rstrip()
            if len(l) > 0:            
                rec = json.loads(l)
                if 'first_seen' in rec.keys():
                    rec['first_seen'] = str(datetime.utcfromtimestamp(rec['first_seen']))
                if 'last_seen' in rec.keys():
                    rec['last_seen']  = str(datetime.utcfromtimestamp(rec['last_seen'])) 

                if 'first_seen_ms' in rec.keys():
                    rec['first_seen_ms'] = str(datetime.utcfromtimestamp(rec['first_seen_ms']/1000))
                if 'last_seen_ms' in rec.keys():
                    rec['last_seen_ms']  = str(datetime.utcfromtimestamp(rec['last_seen_ms']/1000)) 

                rec['@timestamp'] = rec['first_seen_ms'] if 'first_seen_ms' in rec.keys() else rec['first_seen']



                res.append(rec)
        return res
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)


