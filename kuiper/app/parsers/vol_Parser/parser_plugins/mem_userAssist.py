


def imain(res):
    results = []
    for i in range(len(res)):
        for child in res[i]['__children']:
            results.append(child)

    for i in range(len(results)):
        del results[i]['__children']
        del results[i]['Raw Data']

        results[i]["Hive Offset"] = hex(results[i]["Hive Offset"])
        results[i]['@timestamp'] = results[i]['Last Updated']

    return results