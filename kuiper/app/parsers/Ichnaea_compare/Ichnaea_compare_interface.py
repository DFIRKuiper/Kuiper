import sys
import os
import Ichnaea_compare as compare

def Ichnaea_compare_interface(file, parser):
    try:
        file = os.path.dirname(os.path.abspath(file))
        parentPath=os.path.relpath(os.path.join(os.path.join(os.path.join(os.path.join(file, os.pardir),os.pardir),os.pardir),os.pardir))
        historyPath= parentPath + "/inetpub/history"
        compare_obj = compare.Ichnaea(file, historyPath)
        return_data = []
        if compare_obj.compareResult is not None:
            return_data = compare_obj.compareResult
        return return_data

    except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
                return (None, msg)           





