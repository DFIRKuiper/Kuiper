

![logo.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/logo2.png?raw=true)


## Table of Contents

<!-- TOC depthFrom:2 -->


- [1. Kuiper](#kuiper)
    - [1.1. What is Kuiper?](#what-is-kuiper)
    - [1.2. Why Kuiper?](#why-kuiper)
    - [1.3. How Kuiper Will Help Optimize the Investigation?](#How-Kuiper-Will-Help-Optimize-the-Investigation)
    - [1.4. Use Cases](#Use-Cases)
- [2. Kuiper Components](#Kuiper-Components)
    - [2.1. Overview Components](#Overview-Components)
    - [2.2. Parsers](#Parsers)
- [3. Examples](#Examples)
- [4. Getting Started](#getting-started)
    - [4.1. Requirements](#requirements)
    - [4.1. Installation](#Installation)
- [5. Licenses](#Licenses)
- [6. Authors](#Authors)

    


<!-- /TOC -->


# Kuiper

Digital Investigation Platform


## What is Kuiper?
Kuiper is a digital investigation platform that provide a capabilities for the investigation team and individuals to parse, search, visualize collected evidences (evidences could be collected by fast traige script like [Hoarder](https://github.com/muteb/Hoarder)). In additional, collaborate with other team members on the same platform by tagging artifacts and present it on a timeline schema, as well as setting rules for automating the detection on the future cases. The main purpose of this project is to aid in streamlining incident responders investigation activities and allow advanced analytics capabilities with the ability to handle a large amounts of data. 
![diagram.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/diagram.png?raw=true)


## Why Kuiper?
Today there are a lot of tools used by incident response analysts during the investigation, thou these tools help to identify the malicious activities and findings, as incident response analysts there are some shortages that needs to be optimized:
- Speeding the work flow.
- Increase the accuracy.
- Reduce resources exhaustion.

With a large number of cases (like IR service providing) and a large number of team members, it becomes hard for collaboration among team members and correlation and building rules to detect malicious activities on future cases. 
Kuiper solve these shortages. 

## How Kuiper Will Help Optimize the Investigation?
- **Centralized server**: Using a single centralized server (**Kuiper**) that do all the processing on the server-side reduce the needed hardware resources (CPU, RAM, Hard-disk) for the analysts team, no need for powerful laptop any more. In addition, all evidences stored in single server instead of copying it on different machines during the investigation.
- **Consistency**: Depending on different parsers by team member to parse same artifacts might provide inconsistency on the generated results, using tested and trusted parser increase the accuracy.
- **Predefined rules**: Define rules on Kuiper will save a lot of time to trigger alerts on past, current, and future cases, for example have you thought of creating rule to trigger suspicious encoded powershell commands on all parsed artifacts, or suspicous binary executed from temp folder, in **Kuiper** you can defined these rules and more.
- **Collaboration**: Browsing the parsed artifacts on same web interface by team members boost the collaboration among them using **tagging** and **timeline** feature instead of every one work on his/her machine.


## Use Cases

 - Create cases for the investigation and each case contain the list of machines scoped.
 - Upload multiple files (artifacts) collected from scoped machines via [Hoarder](https://github.com/muteb/Hoarder), [KAPE](https://www.kroll.com/en/services/cyber-risk/investigate-and-respond/kroll-artifact-parser-extractor-kape), or files collected by any other channel.
 - Start parsing these artifact files concurrently for selected machines or all.
 - Browse and search within the parsed artifacts for all machines on the opened case.
 - Save search query as rules, these rules could be used to trigger alerts for future cases.
 - Tag suspicious/malicious records, and display the tagged records on timeline schema. For records or information without records (such as information collected from external evidences like FW, proxy, WAF, etc. logs) you can add a message on timeline with the specific time.
 - Collected files without predefined parser is not an issue anymore, you can write your own parser and add it to Kuiper and will parse these files. read more how to add parser from [Add Custom Parser](https://github.com/salehmuhaysin/Kuiper/blob/master/Add_Custom_Parser.md)




# Kuiper Components

## Overview Components

Kuiper use the following components:

**Flask:** A web framework written in Python, used as the primary web application component. 

**Elasticsearch:** A distributed, open source search and analytics engine, used as the primary database to store parser results.

**MongoDB:** A database that stores data in JSON-like documents that can vary in structure, offering a dynamic, flexible schema, used to store Kuiper web application configurations and information about parsed files. 

**Redis:** A in-memory data structure store, used as a database, cache and message broker, used as a message broker to relay tasks to celery workers.

**Celery:** A asynchronous task queue/job queue based on distributed message passing, used as the main processing engine to process relayed tasks from redis.


## Parsers

The following are parsers used in Kuiper project, some are built custom, and some have been modified to output the results in a compliant format in order to integrate it with Kuiper and some have been heavily modified to fix issues with pushed data.

Parser 		         | Author
----------------- | -------------
BrowserHistory    | [Saleh Muhaysin](https://github.com/salehmuhaysin/BrowserHistory_ELK)
Srum              | [Saleh Muhaysin](https://github.com/salehmuhaysin/SRUM_parser)
CSV               | Custom
Recyclebin        | Custom
Scheduled Tasks   | Custom
Prefetch          | [MBromiley](https://github.com/bromiley/tools/tree/master/win10_prefetch)
Windows Events    | [dgunter](https://github.com/dgunter/evtxtoelk)
Amcache	          | [Willi Ballenthin](https://github.com/williballenthin/python-registry/blob/master/samples/amcache.py) 
bits_admin        | [ANSSI](https://github.com/ANSSI-FR/bits_parser)
Jumplist          | [Bhupendra Singh](https://github.com/Bhupipal/JumpListParser)
MFT               | [dkovar](https://github.com/dkovar/analyzeMFT)
RUA               | [davidpany](https://github.com/davidpany/WMI_Forensics)
Shellbags         | [Willi Ballenthin](https://github.com/williballenthin/shellbags)
Shimcache         | [MANDIANT](https://github.com/mandiant/ShimCacheParser)
Shortcuts         | [HarmJ0y](https://github.com/HarmJ0y/pylnker)
UsnJrnl           | [PoorBillionaire](https://github.com/PoorBillionaire/USN-Journal-Parser)
WMI_Persistence   | [davidpany](https://github.com/davidpany/WMI_Forensics)

To add your own parser on Kuiper, read documentation [Add Custom Parser](https://github.com/salehmuhaysin/Kuiper/blob/master/Add_Custom_Parser.md)

# Examples

1. **Cases page**: from here you can manage cases
![diagram.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/cases.png?raw=true)
2. **Rules management**: edit and remove rule
![diagram.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/rules.png?raw=true)

3. **Parsers Configuration**: manage the parsers (add, delete, and edit)
![diagram.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png?raw=true)

4. **Case machines**: list all machines on the selected case, from here you can add machine and upload artifacts to it as zip file or raw files. In addition, if you have multiple machines compressed you can upload all of them and the machine name will take the file name.
![diagram.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/machines.png?raw=true)


5. **Artifacts Browsing**: this is where the hunting exists ;), all records parsed from artifacts will be here, you can search, save search as rule, tag records.
![diagram.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/browse_artifacts.png?raw=true)

6. **Timeline**: all tagged records and add messages listed on chronological order. You can export it as CSV.
![diagram.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/timeline.png?raw=true)


# Getting Started

## Requirements

- **OS:** 64-bit Ubuntu 16.04.1 LTS (Xenial)  (preferred)
- **RAM:**  4GB (minimum), 8GB (preferred)
- **Cores:** 4 (minimum)
- **Disk:** 25GB for testing purposes and more disk space depends on the amount of data collected.

  

## Installation 

Run the following commands to clone the Kuiper repo via git.

```
$ git clone https://github.com/salehmuhaysin/Kuiper.git
```

Change your current directory location to the new Kuiper directory, and run the **kuiper_install.sh** bash script as root.

```
$ cd Kuiper/
$ sudo ./kuiper_install.sh -install 
```

The **kuiper_install.sh** bash script will install all Kuiper dependencies such as (python, pip, redis, elasticsearch, mongodb and many others used by Kuiper default parsers).

In order to make the configuration of Kuiper straight forward, a single file named **configuration.yaml** holds all configuration parameters as seen below.

The following section of the configuration file is responsible for setting the parameters for Flask web application. 

~~~yaml
...
# ============ Kuiper Platform
Kuiper:
  IP    : 0.0.0.0
  PORT  : 5000
  Debug : True   # enable debugging mode
...
~~~

The following section of the configuration file is responsible for setting the parameters for celery based on redis configurations. 

~~~yaml
...
# ============ configuration of celery
CELERY:
  CELERY_BROKER_URL     : redis://localhost:6379
  CELERY_RESULT_BACKEND : redis://localhost:6379
  CELERY_TASK_ACKS_LATE : True
...
~~~

The following section of the configuration file is responsible for setting the parameters for the elasticsearch database. 

~~~yaml
...
# ============ Elasticsearch
ElasticSearch:
  IP    : 127.0.0.1
  PORT  : 9200
...
~~~

After properly modifying the configuration file, use the following bash file to launch Kuiper.

```
$ ./kuiper_install.sh -run 
```

If everything runs correctly now you should be able to use Kuiper through the link (http://<kuiper-ip>:<kuiper-port>/).

Happy hunting :).

# Issues Tracking and Contribution

We are happy to receive any issues, contribution, and ideas.

we appreciate sharing any parsers you develop, just send a pull request to be able to add it to the parsers list


# Licenses

- Each parser has its own license, all parsers places on one folder  `parsers/` .

- what licensing do we want ??

  

# Creators

[Saleh Muhaysin](https://github.com/salehmuhaysin), Twitter ([@saleh_muhaysin](https://twitter.com/saleh_muhaysin)),

[Muteb](https://github.com/muteb), Twitter([@muteb_alqahtani](https://twitter.com/muteb_alqahtani))

Abdullah 
