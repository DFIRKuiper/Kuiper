# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import contextlib
import mmap
import traceback
import json
import argparse
from collections import OrderedDict
from datetime import datetime

from Evtx.Evtx import FileHeader
from Evtx.Views import evtx_file_xml_view

import xmltodict
from lxml import etree
from io import StringIO, BytesIO
import re
import string



# return json in a beautifier
def json_beautifier(js):

	return json.dumps(js, indent=4, sort_keys=True)


# class to control the evtx to ELK
class EvtxToElk:
	
    @staticmethod
    def syntax_resolver(xml):

	# remove any "<>" on the xml since it is not valid
	xml = xml.replace("<>" , "")
	xml = ''.join([x if x in string.printable else '' for x in xml])

	# fix "<<PROCESS>>" => "<PROCESS>"
	search = re.findall('\<\<[^>]*\>\>', xml)
	#print "---"
	for g in search:
		#print g
		res = g.replace("<","").replace(">","")
		xml = re.sub('\<\<[^>]*\>\>', res, xml)

	# find all elements
	all_matches = re.findall("\<[^>]+\>" , xml)

	for e in range(0 , len(all_matches)):
		# if uniq element "<element/>" will not be counted
		if all_matches[e].endswith("/>"):
			del(all_matches[e])
			e -= 1
			continue
			
		# get only the element name
		all_matches[e] = all_matches[e].replace(">","").replace("</","").replace("<","").split(" ")[0]
	# find any element without closing tag
	odd_tags = []		
	for am in all_matches:
		if all_matches.count(am) == 1:
			odd_tags.append(am)

	# remove the odd tags from the original xml
	for ot in odd_tags:
		xml = re.sub('\<'+ot+'[^>]*\>',ot , xml)

	return xml
    
  
	
    @staticmethod
    def build_json(xml):
		# validate the given xml, if it is not valid xml try to resolve it
		try:
			etree.fromstring(xml) 
		except: 
			xml = EvtxToElk.syntax_resolver(xml)
		
		# parse the xml to json 
		log_line = xmltodict.parse(xml)

		# Format the date field
		date = log_line.get("Event").get("System").get("TimeCreated").get("@SystemTime")
		if "." not in str(date):
		    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
		else:
		    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
		log_line['@timestamp'] = str(date.isoformat())
		log_line["Event"]["System"]["TimeCreated"]["@SystemTime"] = str(date.isoformat())

		# Process the data field to be searchable
		data = ""
		if log_line.get("Event") is not None:
		    data = log_line.get("Event")
		    if log_line.get("Event").get("EventData") is not None:
			data = log_line.get("Event").get("EventData")
			if log_line.get("Event").get("EventData").get("Data") is not None:
			    data = log_line.get("Event").get("EventData").get("Data")
			    if isinstance(data, list):
			        contains_event_data = True
			        data_vals = {}
			        for dataitem in data:
			        	try:
			        		if dataitem.get("@Name") is not None:
			        			data_vals[str(dataitem.get("@Name"))] = str( str(dataitem.get("#text")) )
			        	except:
							pass

			        log_line["Event"]["EventData"]["Data"] = data_vals
			    else:
			        if isinstance(data, OrderedDict):
			            log_line["Event"]["EventData"]["RawData"] = json.dumps(data)
			        else:
			            log_line["Event"]["EventData"]["RawData"] = str(data)
			        del log_line["Event"]["EventData"]["Data"]
			else:
			    if isinstance(data, OrderedDict):
			        log_line["Event"]["RawData"] = json.dumps(data)
			    else:
			        log_line["Event"]["RawData"] = str(data)
			    del log_line["Event"]["EventData"]
		    else:
			if isinstance(data, OrderedDict):
				log_line["Event"] = dict(data)
			else:
				log_line["RawData"] = str(data)
				del log_line["Event"]
		else:
			pass
		return log_line

    
	
    @staticmethod
    def parse(filename):
    	
        bulk_data = []
        with open(filename) as infile:
        	
        	with contextlib.closing(mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)) as buf:
        		fh = FileHeader(buf, 0x0)
        		for xml, record in evtx_file_xml_view(fh):
        			contains_event_data = False

        			log_line = EvtxToElk.build_json(xml)
        			bulk_data.append(json.loads(json.dumps(log_line) ) )

        return bulk_data
			
			
"""
if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser()
    # Add arguments
    parser.add_argument('evtxfile', help="Evtx file to parse")
    parser.add_argument('elk_ip', default="localhost", help="IP (and port) of ELK instance")
    parser.add_argument('-i', default="hostlogs", help="ELK index to load data into")
    parser.add_argument('-s', default=2000, help="Size of queue")
    parser.add_argument('-meta', default={}, type=json.loads, help="Metadata to add to records")
    # Parse arguments and call evtx to elk class
    args = parser.parse_args()
    EvtxToElk.evtx_to_elk(args.evtxfile, args.elk_ip, elk_index=args.i, bulk_queue_len_threshold=int(args.s), metadata=args.meta)
"""
