import lnker
import sys

def auto_link(file , parser):
    try:        
        lnker_data = lnker.main(file)
        if lnker_data is None:
        	return []
        return [lnker_data]

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)


