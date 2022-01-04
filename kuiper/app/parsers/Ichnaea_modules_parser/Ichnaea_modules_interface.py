import sys
import Ichnaea_modules_Parser as modules

def Ichnaea_modules_interface(file, parser):
    try:
        sites_obj = modules.Ichnaea(file)
        return_data = []
        if sites_obj.IIS_modules is not None:
            return_data = sites_obj.IIS_modules
        return return_data

    except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
            return (None, msg)