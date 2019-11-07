
- [Contribution](#Contribution)
  - [Parsers List](#Parsers-List)
  - [Parsers Requests](#Parsers-Requests)
  - [Add Your Parser to the List](#Add-Your-Parser-to-the-List)


# Contribution

Dears, the core engine of **Kuiper** is the parsers, without parsers **Kuiper** cannot display any results and it is useless, the predefined parsers are few compared to the number of artifacts could be parsed and help the investigator on his/her analysis.

Add your parser to the list and help other analysts.



## Parsers List

Parser 		         | Author																	| Parser		| Author
-----------------   | ------------------------------------------------------------------------- | ------------ | ---
BrowserHistory      | [Saleh Muhaysin](https://github.com/salehmuhaysin/BrowserHistory_ELK)		| ComputerName        | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Srum                | [Saleh Muhaysin](https://github.com/salehmuhaysin/SRUM_parser)			|DHCP                | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
CSV                 | Custom by Saleh Muhaysin													|InstalledApp        | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Recyclebin          | Custom by Muteb Alqahtani													|InstalledComponents | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Scheduled Tasks     | Custom by Muteb Alqahtani													|LastVisitedMRU      | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Prefetch            | [MBromiley](https://github.com/bromiley/tools/tree/master/win10_prefetch)	|LaunchTracing       | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Windows Events      | [dgunter](https://github.com/dgunter/evtxtoelk)							|OpenSaveMRU         | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Amcache	            | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)						|ProfileList         | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
bits_admin          | [ANSSI](https://github.com/ANSSI-FR/bits_parser)							|ShellExtensions     | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Jumplist            | [Bhupendra Singh](https://github.com/Bhupipal/JumpListParser)				|TimeZoneInformation | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
MFT                 | [dkovar](https://github.com/dkovar/analyzeMFT)							|TypedUrls           | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
RUA                 | [davidpany](https://github.com/davidpany/WMI_Forensics)					|Uninstall           | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Shellbags           | [Willi Ballenthin](https://github.com/williballenthin/shellbags)			|UserAssist          | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Shimcache           | [MANDIANT](https://github.com/mandiant/ShimCacheParser)					|WordWheelQuery      | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
Shortcuts           | [HarmJ0y](https://github.com/HarmJ0y/pylnker)								|Bam                 | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
UsnJrnl             | [PoorBillionaire](https://github.com/PoorBillionaire/USN-Journal-Parser)	|AppCompatFlags      | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
WMI_Persistence     | [davidpany](https://github.com/davidpany/WMI_Forensics) | MuiCache            | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
RunMRU              | [Muteb Alqahtani](https://github.com/muteb/RegSkewer) | Sysinternals        | [Muteb Alqahtani](https://github.com/muteb/RegSkewer)
TerminalServerClient| [Muteb Alqahtani](https://github.com/muteb/RegSkewer)



# Parsers Requests

Do you have good development skills and want to contribute and help analysts on developing new parser, this is your place, analysts requested the following parsers to help their investigation, pick what is interesting, start developing, and [Add Your Parser to the List](#Add-Your-Parser-to-the-List)

Parser  | Request Link
------- | ------
XML		| None


If you want a specific parser to be added to the list, please send an issues -> Parser request template, and it will be added here



## Add Your Parser to the List

To add your custom parser to the parser's contribution list, please do the following:

1- Go to [Add Custom Parser](https://github.com/DFIRKuiper/Kuiper/wiki/Add-Custom-Parser)

2- Test the parser on **Kuiper** over a sample and make sure it parsed the sample correctly.

3- Send a "pull request" for only the parser folder and its files, make sure do not commit other files changed on **Kuiper** folders, only the parser folder.

4- Please send the sample of file artifacts and a screenshot of the parser configuration as follows
![create_cases](https://github.com/DFIRKuiper/Kuiper/blob/master/img/parser_details.png?raw=true)

5- If the parser need any dependencies to be installed, list the commands to install these dependencies, and we will add it to the installer
