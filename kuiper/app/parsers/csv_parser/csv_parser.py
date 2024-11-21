
import csv  
import json  
import sys


def auto_csv_parser(file , parser):
	# Open the CSV  
	try:
		f = open( file, 'r' )  
		# Change each fieldname to the appropriate field name. I know, so difficult.  
		reader = csv.DictReader( f )  
		records = [ row for row in reader ]    
		return records
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		
		msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)

