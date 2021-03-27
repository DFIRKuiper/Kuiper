


def imain(res):
    for i in range(len(res)):
        del res[i]['__children']
        res[i]["Offset"]    = hex(res[i]["Offset"])
        res[i]["End_VPN"]   = hex(res[i]["End_VPN"])
        res[i]["Parent"]    = hex(res[i]["Parent"])
        res[i]["Start_VPN"] = hex(res[i]["Start_VPN"])
    return res
    