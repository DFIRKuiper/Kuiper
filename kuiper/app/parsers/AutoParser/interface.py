import os
import sys
import subprocess
import json
import ast

def auto_interface(file,parser):

    lst = [ 'AppinitDLLs', 'BootExecute', 'Codecs', 'CompresseApp', 'Explorer', 'ImageHijacks', 'InternetExplorerAddons', 'KnownDLLs', 'Logon', 'LSAsecurityProviders', 'OfficeAddins', 'PrintMonitorDLLs', 'RDP', 'SMB', 'VSS', 'Winlogon', 'WinServices', 'Winsock' ]
    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        if parser in lst:
            cmd = 'python3 '+ CurrentPath+'/AutoParser.py -k -f "' + file.replace("$" , '\$') + '" -pl ' + parser + ' -t'
            proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
            res , err = proc.communicate()

            # the error "An error has occurred when recovering a hive using a transaction log"
            if err != "" and err != "An error has occurred when recovering a hive using a transaction log":
                raise Exception(err.split("\n")[-2])

            res = res.split('\n')
            data = ""
            for line in res:
                if line.startswith('['):
                    data += line
            if data == "":
                return []
            d = []
            for i in ast.literal_eval(data):
                if type(i) == dict:
                    if len(i.keys()):
                        d.append(i)
                    else:
                        continue
                else:
                    d.append(json.loads(i) )
            return d
        else:
            return (None, "[-] [Error] "+str(parser)+" Parser: is not exists")

    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)
