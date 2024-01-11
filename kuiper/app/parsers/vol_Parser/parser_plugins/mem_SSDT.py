


def imain(res):
    for i in range(len(res)):
        del res[i]['__children']
        res[i]["Address"] = hex(res[i]["Address"])
    return res
    