import  json, os
import requests
import sys
import subprocess 
import yaml 
import re 
import uuid

import inspect

from app import logger 

from elasticsearch import Elasticsearch
import elasticsearch
from elasticsearch import helpers

from datetime import datetime 

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
def json_update_val_by_path(j , p , val):
    try:
        p_l = p.split('.')
        if len(p_l) == 1:
            j[p] = val
            return [True , val]
        k = p_l[0]
        if k not in j.keys():
            return [False, "Key ["+str(k)+"] not in the json"]
            
        a = json_update_val_by_path( j[k] , '.'.join(p_l[1:]) , val)
        if a[0]:
            return [True , "update"]
        else:
            return a
    except Exception as e:
        return [False , str(e)]
        
# ================================ update json failed
# get the value of specific 
def json_get_val_by_path(j , p):
    try:
        p_l = p.split('.')
        if len(p_l) == 1:
            return [True, j[p] ]
        k = p_l[0]
        if k not in j.keys():
            return [False, "Key ["+str(k)+"] not in the json"]
            
        return json_get_val_by_path( j[k] , '.'.join(p_l[1:]))
    except Exception as e:
        return [False , str(e)]

# =================================================
#               Database Elasticsearch
# =================================================

def get_es():
    return ES_DB(y['ElasticSearch']["IP"] ,str( y['ElasticSearch']['PORT'] ) )

class ES_DB:

    es_db     = None

    # ================================ initializer
    def __init__(self, es_ip , es_port):
        self.es_ip = es_ip
        self.es_port = es_port
        self.es_db = Elasticsearch('http://'+self.es_ip+':' + self.es_port , timeout=120)
        #print inspect.getargspec(self.es_db.indices.put_settings())
        # setting 

    # ================================ Create Index
    # create new index (case)
    def create_index(self, index_name):
        try:
            self.es_db.indices.create(index=index_name , body={
                    "mappings": {
                        "dynamic_templates": [
                            {
                            "strings": {
                                "match_mapping_type": "string",
                                "mapping": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type":  "keyword",
                                            "ignore_above": 256
                                        }
                                    },
                                    "copy_to": "catch_all"
                                }
                            }
                            }
                        ]
                    },
                    "settings": {
                        "analysis": {
                            "analyzer": {
                                "default": { 
                                    "tokenizer":"keyword",
                                    "filter" : ["lowercase"]
                                },
                                "default_search": {
                                    "tokenizer":"keyword",
                                    "filter" : ["lowercase"]
                                }
                            }
                        }
                    }
                })
            return [ True, index_name]
        except Exception as e:
            return [False , "Error: " + str(e)]


    # ================================ Delete Index
    # delete index (case) 
    def delete_index(self , index_name):
        try:
            self.es_db.indices.delete(index=index_name)
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



    # ================================ get max results window
    # get the setting for maximum number of records to be retrived from elasticsearch
    def get_max_fields_num(self,  indx):
        settings = self.es_db.indices.get_settings(index=indx)
        settings = settings[indx]['settings']['index']
        if "query" in settings.keys():
            if "default_field" in settings['query']:
                return settings['query']['default_field']
        else:
            return 1024 # default value

    # ================================ bulk query
    # this except index and bodies (list of single body requests)
    def multiqueries(self, index , bodies):
        request_header = json.dumps({'index': index})
        requests = []
        for b in bodies:
            b["track_total_hits"] = True
            requests.extend([request_header , b])
        resp = self.es_db.msearch(body=requests)

        # check if there are failed queries
        for result in resp["responses"]:
            if "error" in result.keys():
                return [False , result["error"]["root_cause"][0]["reason"]]
        return [True,  resp['responses']]


    # ================================ query
    # query the elasticsearch db, index is the index name of the case, and body is the query body
    # count: number of times the function recursive
    def query(self, indexname , body , count=3):
        count -=1
        
        indexname = indexname.lower()
        body["track_total_hits"] = True
        logger.logger(level=logger.DEBUG , type="elasticsearch", message="Query to index ["+indexname+"]", reason=json.dumps(body))
        filter_path=['hits.hits._source.Data' , 'hits.total.value' , 'aggregations.*.buckets']
        try:
            #search_res = self.es_db.search(index=indexname,body=body , filter_path=filter_path)
            search_res = self.es_db.search(index=indexname , body=body)
            return [True, search_res]
        except elasticsearch.RequestError as e:
            reason = e.info['error']['reason']
            logger.logger(level=logger.WARNING , type="elasticsearch", message="Query ["+indexname+"] failed [RequestError]" , reason=reason)
            # if the problem in shards
            if reason == "all shards failed":
                for shard in e.info['error']['failed_shards']:
                    if 'caused_by' in shard['reason'].keys():
                        shard_reason = shard['reason']['caused_by']['reason']
                    else:
                        shard_reason = shard['reason']['reason']



                    # if the reason is that the field used for key is text and is not sortable, then try it sub-field ".keyword" 
                    if shard_reason.startswith("Text fields are not optimised for operations that require per-document field data like aggregations and sorting, so these operations are disabled by default"):
                        if "sort" in body.keys():
                            field = body['sort'].keys()[0]
                            order = body['sort'][field]['order']
                            body['sort'] = {
                                field + ".keyword" : {
                                    'order' : order
                                }
                            }


                            logger.logger(level=logger.INFO , type="elasticsearch", message="Query ["+indexname+"], the sort is not a sortable field, try using sub-field .keyword")
                            return self.query(indexname , body , count)



                    # if the reason is the result has too many fields
                    match = re.match('field expansion (for \[.*\] )?matches too many fields, limit: ([0-9]+), got: ([0-9]+)' , shard_reason)
                    if match is not None:
                        # if the problem is the number of fields more than the default max number of fields in query
                        max_field_num = int(match.groups()[1]) + 100

                        inc = self.es_db.indices.put_settings(index=indexname , body='{ "index" : { "query": { "default_field" : '+str(max_field_num)+'} } }')
                        if inc["acknowledged"]:
                            logger.logger(level=logger.INFO , type="elasticsearch", message="Query ["+indexname+"] max query fields number increased " + str(max_field_num))
                            if count != 0:
                                return self.query(indexname , body , count)
                            else:
                                return [False, "exceeded the number of tries to fix the issue, field expansion matches too many fields"]
                        else:
                            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] Failed increasing the result window")
                            continue
                    
                    # if the result window is too large, increase the window
                    match = re.match('Result window is too large, from \+ size must be less than or equal to: \[([0-9]+)\] but was \[([0-9]+)\].*' , shard_reason)
                    if match is not None:
                        max_result_window = int(match.groups()[1]) + 1000
                        inc = self.es_db.indices.put_settings(index=indexname , body='{ "index" : { "max_result_window" : ' + str(max_result_window) + ' } }')
                        if inc["acknowledged"]:
                            logger.logger(level=logger.INFO , type="elasticsearch", message="Query ["+indexname+"] result window increased to " + str(self.get_max_result_window(indexname)))
                            if count != 0:
                                return self.query(indexname , body , count)
                            else:
                                return [False, "exceeded the number of tries to fix the issue, Result window is too large"]
                        else:
                            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] Failed increasing the result window")
                            continue

                    else:
                        logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [RequestError]" , reason=shard_reason)
            else:
                logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [RequestError]" , reason=json.dumps(e.info))
            res = [False, reason]
        except elasticsearch.ConnectionError as e:
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [ConnectionError]" , reason=e.info)
            res = [False, 'Failed to connect to elasticsearch']
        except elasticsearch.TransportError as e:
            reason = str(e)
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [TransportError]" , reason=reason)
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [TransportError]" , reason=json.dumps(e.info))
            res = [False, reason]
        except elasticsearch.ElasticsearchException as e:
            reason = str(e)
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [ElasticsearchException]" , reason=reason)
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [ElasticsearchException]" , reason=json.dumps(e.info))
            res = [False, reason]
        except Exception as e:
            print str(e)
            res = [False, str(e)] 
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Query ["+indexname+"] failed [Exception]" , reason=str(e))

            
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
    def bulk_queue_push(self, data , case_id , source = None , machine = None , data_type = None, data_path = None , chunk_size=500,kjson=False):
        case_id = case_id.lower()
        bulk_queue = []

        for d in data:
            di = {
                "_index": case_id,
                "_source": {},
                '_id' : str(uuid.uuid4())
            }

            di['_source']['Data'] = d['Data'] if kjson else d
            source                = d['data_source'] if kjson else source
            data_type             = d['data_type'] if kjson else data_type
            data_path             = d['data_path'] if kjson else data_path

            if source is not None:
                di['_source']['data_source'] = source
            if machine is not None:
                di['_source']['machine'] = machine
            if data_type is not None:
                di['_source']['data_type'] = data_type
            if data_path is not None:
                di['_source']['data_path'] = data_path
                
            bulk_queue.append(di)
        
        
        logger.logger(level=logger.DEBUG , type="elasticsearch", message="Index ["+case_id+"]: Pushing ["+str(len(bulk_queue))+"] records")

        push_es = self.bulk_to_elasticsearch( bulk_queue , case_id , chunk_size )
        if push_es[0]:
            logger.logger(level=logger.INFO , type="elasticsearch", message="Index ["+case_id+"]: Pushed ["+str(len(bulk_queue) - len(push_es[2]))+"] records successfully")
            return [ True , "Pushed ["+str(len(bulk_queue))+"] records" , push_es[2] , push_es[3]]
        else:
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Index ["+case_id+"]: Failed pusheing ["+str(len(bulk_queue))+"] records" , reason=push_es[1])
            return [ False, 'Failed to bulk data to Elasticsearch: ' + str(push_es[1]) , bulk_queue , push_es[3]]
            


    # ================================ push records to elasticsearch
    # return list of records ids successed or failed
    def bulk_to_elasticsearch(self,  bulk_queue, indx , chunk_size):    
        
        try:
            errors = {} # contain dictionary of failed data (origin data and error info)
            failed = [] # contain the IDs of the failed records
            successed = [] # contain the IDs of successed records

            logger.logger(level=logger.DEBUG , type="elasticsearch", message="Index ["+indx+"]: bulk push to ES, default chunk["+str(chunk_size)+"]: " , reason="number of records: " + str(len(bulk_queue)))
            # use helpers to push the data to elasticsearch
            for ok, item in helpers.parallel_bulk(self.es_db, bulk_queue, chunk_size=chunk_size,raise_on_error=False, raise_on_exception=False):
                if not ok:
                    errors[item['index']['_id']] = item
                    logger.logger(level=logger.WARNING , type="elasticsearch", message="Index ["+indx+"]: Failed pushing record: " , reason=str(item))
                    failed.append(item['index']['_id']) 
                else:
                    successed.append(item['index']['_id'])


            if len(failed):
                logger.logger(level=logger.WARNING , type="elasticsearch", message="Index ["+indx+"]: Failed pushing ["+str(len(failed))+"] records, try to fix the issue")
                # get origin data from ID
                for data in bulk_queue:
                    try:
                        errors[data['_id']]['index']['data'] = data['_source']   
                        logger.logger(level=logger.DEBUG , type="elasticsearch", message="Index ["+indx+"]: get data for failed record ["+data['_id']+"]", reason=str(errors[data['_id']]))
                    except:
                        # if record not in the errors list, continue
                        continue
                    logger.logger(level=logger.WARNING , type="elasticsearch", message="Index ["+indx+"]: Failed pushing record: " , reason=str(data['_id']))

                fixed_errors,nonfixed_errors = self.bulk_to_elasticsearch_fix_errors(indx , errors)
                failed = nonfixed_errors
                if len(fixed_errors):
                    logger.logger(level=logger.DEBUG , type="elasticsearch", message="Index ["+indx+"]: fixed issue of ["+str(len(fixed_errors))+"] records, retry to push it")
                    repush_failed_errors = self.bulk_to_elasticsearch(fixed_errors , indx , chunk_size)
                    if repush_failed_errors[0]:
                        successed += repush_failed_errors[3]
                        failed += repush_failed_errors[2]
                    

            return [True , "Pushed ["+str(len(successed))+"] records to ["+indx+"] index" , failed , successed]


        # if connection timeout to elasticsearch occurred
        except elasticsearch.exceptions.ConnectionTimeout as e:
            logger.logger(level=logger.WARNING , type="elasticsearch", message="Index ["+indx+"]: Failed to push the records, retry again" , reason="Connection to Elasticsearch timeout")
            return self.bulk_to_elasticsearch( bulk_queue, indx , chunk_size)


        except Exception as e:
            logger.logger(level=logger.ERROR , type="elasticsearch", message="Failed pushing the records, unexpected error" , reason=str(e))
            
            return [False , "Failed pushing ["+str(len(bulk_queue))+"] records to ["+indx+"] index" , bulk_queue , [] ]

    
    # ================================ fix the errors faced during build_to_elasticsearch
    # this will recevie the failed data from bulk queue and fix it
    # it will return the list of fixed records and nonfixed records
    def bulk_to_elasticsearch_fix_errors(self, indx, errors):
        logger.logger(level=logger.WARNING , type="elasticsearch", message="Index ["+indx+"]: Failed pushing ["+str(len(errors))+"] records [BulkIndexError], retry to fix the issue")

        # check the returned error for each document and try to solve it
        fixed_data              = []
        nonfixed_data           = []
        limit_fields_increased  = False
        for _id, doc in errors.iteritems():
            
            record_msg_info = "Indx["+indx+"]"
            if 'machine' in doc['index']['data'].keys():
                record_msg_info += ", machine ["+doc['index']['data']['machine'] + "]"
            if 'data_type' in doc['index']['data'].keys():
                record_msg_info += ", data_type["+doc['index']['data']['data_type']+"]"
            if '_id' in doc['index'].keys():
                record_msg_info += ", rec_id["+doc['index']['_id']+"]"

            try:
                

                doc_reason = doc['index']['error']['reason']
                logger.logger(level=logger.WARNING , type="elasticsearch", message=record_msg_info + ": record failed" , reason=doc_reason)
                
                # === if the error is the limitation on the fields number, get the add 1000 to the limitation and try again
                if "Limit of total fields" in doc_reason and limit_fields_increased == False:
                    new_limit = int(self.get_total_fields_limit(indx))
                    new_limit = new_limit + 1000
                    inc = self.es_db.indices.put_settings(index=indx , body='{"index.mapping.total_fields.limit": '+str(new_limit)+'}')
                    
                    if inc["acknowledged"]:
                        logger.logger(level=logger.INFO , type="elasticsearch", message=record_msg_info +" : The total_fields.limit has been increased to " + str(new_limit))
                        limit_fields_increased = True
                    else:
                        logger.logger(level=logger.ERROR , type="elasticsearch", message=record_msg_info +" : failed to increase total_fields.limit")
                    
                    
                # === if already fixed the limit of total fields issue, then add it to the list
                if "Limit of total fields" in doc_reason and limit_fields_increased:
                    fixed_data.append({
                        "_index": doc['index']['_index'],
                        "_type": doc['index']['_type'],
                        "_id" : doc['index']['_id'],
                        "_source": doc['index']['data']
                    })
                    continue
                
                

                # if there is error where the text field exceeded the maximum number of charactors (by default 32766)
                match = re.match('Document contains at least one immense term in field="(.+)" \(whose UTF8 encoding is longer than the max length ([0-9]+)\), all of which were skipped.* original message: bytes can be at most ([0-9]+) in length; got ([0-9]+)' , doc_reason)
                if match is not None:
                    field = match.groups()[0]
                    current_max = int(match.groups()[1])
                    data_length = int(match.groups()[3])
                    
                    logger.logger(level=logger.ERROR , type="elasticsearch", message=record_msg_info +" : field data more than the specified" , reason="field " + field + ", defined max length ["+str(current_max)+"], field data ["+str(data_length)+"]")
                    



                # ==== check if reason that an object received but the field data type is not correct
                match = re.match("object mapping for \[(.*)\] tried to parse field \[(.*)\] as (.*), but found a concrete value" , doc_reason)
                if match is not None:
                    match = match.groups()
                    failed_field = match[0]

                    # if datatype is object but found concrete value
                    if match[2] == 'object':
                        d = json_get_val_by_path( doc['index']['data'] , failed_field)
                        
                        if d[0]:
                            # if type of field is object but found "None" as string
                            if d[1] == 'None':
                                
                                if json_update_val_by_path( doc['index']['data'] , failed_field , None )[0]:
                                    
                                    fixed_data.append({
                                        "_index": doc['index']['_index'],
                                        "_type": doc['index']['_type'],
                                        "_id" : doc['index']['_id'],
                                        "_source": doc['index']['data']
                                    })   
                                    continue
                            
                            # if type of field is object but found string
                            if isinstance(d[1] , str):
                                if json_update_val_by_path( doc['index']['data'] , failed_field , { 'value' : d[1]} )[0]:
                                    
                                    fixed_data.append({
                                        "_index": doc['index']['_index'],
                                        "_type": doc['index']['_type'],
                                        "_id" : doc['index']['_id'],
                                        "_source": doc['index']['data']
                                    })   
                                    continue

                # ==== failed to parse field as date 
                match = re.match("failed to parse field \[(.*)\] of type \[(.*)\] in document with id .*" , doc_reason)
                if match is not None:
                    match = match.groups()
                    failed_field = match[0]
                    failed_field_type = match[1]
                    
                    # if the field mapped as date 
                    if failed_field_type == 'date':
                        if json_update_val_by_path( doc['index']['data'] , failed_field , '1700-01-01T00:00:00' )[0]:
                            fixed_data.append({
                                "_index": doc['index']['_index'],
                                "_type": doc['index']['_type'],
                                "_id" : doc['index']['_id'],
                                "_source": doc['index']['data']
                            })   
                            continue

                    # if the field mapped as text
                    if failed_field_type == 'text':
                        d = json_get_val_by_path( doc['index']['data'] , failed_field)
                        if d[0]:
                            d=d[1]
                            try:
                                if isinstance(d , list):
                                    res = [0 for x in range(len(d))]
                                    for i in d.keys():
                                        res[int(i)] = d[i]
                                    res_str = '\n'.join(res)
                                    if json_update_val_by_path( doc['index']['data'] , failed_field , res_str )[0]:
                                        fixed_data.append({
                                            "_index": doc['index']['_index'],
                                            "_type": doc['index']['_type'],
                                            "_id" : doc['index']['_id'],
                                            "_source": doc['index']['data']
                                        })   
                                        continue
                                elif isinstance(d , dict):
                                    res_str = "\n".join([str(k) + "=" + str(d[k]) for k in d.keys()])
                                    if json_update_val_by_path( doc['index']['data'] , failed_field , res_str )[0]:
                                        fixed_data.append({
                                            "_index": doc['index']['_index'],
                                            "_type": doc['index']['_type'],
                                            "_id" : doc['index']['_id'],
                                            "_source": doc['index']['data']
                                        })   
                                        continue

                            except Exception as e:
                                pass

                logger.logger(level=logger.ERROR , type="elasticsearch", message=record_msg_info +" : No fix found for failed record ["+doc['index']['_id']+"] data" , reason=doc['index']['data'])
                nonfixed_data.append({
                        "_index": doc['index']['_index'],
                        "_type": doc['index']['_type'],
                        "_id" : doc['index']['_id'],
                        "_source": doc['index']['data']
                    })
            except Exception as e:
                logger.logger(level=logger.ERROR , type="elasticsearch", message=record_msg_info +" : unsuspected error in fixing record issue" , reason=str(e))
                nonfixed_data.append({
                        "_index": doc['index']['_index'],
                        "_type": doc['index']['_type'],
                        "_id" : doc['index']['_id'],
                        "_source": doc['index']['data']
                    })
            



        return fixed_data, nonfixed_data



    # ================================ push records to elasticsearch
    # update specific record in elasticsearch
    def update_field(self, data , doc_id , indx):
        try:
            indx = indx.lower()

            up = self.es_db.update(index = indx , doc_type="_doc", id=doc_id , body = data )
            if up['result'] == 'updated':
                return [True , 'updated']
            else :
                return [False , "Index["+indx+"]: Failed to update the record [" + str(doc_id) + "] : " + str(json.dumps(data))]
        except Exception as e:
            return [False, str(e)]

    # ================================ add tag
    def es_add_tag(self, data , case_id ):
        try:
            case_id = case_id.lower()
            ins = self.es_db.index(index=case_id  , body = data )
            return [True, ins]
        except Exception as e:
            return [False, str(e)]

    # ================================ get record
    # get specific record by its id 
    def get_record_by_id(self, case_id , record_id):
        case_id = case_id.lower()
        try:
            res = self.es_db.get(index = case_id, doc_type="_doc", id=record_id )
            return [True, res]
        except Exception as e:
            return [False , str(e)]

    
    # ================================ Delete record
    # delete records by id 
    def del_record_by_id(self, case_id , record_id):
        case_id = case_id.lower()
        try:
            res = self.es_db.delete(index = case_id, doc_type="_doc" , id=record_id)
            if res['result'] == 'deleted':
                return [True , 'deleted']
            else:
                return [False , "Index["+case_id+"]: Failed to delete the record [" + str(record_id) + "]"]
        except elasticsearch.NotFoundError as e:
            return [False, "NotFound: ["+case_id+"] _id["+record_id+"]"]
        except Exception as e:
            return [False , str(e)]

    # ================================ Delete record
    # delete records by query
    def del_record_by_query(self, case_id , query):
        case_id = case_id.lower()
        
        try:
            res = self.es_db.delete_by_query(index = case_id  ,  body=query)
            return [True, "Indx["+case_id+"]: Deleted " + json.dumps(query)]
        except Exception as e:
            return [False , str(e)]



    # ================================ Get fields mapping
    # return the fields mapping (all fields and its properties)
    def get_mapping_fields(self, case_id):
        try:
            mapping = self.es_db.indices.get_mapping(index=case_id)
            
            if 'properties' in  mapping[case_id]['mappings'].keys():
                fields      = mapping[case_id]['mappings']['properties']
                fields_rec  = self.get_mapping_fields_rec(fields)
                if fields_rec[0] == False:
                    return fields_rec
                else:
                    fields_list = fields_rec[1]
            else: 
                fields_list = []
            
            return [True, fields_list]
        except Exception as e:
            return [False , str(e)]



    # recursive function for get_mapping_fields
    def get_mapping_fields_rec(self, fields ,current_path=[]):
        fields_list = []
        try:
            for k in fields.keys():
                if 'properties' in fields[k].keys():
                    fields_rec  =  self.get_mapping_fields_rec( fields[k]['properties'] , current_path + [k] )
                    if fields_rec[0] == False:
                        return fields_rec
                    else:
                        fields_list += fields_rec[1]
                else:
                    current_path_tmp = '.'.join( current_path )
                    if len(current_path) > 0:
                        current_path_tmp += "."

                    r = {
                        'type':         fields[k]['type'],
                        'field_path' :  current_path_tmp + k,
                        'fields' :      fields[k]['fields'].keys()[0] if 'fields' in fields[k].keys() else ''
                    }
                    fields_list.append( r )
            return [True, fields_list]
        except Exception as e:
            return [False, str(e)]




    # ============================== get System health information
    # return the nodes information
    def get_nodes_info(self):
        try:
            return [True, self.es_db.nodes.info()]
        except Exception as e:
            return [False, str(e)]

    def get_indices_settings(self):
        try:
            return [True , self.es_db.indices.get_settings('*')]
        except Exception as e:
            return [False, str(e)]


    def get_indices_stats(self):
        try:
            return [True, self.es_db.indices.stats('')]
        except Exception as e:
            return [False, str(e)]

    def get_index_count(self, index):
        #print json_beautifier( self.es_db.indices.stats(index) )
        try:
            return [True , self.es_db.cat.count(index, params={"format": "json"})]
        except Exception as e:
            return [False, str(e)]

db_es = get_es()
