
import PyWMIPersistenceFinder
import sys


def auto_wmi_persistence(file,parser):
    try:
        file_amcache = file	
        WMI_DATA = PyWMIPersistenceFinder.main(file_amcache)
        return WMI_DATA

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

