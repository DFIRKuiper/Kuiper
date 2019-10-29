# Add Parser

## Overview
A parser is a script used to read a row data (artifacts) to parse it and return the results on a structured format that are understandable by Kuiper, such as reading the Windows Events row files (.evtx) and return the result on a readable and understandable format for Kuiper to present it on the case. Kuiper store all parsed data in Elasticsearch, so it will be stored as JSON format. 

## Instructions

### 1. List All parsers

To list all parsers, go to (Administrator Panel -> Configuration) then click the (Parsers) tab.
![parsers.png]([https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png?raw=true)


### 2. Add New Parser
In parser page, click on the (+) button.
![addparser.png]([https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/add_parser.png?raw=true)

Fill the input fields as following:
1.	**Parser Name**: make sure it does not contain spaces or special characters, only (letters, numbers, _)
2.	**Parser Description**
3.	**Parser File**: select the list of files and compress it in a zip file and upload it, make sure the files on the zip file directly not inside a folder.
![addparser.png]([https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/add_parser2.png?raw=true)
4.	**Parser Important Fields**: here you can select multiple fields that will show on the (browser artifacts) page.
![addparser.png]([https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/add_parser3.png?raw=true)
The field path contains the data json path, example of Windows Events
![addparser.png]([https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/add_parser4.png?raw=true)
5.	**Interface Function**: this function will be called to parse provided file row data, fill on the field the filename and the function name, example (srum_interface.SRUM_interface)
![addparser.png]([https://github.com/salehmuhaysin/Kuiper/blob/master/img/parsers.png](https://github.com/salehmuhaysin/Kuiper/blob/master/img/add_parser5.png?raw=true)
*Note*: this function should return a list of json “[{…},{…},{…}]”, each json represent a record on the database, if there is no records return empty list “[]”, if parser failed return (None). The function should have two parameters (file: path of the file to be parsed, parser: is the parser name). In addition, each Json record on the returned list should include a field named (@timestamp) which will be used on the timeline artifact browser pages.
6.	**Parser Type**: OS General, Web Browser, Program Execution, Logging Information, User Activities, etc.
7.	**File Categorization (comma separated)**: this is how the parser engine will identify if the files exist should be parsed by this parser or not, such as extension (.evtx), file_name (\$MFT), startswith (\$I), magic_number (file content start with provided hex value)
