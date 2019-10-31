


import subprocess
import json
import ast
import os 
import sys


# fix the "datetime.datetime(2019, 7, 26, 17, 18, 49, 866488)" issue on the result of the parser
def delete_datetime_obj(json_line):

	while True:
		datetime_indx = json_line.find('datetime')
		if datetime_indx == -1:
			break
		datetime_end = json_line.find(')' , datetime_indx)
		datetime = json_line[datetime_indx:datetime_end+1]
		datetime_list = datetime.replace('datetime.datetime(' , '').replace(')' , '').replace(' ' , '').split(',')
		new_datetime = datetime_list[0].rjust(4 ,'0') + "-" + datetime_list[1].rjust(2 ,'0') + "-" + datetime_list[2].rjust(2 ,'0') + "T" + datetime_list[3].rjust(2 ,'0') + ":" + datetime_list[4].rjust(2 ,'0') + ":" + datetime_list[5].rjust(2 ,'0')
		json_line = json_line.replace(datetime , "'" + new_datetime + "'")
	return json_line

# parser interface
def bits_admin_interface(file , parser):
	try:
		p = subprocess.Popen(['bits_parser',file] , stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		res , err = p.communicate() 
		columns = res.split('\n')[0].strip().split(',')
		output = []
		for lines in res.split('\n')[1:]: 
			l = {}
			line = lines.strip().split(',')
			if len(line) != len(columns):
				continue
			for c in range(0 , len(columns)):
				#print columns[c] + " = " + line[c]
				if columns[c] in ['ctime' , 'mtime' , 'other_time1' , 'other_time0' , 'other_time2' ]:
					line[c] = line[c].replace(' ' , 'T').split('.')[0]
				l[ columns[c] ] = line[c]
			l['@timestamp'] = l['ctime']
			output.append(l)
		"""
		for json_line in res.split('\n'):
			print json_line
			if json_line.startswith('{'):
				json_line = delete_datetime_obj(json_line)
				json_line = ast.literal_eval(json_line)	# remove single quote from the json string
				json_line['@timestamp'] = json_line['ctime']
				output.append(  json_line  ) 
		"""

		return output
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		
		msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)


