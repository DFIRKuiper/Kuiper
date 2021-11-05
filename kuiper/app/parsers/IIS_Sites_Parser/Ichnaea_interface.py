import sys
import Ichnaea_Sites_Parser as sites

def Ichnaea_interface(file, parser):
    try:
        sites_obj = sites.Ichnaea(file)
        return_data = []
        if sites_obj.IIS_Sites is not None:
            return_data = sites_obj.IIS_Sites
        return return_data

    except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
            return (None, msg)