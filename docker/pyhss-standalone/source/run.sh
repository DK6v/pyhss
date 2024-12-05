#!/usr/bin/env bash

ls -al /pyhss
ls -al /pyhss/bin

cd ./services || exit 1

echo " * Start API service"
python3 apiService.py --host="${PYHSS_COMPONENT_NAME}" --port=8080 &
# Sleep is needed to let db be populated in a non-overlapping fashion
sleep 5

echo " * Start Diameter service"
python3 diameterService.py &
# Sleep is needed to let db be populated in a non-overlapping fashion
sleep 5

if [ "$PYHSS_LOG_ENABLED" == "true" ]; then
    echo " * Start Log service"
    python3 logService.py &
fi

echo " * Start HSS service"
python3 hssService.py
