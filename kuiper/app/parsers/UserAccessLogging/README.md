![KStrike](https://github.com/brimorlabs/KStrike/blob/master/logo.png?raw=true)


# KStrike
Stand-alone parser for User Access Logging from Server 2012 and newer systems

# [BriMor Labs](https://www.brimorlabs.com)

## KStrike

This script will parse data from the User Access Logging files contained on Windows Server 2012 and newer systems, found under the path "\Windows\System32\Logfiles\SUM" (please visit the KPMG blog post at https://advisory.kpmg.us/blog/2021/digital-forensics-incident-response.html for more details). For documentation on these files, please visit the official documentation page at https://docs.microsoft.com/en-us/windows-server/administration/user-access-logging/manage-user-access-logging



### Usage 
Run the script from the command line, afer you have extracted the database files from the SUM folder. This script will work with Python 2 or Python 3. It has also been tested on the most recent SIFT workstation release

```
This script will parse on-disk User Access Logging found on Windows Server 2012
and later systems, found under the path "\Windows\System32\Logfiles\SUM"
The output is double pipe || delimited

Example usage: KStrike.py SYSTEMNAME\Current.mdb > Current_mdb.txt
```

This script has been tested on the following systems:
- Windows
- macOS
- \*nix

REQUIREMENTS:

- libesedb (pyesedb) (https://github.com/libyal/libesedb)
