import  json, os
import requests
import sys
import subprocess 
import yaml 


from elasticsearch import Elasticsearch
from elasticsearch import helpers



# get configuration
y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )


reload(sys)
sys.setdefaultencoding('utf8')



# =================================================
#               Helper Function
# =================================================

# ================================ return json in a beautifier
def json_beautifier(js):
	return json.dumps(js, indent=4, sort_keys=True)



# ================================ update json failed
# get a json variable, path, and new value
def json_update_val_by_path(j , p , v):
    if p == '':
        return v
    p_l = p.split('.')
    k = p_l[0]
    a = json_update_val_by_path( j[k] , '.'.join(p_l[1:]) , v)
    j[k] = a
    return j



# =================================================
#               Database Elasticsearch
# =================================================

def get_es():
	return ES_DB(y['ElasticSearch']["IP"] ,str( y['ElasticSearch']['PORT'] ) )

class ES_DB:

	es_db 	= None

	# ================================ initializer
	def __init__(self, es_ip , es_port):
		self.es_ip = es_ip
		self.es_port = es_port
		self.es_db = Elasticsearch('http://'+self.es_ip+':' + self.es_port)


	# ================================ Create Index
	# create new index (case)
	def create_index(self, index_name):
		try:
			self.es_db.indices.create(index=index_name, ignore=400)
			self.es_db.indices.put_settings(index=index_name , body='{"index.mapper.dynamic": "false"}')
			return [ True, index_name]
		except Exception as e:
			return [False , "Error: " + str(e)]


	# ================================ Delete Index
	# delete index (case) 
	def delete_index(self , index_name):
		try:
			self.es_db.indices.delete(index=index_name, ignore=400)
			return [True , index_name]
		except Exception as e:
			return [False, "Error: " + str(e)]


	# ================================ get max results window
	# get the setting for maximum number of records to be retrived from elasticsearch
	def get_max_result_window(self,  indx):
		settings = self.es_db.indices.get_settings(index=indx)
		settings = settings[indx]['settings']['index']
		if "max_result_window" in settings.keys():
			return settings['max_result_window']
		else:
			return 10000 # default value


	# ================================ query
	# query the elasticsearch db, index is the index name of the case, and body is the query body
	def query(self, indexname , body):
		print "[+] Elasticsearch Query on index ["+indexname+"]"
		print "[+] Body: " + json.dumps(body)
		indexname = indexname.lower()

		try:
			res= {'result' : True, 'data' : self.es_db.search(index=indexname,body=body) }
		except:
			res = {'result' : False , 'data' : 'unknown error' } 
			error = sys.exc_info()
			error = error[1][2]
			print error
			print "[-] Error: "  + str(error['status'])
			print "[-] Reason: " + error['error']['root_cause'][0]['reason']

			# error if the number if fields to search for excced 10000
			if "Result window is too large" in error['error']['root_cause'][0]['reason']:
				max_result_window = int(self.get_max_result_window(indexname))
				max_result_window = max_result_window + 10000
				inc = self.es_db.indices.put_settings(index=indexname , body='{ "index" : { "max_result_window" : ' + str(max_result_window) + ' } }')
				
				if inc["acknowledged"]:
					print "[+] result window increased to " + str(self.get_max_result_window(indexname))
					res = self.query(indexname , body)
				else:
					print "[-] Could not increase the result window size"

			# if want to sort over text fields while it needs keyword
			if "Fielddata is disabled on text fields by default" in error['error']['root_cause'][0]['reason']:
				print  json_beautifier(error)
				field = error['error']['root_cause'][0]['reason'].split('[')[1].split(']')[0]
				body['sort'][field + '.keyword'] = body['sort'][field]
				del body['sort'][field]
				res = self.query(indexname , body)

			# if there is no index for the case
			if "no such index" in error['error']['root_cause'][0]['reason']:
				res= {'result' : False , 'data' : "no such index"}

			# if there is no mapping for specifc field
			if "No mapping found for" in  error['error']['root_cause'][0]['reason']:
				res= {'result' : False , 'data' : error['error']['root_cause'][0]['reason'] }
		return res

	# ================================ get max fields limit
	# get the total_fields.limit from settings
	def get_total_fields_limit(self, indx):
		settings = self.es_db.indices.get_settings(index=indx)
		if 'mapping' in settings[settings.keys()[0]]['settings']['index']:
			if 'total_fields' in settings[settings.keys()[0]]['settings']['index']['mapping']:
				if 'limit' in settings[settings.keys()[0]]['settings']['index']['mapping']['total_fields']:
					return settings[settings.keys()[0]]['settings']['index']['mapping']['total_fields']['limit']
		return 1000 # default fields limit



	# ================================ push records to elasticsearch
	# data: is a list of json data 
	def bulk_queue_push(self, data , case_id , source = None , machine = None , data_type = None, data_path = None):
		case_id = case_id.lower()
		bulk_queue = []
		for d in data:
			di = {
				"_index": case_id,
				"_type": 'None',
				"_source": { "Data" : d }
			}
			if source is not None:
				di['_source']['data_source'] = source
			if machine is not None:
				di['_source']['machine'] = machine
			if data_type is not None:
				di['_source']['data_type'] = data_type
			if data_path is not None:
				di['_source']['data_path'] = data_path
				
			bulk_queue.append(di)
		
		push_es = self.bulk_to_elasticsearch( bulk_queue , case_id )
		if push_es[0]:
			return [ True , "Pushed ["+str(len(bulk_queue))+"] records"]
		else:
			return [ False, 'Failed to bulk data to Elasticsearch: ' + str(push_es[1])]


	# ================================ push records to elasticsearch
	def bulk_to_elasticsearch(self,  bulk_queue, indx):	
		
		try:
			# use helpers to push the data to elasticsearch
			helpers.bulk(self.es_db, bulk_queue)
			return [True , "Pushed ["+str(len(bulk_queue))+"] records to ["+indx+"] index"]

		except Exception as e:
			
			# get the error message and print it
			error = sys.exc_info()
			smg = error[1][0]
			ret = [False , "Error: " + str(smg)] # the value to return if fixing the issue not successed
			print ret
			# rebuild only the failed records to avoid retring push all the records again
			bulk_queue = []
			
			for err in error[1][1]:
				status = err["index"]["status"]
				reason = err["index"]["error"]["reason"]		
				print "[-] Status: " + str(status)
				print "[-] Reason: " + reason
				
				# if the error is the limitation on the fields number, get the add 1000 to the limitation and try again
				if "Limit of total fields" in reason:
					new_limit = int(self.get_total_fields_limit(indx))
					new_limit = new_limit + 1000
					inc = self.es_db.indices.put_settings(index=indx , body='{"index.mapping.total_fields.limit": '+str(new_limit)+'}')
					
					if inc["acknowledged"]:
						print '[+] The total_fields.limit has been increased to ' + str(new_limit)
					else:
						return [ False , "Error in increasing the total_failds limitation"]
					
				
				# if the field is Date type and provided data is not date
				if "failed to parse field" in reason and "of type [date]" in reason:
					d = err['index']['data']
					failed_field = reason.split('[')[1].split(']')[0] # get the field that failed
					d = json_update_val_by_path( d , failed_field , '1700-01-01T00:00:00' )
					bulk_queue.append({
						"_index": err['index']['_index'],
						"_type": err['index']['_type'],
						"_id" : err['index']['_id'],
						"_source": d
					})	
				
				# object mapping for [Data.Event.EventData] tried to parse field [EventData] as object, but found a concrete value
				# if the field of type object and a value string assigned to it, convert it to null
				if "tried to parse field " in reason and "as object, but found a concrete value" in reason:
					d = err['index']['data']
					failed_field = reason.split('[')[1].split(']')[0] # get the field that failed
					d = json_update_val_by_path( d , failed_field , None )
					bulk_queue.append({
						"_index": err['index']['_index'],
						"_type": err['index']['_type'],
						"_id" : err['index']['_id'],
						"_source": d
					})	
					
			ret = self.bulk_to_elasticsearch( bulk_queue, indx)
			return ret

  





	# ================================ push records to elasticsearch
	# update specific record in elasticsearch
	def update_field(self, data , doc_id , indx):
		indx = indx.lower()

		up = self.es_db.update(index = indx ,doc_type='None', id=doc_id , body = data )
		if up['result'] == 'updated':
			return True
		else :
			return False


	# ================================ add tag
	def es_add_tag(self, data , case_id ):
		case_id = case_id.lower()
		ins = self.es_db.index(index=case_id , doc_type = "None" , body = data )
		return ins

	# ================================ get record
	# get specific record by its id 
	def get_record_by_id(self, case_id , record_id):
		case_id = case_id.lower()

		try:
			res = self.es_db.get(index = case_id , doc_type = "None" , id=record_id )
			return res
		except:
			return False

	
	# ================================ Delete record
	# delete records by id 
	def del_record_by_id(self, case_id , record_id):
		case_id = case_id.lower()
		try:
			res = self.es_db.delete(index = case_id , doc_type = "None" , id=record_id)
			if res['result'] == 'deleted':
				return True
			else:
				return False
		except:
			return False

	# ================================ Delete record
	# delete records by query
	def del_record_by_query(self, case_id , query):
		case_id = case_id.lower()
		
		try:
			try:
				res = self.es_db.delete_by_query(index = case_id , doc_type = "None" ,  body=query)
			except Exception as e:
				return False
			return True
		except:
			return False



	# ================================ Get fields mapping
	# return the fields mapping (all fields and its properties)
	def get_mapping_fields(self, case_id):
		fields = self.es_db.indices.get_mapping(index=case_id)[case_id]['mappings']['None']['properties']
		fields_list = self.get_mapping_fields_rec(fields)
		return fields_list

	# recursive function for get_mapping_fields
	def get_mapping_fields_rec(self, fields ,current_path=[]):
		fields_list = []
		for k in fields.keys():
			if 'properties' in fields[k].keys():
				fields_list += self.get_mapping_fields_rec( fields[k]['properties'] , current_path + [k] )
			else:
				current_path_tmp = '.'.join( current_path )
				if len(current_path) > 0:
					current_path_tmp += "."

				#print k + ":" + json_beautifier(fields[k])
				r = {
					'type': 		fields[k]['type'],
					'field_path' : 	current_path_tmp + k,
					'fields' : 		fields[k]['fields'].keys()[0] if 'fields' in fields[k].keys() else ''
				}
				fields_list.append( r )
		return fields_list









db_es               = get_es()
