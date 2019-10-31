import BrowserHistory_ELK
import os



def auto_browser_history(file , parser):
	print "browser interface " + file
	try:
		filename = os.path.basename(file)
		if filename == "History":
			h = BrowserHistory_ELK.extract_chrome_history(file)
			data_src = "chrome_history"
		elif filename == "WebCacheV01.dat":
			h = BrowserHistory_ELK.extract_webcachev01_dat(file)
			data_src = "IE_history"
		elif filename == "places.sqlite":
			h = BrowserHistory_ELK.extract_firefox_history(file)
			data_src = "Firefox_history"
		else:
			pass
		return h
		
	except Exception as exc:
		print exc
		return []


