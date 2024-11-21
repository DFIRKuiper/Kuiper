#!/bin/bash

# Run scheduler
for variable_value in $(cat /proc/1/environ | sed 's/\x00/\n/g'); do
    export $variable_value
done

if [ $1 = "celery" ];
then
        python "/system_health/$1_health.py"
else
        python3 "/system_health/$1_health.py"
fi
