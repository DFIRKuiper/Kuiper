
import amcache
import sys


def auto_amcache(file,parser):
    try:
        file_amcache = file	
        amcache_data = amcache.main(file_amcache)
        return amcache_data

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)
