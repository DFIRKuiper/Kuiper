# ========================== Descrption
# this script used to collect and push the celery system health
import resources, push_health
import os
import json 
import psutil 
from datetime import datetime 
from elasticsearch import Elasticsearch


# ================================ get max fields limit
# get the total_fields.limit from settings
def get_total_fields_limit(es_db , indx):
    settings = es_db.indices.get_settings(index=indx)
    try:
        return settings[list(settings.keys())[0]]['settings']['index']['mapping']['total_fields']['limit']
    except Exception as e:
        return 1000 # default fields limit

def get_es_info(es_ip , es_port):
    elasticsearch_details = {}
    db_es = Elasticsearch('http://'+es_ip+':' + es_port , timeout=120)

    # collect nodes info
    es_nodes = db_es.nodes.info()

    elasticsearch_details['service_status'] = 'active'

    elasticsearch_details['nodes'] = {
        'nodes_total'       : es_nodes['_nodes']['total'],
        'nodes_successful'  : es_nodes['_nodes']['successful'],
        'nodes_failed'      : es_nodes['_nodes']['failed'],
        'nodes_details'     : []
    } 

    for node in es_nodes['nodes'].keys():
        data = '' if 'data' not in es_nodes['nodes'][node]['settings']['path'].keys() else  ','.join(es_nodes['nodes'][node]['settings']['path']['data'])

        elasticsearch_details['nodes']['nodes_details'].append({
            'name' : node,
            'host' : es_nodes['nodes'][node]['host'],
            'processors' : {
                'allocated' : es_nodes['nodes'][node]['os']['allocated_processors'] , 
                'avaliable': es_nodes['nodes'][node]['os']['available_processors']
            },
            'pid' : es_nodes['nodes'][node]['process']['id'],
            'version' : es_nodes['nodes'][node]['version'],
            'paths' : {
                'data' : data,
                'home' : es_nodes['nodes'][node]['settings']['path']['home'],
                'logs' : es_nodes['nodes'][node]['settings']['path']['logs']
            }

        })
        

    # collect indices info and stats info
    elasticsearch_details['indices'] = {}
    es_indices  = db_es.indices.get_settings('*')
    es_stats    = db_es.indices.stats('')
    
    # indices info 
    
    for indx_name in es_indices.keys():
        
        elasticsearch_details['indices'][indx_name] = {
            'creation_date'         : datetime.fromtimestamp(float(es_indices[indx_name]['settings']['index']['creation_date']) / 1000.).strftime("%Y-%m-%d %H:%M:%S"),
            'uuid'                  : es_indices[indx_name]['settings']['index']['uuid'],
            'total_fields_limit'    : get_total_fields_limit(db_es , indx_name),
            'max_result_window'     : es_indices[indx_name]['settings']['index']['max_result_window'] if 'max_result_window' in es_indices[indx_name]['settings']['index'].keys() else None,
        }

        if indx_name in es_stats['indices']:
            elasticsearch_details['indices'][indx_name]['total_docs'] = es_stats['indices'][indx_name]['total']['docs']['count']
            elasticsearch_details['indices'][indx_name]['disk_size']  = es_stats['indices'][indx_name]['total']['store']['size_in_bytes']
        else:
            elasticsearch_details['indices'][indx_name]['total_docs'] = 0
            elasticsearch_details['indices'][indx_name]['disk_size']  = 0

    # stats info 
    if 'docs' in es_stats['_all']['total']:
        elasticsearch_details['stats'] = {
            'total_docs' : es_stats['_all']['total']['docs']['count'],
            'disk_size' : es_stats['_all']['total']['store']['size_in_bytes'],
        }
    else:
        elasticsearch_details['stats'] = {
            'total_docs' : 0,
            'disk_size' : 0,
        }

    elasticsearch_details['elasticsearch_ip'] = es_ip
    elasticsearch_details['elasticsearch_port'] = es_port


    return elasticsearch_details


ip = os.getenv('ES_IP', "0.0.0.0")
port = os.getenv('ES_PORT', "9200")

info        = get_es_info(es_ip=ip , es_port=port)
resources   = resources.get_system_resources()
url_api     = "http://%s:%s" % (os.getenv("FLASK_IP") , os.getenv("FLASK_PORT") )
api_token   = os.getenv("FLASK_API_TOKEN" , "")


push_health.push_kuiper(url_api=url_api ,api_token=api_token , service='es' , health={'resources': resources , 'info': info})
