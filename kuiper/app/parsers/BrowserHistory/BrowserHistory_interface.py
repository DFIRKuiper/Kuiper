import BrowserHistory_ELK
import os
import sys 


def auto_browser_history(file , parser):
    try:
        filename = os.path.basename(file)
        if filename == "History":
            h = BrowserHistory_ELK.extract_chrome_history(file)
        elif filename == "WebCacheV01.dat":
            h = BrowserHistory_ELK.extract_webcachev01_dat(file)
        elif filename == "places.sqlite":
            h = BrowserHistory_ELK.extract_firefox_history(file)
        else:
            pass
        return h
        
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None, msg )



