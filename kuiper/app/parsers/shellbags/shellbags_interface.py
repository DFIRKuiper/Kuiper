import shellbags_Custom_parser
from Registry import Registry
import sys

def auto_shellbags(file , parser):
	try:
		registry = Registry.Registry(file)
		h = shellbags_Custom_parser.get_all_shellbags(registry)
		return h
		
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		
		msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

