import winjob
import os
import datetime
import glob


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


    test['@timestamp']=datetime.datetime.fromtimestamp(os.path.getatime(file)).isoformat()
    test['task_name'] = file.split('/')[-1]
    
    return test


def main(file):
    
    pars_fle = files_parser(file)
    return pars_fle
