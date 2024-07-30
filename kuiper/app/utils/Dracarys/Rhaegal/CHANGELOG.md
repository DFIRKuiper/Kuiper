# Change Log

## RhaegalLib
### Version 1.3 - 06/06/2020

* Change the processing from multiprocessing to multithriding.
* Added String search.
* A new class that represent an alert.
* Change varibales matching to contains insted of equals.
* Added progress logging.
* Change the main funtion for processing logs (process) to iterable function that return alert object.
* Add search modifier to search the full event for a string or regex search.
* Update dependencies.

### Version 1.2.2 - 19/02/2020

* Hot Fix

### Version 1.2.1 - 27/01/2020

- Change the EVTX parser to more efficient parser, Thanks to https://github.com/omerbenamram/pyevtx-rs.
- Added variables - this enable you to specify a variable instead a constant value (Environment variables, Other fields, etc). 
- Added modifiers - allows you to perform processing on any field such as field length and regex match. 
- Re-write "Event" class.
- Added "returns" field - this allow you to return some fields instead of the full event log (check the WiKi for more details).

### Version 1.0.1 - 27/10/2019

* Added logging
* Better Event log parser
* Better Rhaegal rule validation

### Version 1.0 - 26/10/2019

initial release 

## Rhaegal

### Version 1.1 09/04/2020

* Added new option to stop logging `--no-log`
* Log time taken by Rhaegal to finish.
* Added new option `-o, --output` to specify the output file.
* Added new option `--log-file` to specify the log file path.
* Added new option `--log-level` to specify the logging level.
* Replace the option `--processes` to `-n,--threads` to specify the number of threads for Rhaegal to use.
* Update dependencies.

### Version 1.0.2 19/02/2020

* Minor changes

### Version 1.0.1 - 27/10/2019

- Added logging

### Version 1.0 - 26/10/2019

initial release

## Rhaegal Rules

### 06/06/2020

* Added rules to detect RDP from public IP
* Added a new rule set for `lateral movements`
* Added rule to detect logs cleared.
* Fix some false positive on some rules.