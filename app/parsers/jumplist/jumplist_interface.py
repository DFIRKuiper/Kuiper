# -*- coding: utf-8 -*-

import os
import subprocess
import json 
import ast
import sys



def auto_jumplist(file , parser):
        try:
                CurrentPath=os.path.dirname(os.path.abspath(__file__))
                cmd = 'python3 '+ CurrentPath+'/jumplist.py -a  -i ' + file
                proc = subprocess.Popen(cmd, shell=True ,stdout=subprocess.PIPE)
                dd = proc.communicate()[0]
                decoded_data = (dd.decode('utf-8')).rstrip()
                if decoded_data == '':
                        return []
                else:
                        decoded_data = ast.literal_eval(decoded_data)
                        print decoded_data
                        #ff = json.dumps(ast.literal_eval(json.dumps(decoded_data)))
                        #print list(json.loads(ff))

                        return [decoded_data]
                
        except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                
		msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
                print msg
                return (None , msg)




