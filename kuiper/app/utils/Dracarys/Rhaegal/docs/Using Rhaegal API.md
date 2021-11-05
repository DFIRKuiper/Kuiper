# Using Rhaegal API

In this section we will learn how to use Rhaegal on python scripts using `RhaegalLib.py`. RhaegalLib contains three class main, And they are as follows:

* `Event` class : which is the class that responsible to parse windows event logs. Each object of this class represent a record/event.
* `Rule` class : each object of this class represents a Rhaegal rule.
* `Rhaegal` class : this is the main class that is responsible of rule matching with events.

# Functions and Properties

The following tables breakdown the functions and properties for each class:

## Event

### Functions

| Name        | Description                                                  |
| ----------- | ------------------------------------------------------------ |
| Event(dict) | This is the constructor of the class that takes one argument of type `dict` and return an Event object |

### Properties

This class generates properties dynamically, So there is not a fixed number of properties. Each event field will be available as property. For example the field `EventID` would be accessed using `<OBJECT_NAME>.EventID`. In case of fields that contain `.` on them such as `TimeCreated.SystemTime` you can reference them using `<OBJECT_NAME>.TimeCreatedSystemTime` (just remove `.` character). The following table shows the properties that are present every time you create new Event object:

| Name      | Description                                                  | Type        |
| --------- | ------------------------------------------------------------ | ----------- |
| RawRecord | This is the RAW lxml object that got passed to the constructor | lxml object |
| EventData | This is a dictionary that contains all fields of the event   | Dictionary  |

## Rule

### Functions

| Name           | Description                                                  |
| -------------- | ------------------------------------------------------------ |
| Rule(rulestr)  | This is the constructor of this class. It takes a string as input which is the string version of the rule the parses it and creates rule object. |
| validateRule() | This rule is used to validate Rhaegal rule. This function will be called automatically when the rule parsing is finished. |

### Properties

| Name         | Description                                                  | Type       |
| ------------ | ------------------------------------------------------------ | ---------- |
| RawRule      | The string argument passed to the class constructor          | string     |
| type         | the type of the rule. This can only be public or private.    | String     |
| name         | rule name                                                    | String     |
| author       | the author field in the metadata section                     | String     |
| description  | the description field in the metadata section                | String     |
| reference    | the reference field in the metadata section                  | String     |
| creationDate | the creationDate field in the metadata section               | String     |
| score        | the score field in the metadata section                      | Int        |
| channel      | the channel of the log that this rule applies to             | String     |
| include      | this field contains all the fields in the include section    | Dictionary |
| exclude      | this field contains all the fields in the exclude section    | Dictionary |
| modifiers    | A list of all modifiers from the rule                        | list       |
| returns      | A list that contains all the field to be return by the rule. If empty the raw event will be returned | list       |
| variables    | <Not Implemented yet>                                        | list       |


## Rhaegal

### Functions

| Name                                                         | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| Rhaegal(rulePath=None,outputFormat="CSV",rulesDir=None)      | This is the constructor for this class. it accepts a single rule file, a path to multiple rules and output format RAW or CSV (Default). |
| StringMatch(string,pattern)                                  | Helper function that takes a string and a pattern then return True if the pattern matches the string or False if it is not. |
| match(rule,event)                                            | This is the main matching function. It takes a rule object and an event object and return the matched strings if there is a match or False if there is no match. |
| matchAll(event)                                              | This function takes an event object as an argument and matches all the ruleset to the given event object |
| displayAlert(event,rule,results="",privateRule=False,TriggeredEvents=[]): | This function handles the output.                            |
| MatchLogFile(filePath)                                       | Takes a path to EVTX file as argument and search through it using the ruleset. |
| MatchLogDirectory(directoryPath)                             | Takes a path to a directory that contains EVTX files to search through using the ruleset. |
| ProcessTimeBetweenLogs(EventsList,within)                    | This function is a helper function for the private rules.    |
| ProcessPrivateRules(logspath)                                | This function will only get called if there is a private rule. |
| process(directoryPath,numberOfThreads=10)                    | Takes a path that contains EVTX logs or a path to a single EVTX file and number of threads then process the logs using multithreading |

### Properties

| Name                            | Description                                                  | Type      |
| ------------------------------- | ------------------------------------------------------------ | --------- |
| outputFormat                    | The output format. This can only be `RAW` to print the raw event that got triggered or `CSV` to print the output as CSV (Default) | String    |
| ruleSet                         | A list of Rule objects that got parsed from the rule file/s  | List      |
| channels                        | A list of all the rules channels. This is used to improve the performance if the scanning where Rhaegal will scan only the logs in this list | List      |
| PublicRulesContainsPrivateRules | A list of rule objects that contains private rules (public rules that wraps private rules) | List      |
| Variables                       | An object of the class Variables that represent Rhaegal variable | Variables |
| logger                          | An object of logger class. Used by Rhaegal for logging       | logger    |

## Variables

### Functions

| Name              | Description                                                  |
| ----------------- | ------------------------------------------------------------ |
| Variables()       | This is the constructor of this class. It does not take any arguments but it calls two functions, `GetEnvVariables()` and `GetIPAddresses()` |
| GetEnvVariables() | Get all environment variables and set as properties.         |
| GetIPAddresses()  | Create a property called `IPAddresses` then add all IPs assigned to this property as a list. |

### Properties

| Name        | Description                                          | Type |
| ----------- | ---------------------------------------------------- | ---- |
| IPAddresses | A list that contains all IPs assigned to the machine | list |
| <DYNAMIC>   | A property for every environment variable.           | -    |



## Modifier

A class that represent a Rhaegal modifier, ex. `$Data.ServiceName <= 6` .

### Functions

| Name                                        | Description                                                  |
| ------------------------------------------- | ------------------------------------------------------------ |
| Modifier(modstr)                            | This is the constructor of this class.  It takes one argument which is the string representation of the modifier. |
| ParseModifier(modstr)                       | Parses the string representation of the modifier and return a dictionary that contains field,operation and value. |
| StringMatch(string,pattern,event,variables) | String matching function and variable evolution.             |
| Check(event,variables)                      | Function that returns the modifier evolution results (`True` or `False`). |

### Properties

| Name      | Description                                                  | Type          |
| --------- | ------------------------------------------------------------ | ------------- |
| field     | The field of the modifier. in the example above this is `$Data.ServiceName` | string        |
| operation | The operation of the modifier. in the example above this is `<=` | String        |
| value     | The value of the modifier. in the example above this is `6`  | int or string |



## Alert

A class that represent a Rhaegal alert.

### Functions

| Name                                         | Description                                                  |
| -------------------------------------------- | ------------------------------------------------------------ |
| Alert(event,rule,matchedStrings,record=None) | This is the constructor of this class.  it takes 5 arguments, `event` is the event that got triggered, `rule` is the rule that triggered on the event,`matchedStrings` is a list of matched strings,`record` the formatted record to be printed, if present it will be printed. |
| outputAlert()                                | Format the alert to CSV and print it to stdout.              |

### Properties

| Name           | Description                                 | Type  |
| -------------- | ------------------------------------------- | ----- |
| event          | The event that got triggered                | Event |
| rule           | The rule that triggered on                  | Rule  |
| isPrivateRule  | True if the rule is private False if public | bool  |
| matchedStrings | List that contains matched strings          | list  |
| record         | The formatted record to be printed          | list  |

# Example

Let's use Rhaegal API in a script ! in this example we will write a script that read a single Windows Event Log and a single Rhaegal rule and output the results. Here how the script will look like:

```python
from RhaegalLib import Rhaegal

if "__main__" == __name__:
    rhaegalObj = Rhaegal("Malcious_PowerShell.gh")
    rhaegalObj.MatchLogFile("Windows PowerShell.evtx")
```

This scripts look for malicious PowerShell execution on the event log called `Windows PowerShell.evtx`.