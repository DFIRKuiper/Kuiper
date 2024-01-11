import sys
import rua
import json
reload(sys)
sys.setdefaultencoding('UTF-8')


def RUA_interface(file, parser):
    try:
        return_data = rua.main(file)
        return return_data

    except Exception as e:
    	exc_type, exc_obj, exc_tb = sys.exc_info()
    	msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
    	return (None , msg)

