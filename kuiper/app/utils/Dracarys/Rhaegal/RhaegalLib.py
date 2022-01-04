import re
import yaml
from io import StringIO
import fnmatch
from evtx import PyEvtxParser
import json
from datetime import datetime
import threading
import os
import threading
import logging
import csv
import itertools
from string import ascii_letters,digits
import ifaddr
import queue

__author__ = "AbdulRhman Alfaifi"
__version__ = "1.3.2"
__maintainer__ = "AbdulRhman Alfaifi"
__license__ = "GPL"
__status__ = "Development"

class Variables:
    def __init__(self):
        self.GetEnvVariables()
        self.GetIPAddresses()
    
    def GetEnvVariables(self):
        try:
            for env in os.environ:
                setattr(self,env,os.environ[env])
            return True
        except:
            return False

    def GetIPAddresses(self):
        try:
            ips = []
            for inet in ifaddr.get_adapters():
                for ip in inet.ips:
                    if isinstance(ip.ip,str):
                        ips.append(ip.ip)
            self.IPAddresses = ips
            return ips
        except:
            return False

class Modifier:
    def __init__(self,modstr):
        results = self.ParseModifier(modstr)
        self.field = results["field"]
        self.operation = results["operation"]
        self.value = results["value"]
    
    def ParseModifier(self,modstr):
        parts = modstr.split()
        results = {}
        if modstr.lower().startswith("search "):
            results["field"] = parts[0]
            results["operation"] = parts[1]
            results["value"] = " ".join(parts[2::])
        elif " $rex " in modstr:
            parts = modstr.split(" $rex ")
            results["field"] = parts[0]
            results["operation"] = "$rex"
            results["value"] = parts[1]
        else:
            if len(parts) == 3:
                results["field"] = parts[0]
                results["operation"] = parts[1]
                results["value"] = int(parts[2])
        return results

    def StringMatch(self,string,pattern,event,variables):
        if pattern.startswith("$"):
            if pattern == "$IP":
                for IP in variables.IPAddresses:
                    if IP in string:
                        return True
            else:
                try:
                    return self.StringMatch(string,f"*{getattr(variables,pattern[1::])}*",event,variables)    
                except AttributeError:
                    pass
                eventField = event.EventData.get(pattern[1::])
                if eventField:
                    return self.StringMatch(string,f"*{eventField}*",event,variables)    
                else:
                    return False
        if string and pattern:
            string = string.lower()
            pattern = pattern.lower()
        return fnmatch.fnmatch(string,pattern)

    def Check(self,event,variables):
        if self.field.lower() == "search" and self.operation == "$rex":
            eventData = json.dumps(event.EventData)
            return bool(re.findall(f"{self.value}",eventData))
        elif self.field.lower() == "search" and self.operation == "$str":
            eventData = json.dumps(event.EventData)
            return self.StringMatch(eventData,self.value,event,variables)
        eventValue = event.EventData.get(self.field)
        if eventValue:
            if self.operation == ">":
                return len(eventValue) > self.value
            elif self.operation == "<":
                return len(eventValue) < self.value
            elif self.operation == "<=":
                return len(eventValue) <= self.value
            elif self.operation == ">=":
                return len(eventValue) >= self.value
            elif self.operation == "==":
                return len(eventValue) == self.value
            elif self.operation == "$rex":
                return bool(re.findall(f"^{self.value}$",eventValue))

# A class that represents an event record. it takes 'lxml' object as input.
class Event:
    def __init__(self,record=None,raw=None):
        if raw:
            self.RawRecord = raw
            self.EventData = raw
        elif record:
            self.RawRecord = record
            self.EventData = self.BuildEventData(record["Event"])
        else:
            raise ValueError(f"'record' or 'raw' is required")
        
        for key, value in self.EventData.items():
            setattr(self, key.replace(".",""), value)

    def BuildEventData(self,data,parentName=None):
        results = {}
        for key,val in data.items():
            if key == "xmlns":
                continue
            if isinstance(val,dict):
                if parentName:
                    if key == "#attributes":
                        results.update(self.BuildEventData(val,f"{parentName}"))
                    elif key == "Data" and parentName == "Data":
                        results.update(self.BuildEventData(val,f"{parentName}"))
                    else:
                        results.update(self.BuildEventData(val,f"{parentName}.{key}"))
                else:
                    if key == "EventData":
                        results.update(self.BuildEventData(val,"Data"))
                    elif key == "System":
                        results.update(self.BuildEventData(val))
                    else:
                        results.update(self.BuildEventData(val,key))
            else:
                if parentName:
                    if key == "#text":                          
                        if isinstance(val,list):
                            for i in range(len(val)):
                                results.update({f"{parentName}{i}":str(val[i])})
                        else:
                            results.update({f"{parentName}":str(val)})
                    else:
                        results.update({f"{parentName}.{key}":str(val)})
                elif val != None:
                    results.update({key:str(val)})

        return results

    def __str__(self):
        return str(self.EventData)


    
    # this function get the value from a json dict by path (key1.key2.key3)
    def getDataJsonPath(self, jsonPath):
        jsonPath = jsonPath.split('.')
        jsonDataTmp = self.EventData
        for p in jsonPath:
            try:
                jsonDataTmp = jsonDataTmp[p]
            except:
                return None
        return jsonDataTmp



# A class that represents Rhaegal rule.
class Rule:
    def getRuleDetails(self):
        details = self.metadata
        details['type'] = self.type
        details['name'] = self.name
        return details


    def __init__(self,RuleString):
        self.RawRule = RuleString
        typeAndName = re.match("((public|private) (.*)+)",RuleString).group(0).split()
        self.type = typeAndName[0].lower()
        self.name = typeAndName[1]
        ruleDateStr=""
        for line in re.findall("(\s+(.*:)(\s+.*[^\}])+)",RuleString)[0][0].split("\n"):
            if re.match("[\s]+#",line):
                pass
            else:
                ruleDateStr+=line+"\n"
        ruleData = yaml.safe_load(StringIO(ruleDateStr))

        self.metadata = ruleData.get("metadata")

        self.author = self.metadata.get("author")
        self.description = self.metadata.get("description")
        self.reference = self.metadata.get("reference")
        self.creationDate = self.metadata.get("creationDate")
        self.include = ruleData.get("include")
        self.score = self.metadata.get("score")
        self.channel = ruleData.get("Channel")
        if not self.channel:
            self.channel = ruleData.get("channel")
        if not  self.channel:
            self.channel = "*"
        self.exclude = ruleData.get("exclude")
        self.modifiers = ruleData.get("modifiers")
        self.returns = ruleData.get("returns")
        self.variables = ruleData.get("variables")
        self.validateRule()
        
    def validateRule(self):
        charset = ascii_letters+digits+"_().$"
        if not isinstance(self.include,dict):
            if not isinstance(self.exclude,dict):
                if not isinstance(self.modifiers,list):
                    raise TypeError(f"Error in the rule named '{self.name}'. The 'include' should be a dictionary.")
        if self.channel == None and self.include:
            if not self.include.get("rule"):
                raise TypeError(f"Error in the rule named '{self.name}'. The filed 'Channel' is required.")
        if not self.score:
            self.score = 10
        if self.exclude == None:
            self.exclude = {}
        if not self.modifiers:
            self.modifiers = []
        if not self.variables:
            self.variables = []
        if not self.returns:
            self.returns = []
        if not isinstance(self.returns,list):
            raise TypeError(f"Error in the rule named '{self.name}'. The 'returns' section should be a list not {type(self.returns)}")    
        if not isinstance(self.modifiers,list):
            raise TypeError(f"Error in the rule named '{self.name}'. The 'modifiers' section should be a list not {type(self.modifiers)}")
        if not isinstance(self.variables,list):
            raise TypeError(f"Error in the rule named '{self.name}'. The 'variables' section should be a list not {type(self.variables)}")
        if self.type != "public" and self.type != "private":
            raise TypeError(f"Error in the rule named '{self.name}'. The allowed rule type are 'public' or 'private' but you used '{self.type}'")
        for char in self.name:
            if char not in charset:
                raise ValueError(f"Error in the rule named '{self.name}'. The character '{char}' is not allowed in the rule name. The rule name should only contains letters, numbers and '_'")
        if not self.description:
            raise ValueError(f"Error in the rule named '{self.name}'. The 'metadata' secition should at least contain 'description' field")
        if self.include:
            if self.type == "public" and self.include.get("rule"):
                if not self.include.get("rule") or not self.include.get("if"):
                    raise ValueError(f"Error in the rule named '{self.name}'. private rule wrapper should contain 'rule' & 'if' fields inside 'include' section")
                if not self.include.get("if").get("within"):
                    raise ValueError(f"Error in the rule named '{self.name}'.The 'if' field should contain 'within' field")
                if not isinstance(self.include.get("rule"),list):
                    raise ValueError(f"Error in the rule named '{self.name}'.The 'rule' field should be a 'list' not '{type(self.include.get('rule'))}'")
    def __str__(self):
        return str(self.__dict__)


class Alert:
    def __init__(self,event,rule,matchedStrings,privateRule=False,record=None):
        self.event = event
        self.rule = rule
        self.isPrivateRule = True if rule.type.lower() == "private" else False
        self.matchedStrings = matchedStrings
        self.record = record

     # Formates the output in the choosen format.
    def outputAlert(self,file=None):
        if file:
            out = file
        else:
            out = StringIO()
        writer = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC,lineterminator="\n")
        if self.record:
            writer.writerow(self.record)
        else:
            if self.rule.returns:
                returns = {}
                for field in self.rule.returns:
                    returns[field] = self.event.EventData.get(field)
                data = [self.event.TimeCreatedSystemTime, self.event.EventRecordID, self.rule.name, self.rule.score, self.rule.description, self.rule.reference, self.matchedStrings, returns]
            else:
                data = [self.event.TimeCreatedSystemTime, self.event.EventRecordID, self.rule.name, self.rule.score, self.rule.description, self.rule.reference, self.matchedStrings, self.event.RawRecord]
            writer.writerow(data)
        if not file:
            print(out.getvalue(),end="")

# Rhaegal main class that handles the processing and the trigger mechanism.
class Rhaegal:
    def __init__(self,rulePath=None,outputFormat="CSV",rulesDir=None,logger=None):
        self.Queue = queue.Queue()
        self.logger = logger
        self.Variables = Variables()
        self.outputFormat = outputFormat
        self.PublicRulesContainsPrivateRules = []
        rex = re.compile('((public|private) .*(\n){0,1}\{(.*|\s)+?\})')
        # rex = re.compile('((public|private) .*(\n){0,1}{(\n.*)+})')
        rules=""
        self.channels=[]
        if not rulePath and rulesDir:
            for root, _, files in os.walk(rulesDir):
                for file in files:
                    if file.endswith(".gh"):
                        fullpath = os.path.abspath(os.path.join(root,file))
                        if logger:
                            logger.info(f"Reading Rhaegal rule file '{fullpath}'")
                        for line in open(fullpath).readlines():
                            if line.startswith("#"):
                                pass
                            else:
                                rules+=line
        elif rulePath and not rulesDir:
            for line in open(rulePath).readlines():
                if line.startswith("#"):
                    pass
                else:
                    rules+=line
        else:
            raise ValueError(f"You can pass only 'rulePath' or 'rulesDir' but not both")
        ruleSetStr = rex.findall(rules)
        self.ruleSet = []
        for rule in ruleSetStr:
            self.ruleSet.append(Rule(rule[0]))
        for rule in self.ruleSet:
            if rule.include:
                if rule.include.get("rule"):
                    self.PublicRulesContainsPrivateRules.append(rule)
            if rule.channel not in self.channels and rule.channel != None:
                self.channels.append(rule.channel)
        self.channels = [s.lower() for s in self.channels]

        if len(self.ruleSet) == 0:
            raise Exception(f"{__file__} was not able to load the rules !")
        # Validate the private rules called in the private rules wrapper are present.
        for rule in self.PublicRulesContainsPrivateRules:
            if not all([True if x in [i.name for i in self.ruleSet] else False for x in rule.include.get("rule")]):
                raise ValueError(f"Error in the rule named '{rule.name}'. The 'rule' field should be a list of private rules that are initialize")
        
        ruleNames = [x.name for x in self.ruleSet]
        if logger:
            logger.info(f"The rules were parsed successfully. The total number of rules parsed are '{len(self.ruleSet)}'")
            nl = '\n'
            logger.info(f"A list of all the rules that got parsed successfully : \n{nl.join([ ' - '+name for name in ruleNames])}")
        for rule in self.ruleSet:
            if ruleNames.count(rule.name) > 1:
                raise ValueError(f"Error in the rule named '{rule.name}'. Detected rule name duplication")

    # Takes a string and a pattren. Return True if the pattren matches the string or False if it does not.
    def StringMatch(self,string,pattern,event=None):
        if isinstance(string, int):
            try:
                 pattern = int(pattern)
            except:
                pass
            return string == pattern

        if pattern.startswith("$"):
            if pattern == "$IP":
                return string in self.Variables.IPAddresses    
            else:
                try:
                    return self.StringMatch(string,f"*{getattr(self.Variables,pattern[1::])}*")    
                except AttributeError:
                    pass
                eventField = event.get(pattern[1::])
                if eventField:
                    return self.StringMatch(string,f"*{eventField}*")    
                else:
                    return False
        else:
            if string and pattern:
                string = string.lower()
                pattern = pattern.lower()
                return fnmatch.fnmatch(string,pattern)
            return False


    # The main matching function. tasks rule object and event object as input then returns the matched strings if the rule got triggered or False if not triggered.
    def match(self,rule,event):
        if rule.channel:
            if not self.StringMatch(event.Channel.lower(),rule.channel.lower()):
                return False
        triggired = True            
        matchStrs = []
        if rule.include:
            for key,value in rule.include.items():
                if key == "rule":
                    for privateRuleName in value:
                        for privateRule in self.ruleSet:
                            if privateRule.name == privateRuleName:
                                triggired = triggired and self.match(privateRule,event)
                    return triggired
                else:
                    try:
                        if isinstance(rule.include.get(key),list):
                            oneMatched = False
                            for s in rule.include.get(key):
                                if event.getDataJsonPath(key) == None:
                                    if self.logger:
                                        self.logger.warning(f"Unable to find the field '{key}' from the rule '{rule.name}' in the following event : \n {event}")
                                    oneMatched = False
                                    break

                                if self.StringMatch(event.getDataJsonPath(key),s,event.EventData):
                                    oneMatched = oneMatched or True
                                    matchStrs.append(event.getDataJsonPath(key))
                                else:
                                    oneMatched = oneMatched or False
                            triggired = triggired and oneMatched
                            if not triggired:
                                return False
                        else:
                            if event.getDataJsonPath(key) == None:
                                if self.logger:
                                    self.logger.warning(f"Unable to find the field '{key}' from the rule '{rule.name}' in the following event : \n {event}")
                            
                            if event.getDataJsonPath(key) != None and self.StringMatch(event.getDataJsonPath(key),value,event.EventData):
                                triggired = triggired and True
                                matchStrs.append(event.getDataJsonPath(key))
                            else:
                                triggired = triggired and False
                            if not triggired:
                                return False
                    except TypeError as e:
                        if self.logger:
                            self.logger.error(e,exc_info=True)
        for key,value in rule.exclude.items():
            if key == "rule":
                for privateRuleName in value:
                    for privateRule in self.ruleSet:
                        if privateRule.name == privateRuleName:
                            triggired = triggired and self.match(privateRule,event)
            else:
                try:
                    if isinstance(rule.exclude.get(key),list):
                        oneMatched = False
                        for s in rule.exclude.get(key):
                            if event.getDataJsonPath(key) == None:
                                if self.logger:
                                    self.logger.warning(f"Unable to find the field '{key}' from the rule '{rule.name}'")
                                oneMatched = True
                                break
                            if self.StringMatch(event.getDataJsonPath(key),s,event.EventData):
                                oneMatched = oneMatched or True
                            else:
                                oneMatched = oneMatched or False
                        triggired = triggired and not oneMatched
                    else:
                        if event.getDataJsonPath(key) == None:
                            if self.logger:
                                self.logger.warning(f"Unable to find the field '{key}' from the rule '{rule.name}'")
                        if event.getDataJsonPath(key) != None and self.StringMatch(event.getDataJsonPath(key),value,event.EventData):
                            triggired = triggired and False
                        else:
                            triggired = triggired and True
                except TypeError as e:
                    if self.logger:
                        self.logger.error(e,exc_info=True)
                    pass

        
        modFlag = True

        for modifier in rule.modifiers:
            mod = Modifier(modifier)
            if mod.Check(event,self.Variables):
                modFlag = modFlag and True
                matchStrs.append(f"MOD : {modifier}")
            else:
                modFlag = modFlag and False
                break
        
        triggired = modFlag and triggired
        
        if triggired:
            if self.logger and rule.type != "private":
                self.logger.debug(f"The rule named '{rule.name}' triggered on the event '{event}'")
            return matchStrs
        else:
            return False

    # Takes an event object as input and look that event on all of the available rules then display alert of the alert got triggered.
    def matchAll(self,event):
        for rule in self.ruleSet:
            triggired = True
            if rule.type == "public":
                results = self.match(rule,event)
                if results:
                    triggired = triggired and True
                else:
                    triggired = triggired and False
                if triggired:
                    self.Queue.put(Alert(event,rule,results))
    
    # Helper function for private rule matching that takes a list of events and return the events that happens within X milliseconds
    def ProcessTimeBetweenLogs(self,EventsList,within):
        MatchedEvent = []
        for EventSet in EventsList:
            datesList = []
            relativeTime = 0
            for event in EventSet:
                datesList.append(datetime.strptime(event.TimeCreatedSystemTime,"%Y-%m-%dT%H:%M:%S.%fZ"))
            datesList.sort()
            relativeTime = (datesList[len(datesList)-1] - datesList[0]).total_seconds() * 1000
            relativeTime = int(relativeTime if relativeTime > 0 else relativeTime * -1)
            if relativeTime < within:
                MatchedEvent.append(EventSet)
        return MatchedEvent

    # This function gets triggred only if there is a public rule that calls private rules in the ruleset
    def ProcessPrivateRules(self,logspath):
        if self.logger:
            self.logger.info(f"Starting processing private rules on the log/s in '{logspath}' ...")
        for pubrule in self.PublicRulesContainsPrivateRules:
            triggered = None
            privRules = []
            privRulesChannels = []
            TriggeredEvents = {}
            for privrulename in pubrule.include.get("rule"):
                for rule in self.ruleSet:
                    if rule.name == privrulename:
                        privRules.append(rule)
                        privRulesChannels.append(rule.channel.lower())
            for filePath in self.LogsToProcess:
                parser = PyEvtxParser(filePath)
                for record in parser.records_json():
                    try:
                        data = json.loads(record["data"])
                        event = Event(data)
                        if event.Channel.lower() in privRulesChannels:
                            for prirule in privRules:
                                if self.match(prirule,event):
                                    if triggered == None:
                                        triggered = True
                                    triggered = triggered and True
                                    if not TriggeredEvents.get(prirule):
                                        TriggeredEvents[prirule] = [event]
                                    else:
                                        TriggeredEvents[prirule].append(event)
                        else:
                            break
                    except (OSError, KeyError) as e:
                        if self.logger:
                            self.logger.error(e,exc_info=True)
                        continue
                    except Exception as e:
                        if self.logger:
                            self.logger.error(e,exc_info=True)
                            
            if len(TriggeredEvents) != len(privRules):
                return False

            TriggeredEventsList = []
            for key,val in TriggeredEvents.items():
                TriggeredEventsList.append(val)
            TriggeredEventsWithinTheSpecifiedTime  = self.ProcessTimeBetweenLogs(list(itertools.product(*TriggeredEventsList)),int(pubrule.include.get("if").get("within")))
            
            if TriggeredEventsWithinTheSpecifiedTime:
                for EventSet in TriggeredEventsWithinTheSpecifiedTime:
                    recordIDs = []
                    triggeredEventsData = {}
                    privRuleNames = pubrule.include.get("rule")
                    privateRules = []
                    for r in self.ruleSet:
                        if r.name in privRuleNames:
                            privateRules.append(r)

                    for r in privateRules:
                        for e in EventSet:
                            if r.channel == e.Channel:
                                if r.returns:
                                    fields = {}
                                    for field in r.returns:
                                        fields.update({field:e.EventData.get(field)})
                                    triggeredEventsData[r.name] = fields
                                else:
                                    triggeredEventsData[r.name] = e.RawRecord
                    for event in EventSet:
                        recordIDs.append(event.EventRecordID)
                    data = [event.TimeCreatedSystemTime, recordIDs, pubrule.name, pubrule.score, pubrule.description, pubrule.reference, [], triggeredEventsData]
                    self.Queue.put(Alert(event,pubrule,[],privateRule=True,record=data))
            else:
                return False

    # Go through a directory/file looking for EVTX file then start processing them (multithreading).
    def process(self,destPath,numberOfThreads=10):
        destPath = os.path.abspath(destPath)
        self.LogsToProcess = []
        threads = []
        processedLogs=0
        if os.path.isfile(destPath):
            self.LogsToProcess.append(destPath)
        else:
            for root, _, files in os.walk(destPath):
                for file in files:
                    if file.endswith(".evtx"):
                        fullpath = os.path.abspath(os.path.join(root,file))
                        self.LogsToProcess.append(fullpath)
        
        if self.logger:
            logsList = ""
            for path in self.LogsToProcess:
                logsList+=f"- {path}\n"
            self.logger.info(f"The following list is the logs that will be processed by Rhaegal:\n{logsList}")

        p = threading.Thread(target=self.ProcessPrivateRules,args=(destPath,))
        p.start()
        threads.append(p)
        for path in self.LogsToProcess:
            
            p = threading.Thread(target=self.MatchLogFile,args=(path,))
            p.start()
            threads.append(p)
            while True:
                while not self.Queue.empty():
                    yield self.Queue.get()
                for thread in threads:
                    if not thread.is_alive():
                        threads.remove(thread)
                        processedLogs +=1
                        if self.logger:
                            self.logger.info(f"Processed {processedLogs} of {len(self.LogsToProcess)} Event Logs")
                        if len(threads) < numberOfThreads:
                            break
                if len(threads) < numberOfThreads:
                    break
        while True:
            while not self.Queue.empty():
                yield self.Queue.get()
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)

            if len(threads) == 0:
                break
        
