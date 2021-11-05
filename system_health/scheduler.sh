#!/bin/bash

# Run scheduler
for variable_value in $(cat /proc/1/environ | sed 's/\x00/\n/g'); do
    export $variable_value
done

python3 "/system_health/$1_health.py"