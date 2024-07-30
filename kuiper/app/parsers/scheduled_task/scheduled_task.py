import winjob
import os
import datetime
import glob
import urllib
import xmltodict
from json import loads, dumps
from collections import OrderedDict
import copy

def files_parser(file):
    fd = open(file, 'r')
    task = winjob.winjob.read_task(fd.read())
    test= task.parse()

    # fix trigger time
    for i in range( 0 , len(test['triggers']) ):
    	if test['triggers'][i]['StartBoundary'] == '':
    		test['triggers'][i]['StartBoundary'] = '1700-01-01T00:00:00'
    	if test['triggers'][i]['EndBoundary'] == '':
    		test['triggers'][i]['EndBoundary'] = '1700-01-01T00:00:00'
    
    # convert data field in task to json instead of string
    if 'data' in test.keys():
        try:
            data_json = xmltodict.parse(test['data'])
            for d in data_json.keys():
                data_json[d] = xmltodict.parse(data_json[d])
            test['task_data'] = loads(dumps(data_json))
            del test['data']
        except:
            # if could not convert the data to json, then pass it as is
            pass

    test['@timestamp']=datetime.datetime.fromtimestamp(os.path.getctime(file)).isoformat()
    test['task_name'] = file.split('/')[-1]

    try:
        list_tasks = []
        for i in range(0, len(test['task_data']['Data']['DataCollectorSet']['PerformanceCounterDataCollector']['CounterDisplayName'])):
            t = {}
            t = copy.deepcopy(test)
            del t['task_data']['Data']['DataCollectorSet']['PerformanceCounterDataCollector']['CounterDisplayName']
            del t['task_data']['Data']['DataCollectorSet']['PerformanceCounterDataCollector']['Counter']
            t['task_data']['Data']['DataCollectorSet']['PerformanceCounterDataCollector']['CounterDisplayName'] = test['task_data']['Data']['DataCollectorSet']['PerformanceCounterDataCollector']['CounterDisplayName'][i]
            t['task_data']['Data']['DataCollectorSet']['PerformanceCounterDataCollector']['Counter']            = test['task_data']['Data']['DataCollectorSet']['PerformanceCounterDataCollector']['Counter'][i]
            list_tasks.append(t)
        return list_tasks
    except Exception as e:
        pass
        
    # if the 
    return [test]


def main(file):
    
    pars_fle = files_parser(file)
    return pars_fle
