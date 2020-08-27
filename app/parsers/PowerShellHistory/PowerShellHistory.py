

import sys


def PowerShellHistory(file , parser):
    # Open the CSV  
    try:
        f = open( file, 'r' )  
        # Change each fieldname to the appropriate field name. I know, so difficult.  
        data = []
        for l in f.readlines():
            data.append({"command" : l.strip()})
        return data
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        
        msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)



