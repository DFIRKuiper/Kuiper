


def imain(res):
    for i in range(len(res)):
        del res[i]['__children']
        res[i]['@timestamp'] = res[i]['Created']
        res[i]["Offset"] = hex(res[i]["Offset"])
    return res