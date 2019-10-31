import os
import sys
import json
from datetime import datetime
import analyzeMFT
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


def MFT_interface(file , parser):
    try:
        return_data = analyzeMFT.main(file)
        num_deleted = 0 # count how meny record deleted
        for i in range( 0 , len(return_data)):
            i = i - num_deleted
            if return_data[i] is None: # if record is None delete it
                del return_data[i]
                num_deleted = num_deleted + 1
            else:
                for fn in ['FNInfoModificationdate' , 'FNInfoEntrydate' , 'FNInfoAccessdate' , 'FNInfoModifydate' , 'FNInfoCreationdate']:
                    if return_data[i][ fn ] in ['NoFNRecord' , '']: return_data[i][ fn ] = '1700-01-01T00:00:00'

        return return_data

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)

