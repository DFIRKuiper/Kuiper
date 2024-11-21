<p align="center">
     <img src="./docs/mvt.png" width="200" />
</p>

# Mobile Verification Toolkit

[![](https://img.shields.io/pypi/v/mvt)](https://pypi.org/project/mvt/)
[![Documentation Status](https://readthedocs.org/projects/mvt/badge/?version=latest)](https://docs.mvt.re/en/latest/?badge=latest)

Mobile Verification Toolkit (MVT) is a collection of utilities to simplify and automate the process of gathering forensic traces helpful to identify a potential compromise of Android and iOS devices.

It has been developed and released by the [Amnesty International Security Lab](https://www.amnesty.org/en/tech/) in July 2021 in the context of the [Pegasus project](https://forbiddenstories.org/about-the-pegasus-project/) along with [a technical forensic methodology and forensic evidence](https://www.amnesty.org/en/latest/research/2021/07/forensic-methodology-report-how-to-catch-nso-groups-pegasus/).

## MVT_parser

MVT_parser parses mvt tool decrypted backup to be compatible with Kuiper. The parser at its current version supports ios backup only.

## Output

Containts 26 parsers:
1 ios_BackupInfo
2 ios_Manifest
3 ios_ProfileEvents
4 ios_InstalledApplications
5 ios_Calls
6 ios_ChromeFavicon
7 ios_ChromeHistory
8 ios_Contacts
9 ios_FirefoxFavicon
10 ios_FirefoxHistory
11 ios_IDStatusCache
12 ios_InteractionC
13 ios_LocationdClients
14 ios_OSAnalyticsADDaily
15 ios_Datausage
16 ios_SafariBrowserState
17 ios_SafariHistory
18 ios_TCC
19 ios_SMS
20 ios_SMSAttachments
21 ios_WebkitResourceLoadStatistics
22 ios_WebkitSessionResourceLog
23 ios_Whatsapp
24 ios_Shortcuts
25 ios_Timeline
26 ios_ConfigurationProfiles

## Usage
1- Backup the mobile device with iTunes app

2- Decrypt your backup with MVT tool
MVT_IOS_BACKUP_PASSWORD="mypassword" mvt-ios decrypt-backup -d /path/to/decrypted /path/to/backup

3- Add the file "mdf_iPhone.trigger" to the backup folder as a trigger for the parsers to identify mobile backups.

4- Upload your ios backup folder to Kuiper and start processing it.


## Refrences
https://github.com/mvt-project/mvt
