import sys

#Software: Microsoft Internet Information Services 8.5
#Version: 1.0
#Date: 2021-03-03 00:00:00
#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken


def get_fields(file):
    # The fields header should be present in the first 4KB of the file
    with open(file, 'r') as logfile:
        lines = logfile.readlines(4096)

    for line in lines:
        if line.startswith("#Fields: "):
            fields = line[9:].replace("\r\n", "").split(" ")
            return fields

        if not line.startswith("#"):
            break

    return None


def sanitize_field_names(fields):
    return list(map(lambda f: f.replace('-', '_').replace('(', '_').replace(')', '').lower(), fields))


def log_line_to_json(line, fields):
    if not line or line.startswith("#"):
        return None

    res = {}

    line_split = line.replace("\r\n", "").split(" ")
    for i in range(len(line_split)):
        if i < len(fields):
            res[fields[i]] = line_split[i]
        else:
            # This should not happen but let's not throw away data in case it does
            res["field" + str(i)] = line_split[i]

    if "date" in res and "time" in res:
        # Log times appear to be UTC
        res["@timestamp"] = "{}T{}".format(res["date"], res["time"])

    return res


def iis_log_interface(file, parser):
    try:
        fields = get_fields(file)
        if fields is None:
            raise Exception("Unable to find fields in file header")

        fields = sanitize_field_names(fields)

        res = []
        with open(file, 'r') as logfile:
            for line in logfile:
                record = log_line_to_json(line, fields)
                if record is not None:
                    res.append(record)

        return res
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print(msg)
        return (None, msg)
