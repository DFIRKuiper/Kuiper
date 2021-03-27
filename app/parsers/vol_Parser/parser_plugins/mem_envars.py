


def imain(res):
    print("here")
    for i in range(len(res)):
        del res[i]['__children']
    return res