
def imain(res):
    for i in range(len(res)):
        del res[i]['__children']
        res[i]['@timestamp'] = res[i]['Created_Date']
    return res

