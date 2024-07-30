


def imain(res):
    data = {}
    for r in res:
        data[r['Variable']] = r['Value']


    data['@timestamp'] = data['SystemTime'].replace(" " , 'T')
    
    return [data]