#!/usr/bin/env bash

PYHSS_HSS_SERVICE_WORKERS=${PYHSS_HSS_SERVICE_WORKERS:-1}

cd ./services || exit 1

echo -n " * Starting API service... "
python3 apiService.py --host="${PYHSS_COMPONENT_NAME}" --port=8080 &
api_service_pid=$!
echo "Done (pid: ${api_service_pid})"

# Sleep is needed to let db be populated in a non-overlapping fashion
sleep 5

echo -n " * Starting Diameter service... "
python3 diameterService.py &
diameter_service_pid=$!
echo "Done (pid: ${diameter_service_pid=$!})"

if [ "$PYHSS_LOG_FILES_ENABLED" == "true" ]; then
    echo -n " * Starting Log service... "
    python3 logService.py &
    log_service_pid=$!
    echo "Done (pid: ${log_service_pid=$!})"
fi

for ix in $(seq 1 "$PYHSS_HSS_SERVICE_WORKERS"); do
    echo -n " * Starting HSS:${ix} service... "
    python3 hssService.py &
    hss_service_pids[ix]=$!
    echo "Done (pid: ${hss_service_pids[ix]})"
done

# wait for all pids
echo "Wait for pids: ${hss_service_pids[*]}"
for pid in "${hss_service_pids[@]}"; do
    wait "$pid"
done
