"""
MIT License
Copyright (c) 2022
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re,os,csv
from lxml import etree
from Evtx.Evtx import Evtx
from Evtx.Views import evtx_file_xml_view
from zipfile import ZipFile 
import base64
from base64 import b64decode



def Magic(evtx):
	ps_scripts_ran = []
	for xml, row in evtx_file_xml_view(evtx.get_file_header()):
		try:
			for entry in to_lxml(xml):
				
				R_ID = entry.xpath("/Event/System/EventRecordID")[0].text
				#print R_ID
				ctime = entry.xpath("/Event/System/TimeCreated")[0].get("SystemTime")
				#print ctime
				Computer = entry.xpath("/Event/System/Computer")[0].text
				#print Computer
				user = entry.xpath("/Event/System/Security")[0].text
				#print user
				paths = str(to_lxml(xml).xpath("/Event/EventData/Data")[0].text)
				path=""
				for line in paths.split("\n"):
					#print path
					if "HostApplication" in line:
						line.split("HostApplication=")[1]
						path=line
				
				regex_Base64=""
				
				if "-EncodedCommand" in path:
					regex_Base64=(path.split("-EncodedCommand")[1]).strip()
						
				elif "-enc" in path:
					regex_Base64=(path.split("-enc")[1]).strip()
					
				else:
					regex_Base64="No Base64 Found"
					
			
				exists = False
				for item in ps_scripts_ran:
					if item[3]== path:
						exists = True
				if not exists:
					ps_scripts_ran.append([R_ID, str(ctime) ,Computer,path,regex_Base64])

		except Exception :
			continue
	return ps_scripts_ran
	
	
	
	
	
def to_lxml(record_xml):
    utf8_parser = etree.XMLParser(encoding='utf-8')
    return etree.fromstring("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\" ?>%s" %
            record_xml.replace("xmlns=\"http://schemas.microsoft.com/win/2004/08/events/event\"", "").encode('utf-8'), parser=utf8_parser)
 
	
def to_Base64(Coded):
	decript=[]
	if Coded == "No Base64 Found":
		return Coded
	else:
		f=b64decode(Coded).strip()
		for each in f :
			if each ==  '\x00' :
				pass
			else:
				decript.append(each)
	
		return "".join(decript)
	


def OutPut(script_data):
	path_s=[]
	
	for entries in script_data:
		path_s.append({"RecordID" : entries[0] ,"@timestamp": entries[1],"Computer_Name": entries[2],"Exeution":entries[3],"Base64":to_Base64(entries[4])})
	return path_s




def WindowsPowerShell(file , parser):
	with Evtx(os.path.abspath(file)) as evtx: 
		script_data = Magic(evtx)
		OutPut(script_data)
                    
	

