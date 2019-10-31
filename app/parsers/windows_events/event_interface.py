from evtxtoelk.evtxtoelk import EvtxToElk

import sys
import json
import os 


def auto_interface(file, parser):
	try:
		# check file size, skip file over 750MB
		file_size = (( os.stat(file).st_size ) / 1024 ) / 1024
		if file_size > 750:
			return []
		res = EvtxToElk.parse(file)
		return res
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		
		msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)



