import datetime
import json
import sys

def convert_datetime(date_value):

    micro_secs, _ = divmod(date_value, 10)
    time_delta = datetime.timedelta(
        microseconds=micro_secs
    )

    orig_datetime = datetime.datetime(1601, 1, 1)
    new_datetime = orig_datetime + time_delta
    return new_datetime.isoformat()



def read_file(file):
    parserd_file ={}
    flx = open(file,"r",encoding='utf-16')
    wr_flx = flx.readlines()
    for f in wr_flx:
        f = f.split("=")
        if f[0]== "EventTime":
            date_timex = convert_datetime(int(f[1]))
            parserd_file[f[0]] = date_timex
            parserd_file["@timestamp"] = date_timex
        elif f[0]== "TargetAppId":
            hash = f[1].split("!")[1]
            if hash.startswith("0000"):
                hash = hash[4:]
            parserd_file["hash"]= hash

        else:
            value = f[1].rstrip()
            parserd_file[f[0]]=value

    return [json.dumps(parserd_file)]



print(read_file(sys.argv[1]))
