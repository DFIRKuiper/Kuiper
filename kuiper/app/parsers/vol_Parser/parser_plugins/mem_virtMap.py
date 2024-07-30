


def imain(res):
    for i in range(len(res)):
        del res[i]['__children']
        res[i]["End_offset"]        = hex(res[i]["End_offset"])
        res[i]["Start_offset"]      = hex(res[i]["Start_offset"])
    return res
    