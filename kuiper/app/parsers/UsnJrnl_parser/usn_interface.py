import os
import sys
import json
from datetime import datetime
import usn
import sys
import time
reload(sys)
sys.setdefaultencoding('utf-8')


def UsnJrnl_interface(file , parser):
    try:
        return_data = usn.parserusn(file)


        return return_data

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)


