import sys
import codecs
#Software: Microsoft Exchange Server
#Version: 15.0.0.0
#Log-type: ECP Server Log
#Date: 2021-03-03T00:01:18.223Z
#ECPServer Logs
#Fields: TimeStamp,ServerName,EventId,EventData
#HTTP Proxy Logs
#Fields: DateTime,RequestId,MajorVersion,MinorVersion,BuildVersion,RevisionVersion,ClientRequestId,Protocol,UrlHost,UrlStem,ProtocolAction,AuthenticationType,IsAuthenticated,AuthenticatedUser,Organization,AnchorMailbox,UserAgent,ClientIpAddress,ServerHostName,HttpStatus,BackEndStatus,ErrorCode,Method,ProxyAction,TargetServer,TargetServerVersion,RoutingType,RoutingHint,BackEndCookie,ServerLocatorHost,ServerLocatorLatency,RequestBytes,ResponseBytes,TargetOutstandingRequests,AuthModulePerfContext,HttpPipelineLatency,CalculateTargetBackEndLatency,GlsLatencyBreakup,TotalGlsLatency,AccountForestLatencyBreakup,TotalAccountForestLatency,ResourceForestLatencyBreakup,TotalResourceForestLatency,ADLatency,SharedCacheLatencyBreakup,TotalSharedCacheLatency,ActivityContextLifeTime,ModuleToHandlerSwitchingLatency,ClientReqStreamLatency,BackendReqInitLatency,BackendReqStreamLatency,BackendProcessingLatency,BackendRespInitLatency,BackendRespStreamLatency,ClientRespStreamLatency,KerberosAuthHeaderLatency,HandlerCompletionLatency,RequestHandlerLatency,HandlerToModuleSwitchingLatency,ProxyTime,CoreLatency,RoutingLatency,HttpProxyOverhead,TotalRequestTime,RouteRefresherLatency,UrlQuery,BackEndGenericInfo,GenericInfo,GenericErrors,EdgeTraceId,DatabaseGuid,UserADObjectGuid,PartitionEndpointLookupLatency,RoutingStatus

def get_fields(lines):
    i = 0
    for line in lines:
        i += 1
        if line.startswith("#Fields: "):
            fields = str(line[9:]).replace("\r\n", "").split(",")
            return fields

        if not line.startswith("#") and i > 1:
            break

    return None


def split_log_line(line):
    res = []
    elem = ""
    in_str = False
    had_quote = False
    for char in line:
        if char == '"':
            if had_quote and len(elem) > 0:
                elem += '"'
                had_quote = False
            else:
                in_str = not in_str
                had_quote = True

            continue
        else:
            had_quote = False

        if char == ',' and not in_str:
            res.append(elem)
            elem = ""
        else:
            elem += char

    res.append(elem)
    return res


def log_line_to_json(line, fields):
    if not line or line.startswith("#"):
        return None

    res = {}

    line_split = split_log_line(line.encode('utf-8').replace("\r\n", ""))
    for i in range(len(line_split)):
        if i < len(fields):
            res[fields[i]] = line_split[i]
        else:
            # This should not happen but let's not throw away data in case it does
            res["field" + str(i)] = line_split[i]

    if "DateTime" in res:
        # Log times appear to be UTC
        res["@timestamp"] = res["DateTime"]

    if "TimeStamp" in res:
        # Log times appear to be UTC
        res["@timestamp"] = res["TimeStamp"]

    if "@timestamp" not in res or res["@timestamp"] == "":
        return None
    return res


def exchange_log_interface(file, parser):
    try:
        with codecs.open(file, 'r', 'utf-8-sig') as fp:
            lines = fp.readlines()
        
        fields = get_fields(lines)
        if fields is None:
            return (None, "Unable to find fields in file header")

        res = []
        i = 0
        for line in lines:
            i += 1
            if i > 1:
                record = log_line_to_json(line, fields)
                if record is not None:
                    res.append(record)

        return res
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print(msg)
        return (None, msg)
