# from plugin import amcache,shimcache,userassist
import sys
import recyclebin
import json


def recyclebin_interface(file, parser):
    try:
        recyclebin_data = recyclebin.main(file)
        
        return recyclebin_data

    except Exception as e:
    	exc_type, exc_obj, exc_tb = sys.exc_info()
    	msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
    	return (None , msg)



