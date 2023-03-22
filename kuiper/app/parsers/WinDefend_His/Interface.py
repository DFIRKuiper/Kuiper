import os
import subprocess
import json 
import ast



def WinDefender_DetectionHistory_interface(file , parser):

    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        cmd = 'python3 '+ CurrentPath+'/dhparser.py -f '+ file
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        dd , err = proc.communicate()
        err = err.decode("utf-8")
        if err != "":
            raise Exception(err.split("\n")[-2])
        decoded_data = dd.decode("utf-8")

        if decoded_data != '':         
            return [i for i in  ast.literal_eval(decoded_data)]
        return []
                
    except Exception as e:
        msg = "Failed " + str(e) 
        return (None , msg)


# WinDefender_DetectionHistory_interface(r"C:\Users\dfir\Desktop\dhparser.py\8CC4BE3D-8D3F-4952-9953-F24EB6638A37","")