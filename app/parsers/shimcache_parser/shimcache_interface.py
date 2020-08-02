 
import json
import shimcache
import sys

# shimcase only parse SYSTEM files
def shimcache_interface( file , parser ):
        try:
			res = shimcache.main(file)
			if res is None:
				return []
			return res
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		
		msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

