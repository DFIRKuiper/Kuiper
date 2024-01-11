


def imain(res):

    for i in range(len(res)):
        res[i]['@timestamp'] = res[i]['CreateTime']
        res[i]['Offset'] = hex(res[i]['Offset(V)'])
        
        if res[i]['Handles'] is None:
            del res[i]['Handles']

        del res[i]['Offset(V)']
        del res[i]['__children']

    return res