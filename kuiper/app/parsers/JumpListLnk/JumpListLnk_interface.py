# -*- coding: utf-8 -*-

import os
import subprocess
import json 
import ast
import sys



def JLParser_interface(file , parser):

    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        cmd = 'python3 '+ CurrentPath+'/JLParser.py -f "'+file+'"'

        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        dd , err = proc.communicate()
        if err != "":
            raise Exception(err.split("\n")[-2])

        decoded_data = (dd.decode('utf-8')).rstrip()

        if decoded_data != '':            
            return ast.literal_eval(decoded_data)
        return []
                
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "Failed " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)




