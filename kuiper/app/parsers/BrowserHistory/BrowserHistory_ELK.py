# -*- coding: utf-8 -*-

import csv, json
import pyesedb
import re
from datetime import datetime, timedelta
import sqlite3
from elasticsearch import Elasticsearch, helpers


"""
==============================================

This script used to push parse and push web history files to elasticsearch database
change the values for:
es_link: link to the elasticsearch database
es_index: index to push to on the database
browser: define the browser name (chrome,IE,firefox)
path: path of the web history file (
	chrome 	-> "History" file
	IE 		-> "WebCacheV01.dat" file
	firefox -> "places.sqlite"

==============================================
"""

es_link = "http://<ip address>:9200"
es_index = "test_history"
path = "samples/places.sqlite"
browser = "firefox"

# push the web history to elk
def push_to_elk(url , index , data):
	es = Elasticsearch(url)

	bulk_queue = []
	for d in data:
		di = {
	   		"_index": index,
			"_type": 'None',
			"_source": { "Data" : d }
		}
		bulk_queue.append(di)	

	print 'Bulkingrecords to ES: ' + str(len(bulk_queue))
	try:
		helpers.bulk(es, bulk_queue)
		return True
	except:
		ret = False # the value to return
		# get the error message and print it
		error = sys.exc_info()

# return json in a beautifier
def json_beautifier(js):
	return json.dumps(js, indent=4, sort_keys=True)



def convert_timestamp(timestamp, browser_name=None, tz='utc'):
		"""Helper function to convert different timestamps formats into date strings or POSIX timestamp.
		:param timestamp: Timestamp
		:return: POSIX timestamp (UTC)
		"""
		if browser_name == 'Chrome':
			date = datetime(1601, 1, 1) + timedelta(microseconds=timestamp)
		elif browser_name == 'IE11':
			date = datetime(1601, 1, 1) + timedelta(microseconds=timestamp * 0.1)
		elif browser_name == 'Safari':
			date = datetime(2001, 1, 1) + timedelta(seconds=timestamp)
		elif browser_name == 'Firefox':
			date = datetime.fromtimestamp(timestamp / 1000000)
		else:
			date = datetime.fromtimestamp(timestamp)
		return str(date)



# WebCachev01.dat path: %LocalAppData%\Microsoft\Windows\WebCache\WebCacheV01.dat
def extract_webcachev01_dat(file_path):
	"""Extracts data from WebCacheVxx.dat.
	"""
	visits = []
	esedb_file = pyesedb.file()
	with open(file_path, "rb") as f:
		esedb_file.open_file_object(f) # read the file 
		containers_table = esedb_file.get_table_by_name("Containers") # look for tables "Containers"
		if containers_table is None:
			esedb_file.close()
			return visits
			
		for i in range(0, containers_table.get_number_of_records()):
			if containers_table.get_record(i).get_value_data_as_string(8) == 'History': # only look for History containers
				container_id = containers_table.get_record(i).get_value_data_as_integer(0)
				history_table = esedb_file.get_table_by_name("Container_" + str(container_id)) # get the container by its ID 
				for j in range(0, history_table.get_number_of_records()):	# for each record in the container table
						record = {}
						for v in range(0 , history_table.get_record(j).get_number_of_values()): # for each value in the record
							column_name = history_table.get_record(j).get_column_name(v) # get the current column name
							column_type = history_table.get_record(j).get_column_type(v) # get the current column type number

							if column_type == 12 :	# column is string
								record[column_name] = history_table.get_record(j).get_value_data_as_string(v)

							elif column_type == 15 or column_type == 14: # column is int
								if column_name in ["SyncTime" , "CreationTime" , "ExpiryTime" , "ModifiedTime" , "AccessedTime"]:
									record[column_name] = convert_timestamp( history_table.get_record(j).get_value_data_as_integer(v) , browser_name='IE11', tz='utc')
								else:
									record[column_name] = history_table.get_record(j).get_value_data_as_integer(v)

							elif column_type == 11: # column is hex
								if history_table.get_record(j).get_value_data(v) is not None:
									h = [ord(x) for x in history_table.get_record(j).get_value_data(v)]
									record[column_name] = ''.join('{:02x} '.format(x) for x in h)
								else:
									record[column_name] = history_table.get_record(j).get_value_data(v)

							else:
								record[column_name] = history_table.get_record(j).get_value_data(v)
						 
						record["@timestamp"] = record["AccessedTime"].replace(" " , "T")
						record["browser_name"] = "Internet Explorer"
						record["type"] = "visits"
						link = record['Url'].split('@' , 1)
						if len(link) == 1:
							record['link'] = link[0]
						else:
							record['link'] = link[1]
						
						record['time'] = record['AccessedTime']

						for k in record.keys():
							if k in ["UrlHash" , "Type"]:
								record[k] = str(record[k])
							if record[k] is None:
								record[k] = "None"
						visits.append(record)

		esedb_file.close()

	return visits


# places.sqlite path: C:\Users\<user-name>\AppData\Roaming\Mozilla\Firefox\Profiles\<profile-id>.default\places.sqlite 
def extract_firefox_history(file_path):
	#print file_path
	conn = sqlite3.connect(file_path)
	c = conn.cursor()
	his = []
	
	# get all columns
	columns = {"origins" : [] , "places" : [] , "annos" : [] , "visits" : [] , "anno_attr" : []}
	for d in c.execute('PRAGMA table_info(moz_origins)'):
		columns["origins"].append(  d[1] )
	for d in c.execute('PRAGMA table_info(moz_places)'):
		columns["places"].append(  d[1] )
	for d in c.execute('PRAGMA table_info(moz_annos)'):
		columns["annos"].append(  d[1] )
	for d in c.execute('PRAGMA table_info(moz_anno_attributes)'):
		columns["anno_attr"].append(  d[1] )
	for d in c.execute('PRAGMA table_info(moz_historyvisits)'):
		columns["visits"].append(  d[1] )

	# get the origins
	origins = []
	if 'moz_origins' in columns.keys():
		for org in c.execute('SELECT * FROM moz_origins'):
			origin = {}
			for o in range(0 , len(org)):
				origin[ columns["origins"][o] ] = org[o]

			origins.append(origin)

	
	# get all places
	places = []
	for place in c.execute('SELECT * FROM moz_places'):
		plc = {}
		for p in range(0 , len(place)):
			plc[ columns["places"][p] ] = place[p]

		places.append(plc)

	# get all annos
	annos = []
	for anno in c.execute('SELECT * FROM moz_annos'):
		an = {}
		for a in range(0 , len(anno)):
			an[ columns["annos"][a] ] = anno[a]

		annos.append(an)

	# get all annos_attr
	annos_attr = []
	for anno in c.execute('SELECT * FROM moz_anno_attributes'):
		an = {}
		for a in range(0 , len(anno)):
			an[ columns["anno_attr"][a] ] = anno[a]

		annos_attr.append(an)

	# get all visits
	visits = []
	for visit in c.execute('SELECT * FROM moz_historyvisits'):
		v = {}
		for i in range(0 , len(visit)):
			v[ columns["visits"][i] ] = visit[i]

		visits.append(v)


	visit_type = [
		"TRANSITION_LINK" , 
		"TRANSITION_TYPED" ,
		'TRANSITION_BOOKMARK' ,
		'TRANSITION_EMBED' ,
		'TRANSITION_REDIRECT_PERMANENT' ,
		'TRANSITION_REDIRECT_TEMPORARY' ,
		'TRANSITION_DOWNLOAD',
		'TRANSITION_FRAMED_LINK'
	]
	for visit in visits:
		# add the record type 
		visit["visit_type"] = visit_type[ visit["visit_type"]-1 ]
		if visit["visit_type"] == 'TRANSITION_DOWNLOAD':
			visit["type"] = "downloads"
		else:
			visit["type"] = "visits"

		# add places to the record
		for p in places:
			if p['id'] == visit['place_id']:
				for place in p.keys():
					visit["p_" + place] = p[place]


		# add origins to the record
		for o in origins:
			if o['id'] == visit['p_origin_id']:
				for origin in o.keys():
					visit["o_" + origin] = o[origin]


		# add annos to the record
		for a in annos:
			if a['place_id'] == visit['p_id']:
				if 'annos' not in visit.keys():
					visit['annos'] = {}
				visit_anno = {}
				for anno in a.keys():
					visit_anno["a_" + anno] = a[anno]

				# get the annos attributes
				for a_a in annos_attr:
					if visit_anno['a_anno_attribute_id'] == a_a['id']:
						visit_anno["a_anno_attr"] = a_a['name']

				visit['annos'][ len(visit['annos']) ] = visit_anno

		# fix the records fields 
		for k in visit.keys():
			if k in ["p_last_visit_date" , "visit_date"]:
				visit[k] = convert_timestamp(visit[k] , browser_name='Firefox', tz='utc') # convert the times 
			if k in ["p_url_hash"]:
				visit[k] = str(visit[k])
		

		if 'annos' in visit.keys():
			for anno in range( 0 , len( visit['annos'] )):
				for k in visit['annos'][anno].keys():
					if k in ["a_lastModified",  "a_dateAdded"]:
						visit['annos'][anno][k] = convert_timestamp(visit['annos'][anno][k] , browser_name='Firefox', tz='utc') # convert the times

		# define the timestamp, browser_name, link, and time fields
		visit["@timestamp"] = visit["visit_date"].replace(" " , "T")
		visit["browser_name"] = "Firefox"
		visit['link'] = visit['p_url'] 
		visit['time'] = visit['visit_date']

		# change None values
		for k in visit.keys():
			if visit[k] is None:
				visit[k] = "None"

			



	return visits


# History path: %LocalAppData%\Google\Chrome\User Data\Default\History
def extract_chrome_history(file_path):
	#print file_path
	conn = sqlite3.connect(file_path)
	c = conn.cursor()
	his = []
	
	# get downloads
	columns = []  # get columns names
	url_chain = []

	for d in c.execute('PRAGMA table_info(downloads)'):
		columns.append( (d[1] , d[2]) ) # get columns names 
	
	for download in c.execute('SELECT * FROM downloads_url_chains'):
		url_chain.append(download)		# get all url chains

	# for each download element
	for download in c.execute('SELECT * FROM downloads'):
		downloads = {
			"type" : "downloads" , 
			"browser_name" : "chrome"
		}
		# add in the list
		for i in range( 0 , len(download)):
			if columns[i][0] in ["start_time" , "end_time" , "last_access_time"]:
				downloads[columns[i][0]] = convert_timestamp(download[i] , browser_name='Chrome', tz='utc')
			elif type(download[i]) is int or download[i] is None:
				downloads[columns[i][0]] = download[i]
			else:
				downloads[columns[i][0]] = download[i]

		for i in url_chain:
			if i[0] == downloads['id']:
				if 'url_chain' not in downloads.keys():
					downloads['url_chain'] = {}
				downloads['url_chain'][ len(downloads['url_chain']) ] = i[2]


		
		his.append(downloads) # add to history logs

	# get visits history
	columns = {"urls" : [] , "visits" : [] , "keyword_search_terms" : [] , "segments" : []}
	for d in c.execute('PRAGMA table_info(urls)'):
		columns["urls"].append(d[1])
	for d in c.execute('PRAGMA table_info(visits)'):
		columns["visits"].append(d[1])
	for d in c.execute('PRAGMA table_info(keyword_search_terms)'):
		columns["keyword_search_terms"].append(d[1])
	for d in c.execute('PRAGMA table_info(segments)'):
		columns["segments"].append( d[1])
	

	# get all visits
	for visits in c.execute('SELECT * FROM visits'):
		visit =  {"type" : "visits" ,"browser_name": "chrome"}
		for v in range( 0 , len(visits)):
				
			if columns["visits"][v] in ["visit_time" ]:
				visit[ columns["visits"][v] ] = convert_timestamp(visits[v] , browser_name='Chrome', tz='utc')						
			else:
				visit[ columns["visits"][v] ] = visits[v]

		
		his.append(visit)

	# get the url for each visit
	urls = []
	for url in c.execute('SELECT * FROM urls' ):
		url_dic = {}
		for u in range(0 , len(url)):
			if type(url[u]) is unicode:
				url_dic[ columns['urls'][u] ] = u''.join(url[u].split())
			elif columns['urls'][u] in ["last_visit_time"]:
				url_dic[ columns['urls'][u] ] = convert_timestamp(url[u] , browser_name='Chrome', tz='utc')
			else:
				url_dic[ columns['urls'][u] ] = url[u]
		urls.append(url_dic)

	# add the url details to the visit
	for visit in his:
		if visit["type"] != "visits": # only check the urls, not downloads
			continue
		for u in urls:
			if u["id"] == visit['url']: 
				for k in u.keys():
					visit["url_" + k] = u[k]


	# get all keyword_search_terms for each url 
	for url in his:
		if url["type"] != "visits": # only check the urls, not downloads
			continue
		
		for terms in c.execute('SELECT * FROM keyword_search_terms WHERE url_id='+str(url['url']) ):
			url["keyword_search_terms"] = {}
			term = {}
			for t in range( 0 , len(terms)):
				if type(terms[t]) is unicode:
					term[ columns['keyword_search_terms'][t] ] = u''.join(terms[t].split())
				else:
					term[ columns["keyword_search_terms"][t] ] = terms[t]
			url["keyword_search_terms"][ len(url["keyword_search_terms"]) ] = term

	# get all segments for each url
	for url in his:
		if url["type"] != "visits": # only check the urls, not downloads
			continue

		
		for segments in c.execute('SELECT * FROM segments WHERE url_id='+str(url['url']) ):
			url["segments"] = {}
			segment = {}
			for s in range( 0 , len(segments)):
				if type(segments[s]) is unicode:
					segment[ columns['segments'][s] ] = u''.join(segments[s].split())
				else:
					segment[ columns["segments"][s] ] = segments[s]
			url["segments"][ len(url["segments"]) ] = segment
	

	# get the time, link, and timestamp fields
	for i in his:
		if i['type'] == "visits":
			i['link'] = i['url_url'] 
			i['time'] = i['visit_time']
		else:
			i['link'] = i['url_chain'][0] 
			i['time'] = i['start_time']

		i["@timestamp"] = i['time'].replace(" " , "T")

		# fix the fields from int to string and None value fields
		for k in i.keys():
			if k in ["transition" , "visit_duration"]:
				i[k] = str(i[k])
			if i[k] is None:
				i[k] = "None"

	return his


"""

h = []
if browser == "chrome":
	h = h + extract_chrome_history(path)
elif browser == "IE":
	h = h + extract_webcachev01_dat(path)
elif browser == "firefox":
	h = h + extract_firefox_history(path)
else:
	print "[-] Make sure to specify the browser name"

print json_beautifier(h)

if len(h) > 0:
	push_to_elk( es_link , es_index , h)
else:
	print "[-] There are not web history to parse"


"""