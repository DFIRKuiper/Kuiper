from mans_parser import ParseMans
import sys
import json 

def imain(file , parser):

    try:
        pm = ParseMans(mans_file = file)

        records = pm.parse_files()
        return records 


    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None, msg )


