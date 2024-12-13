#!/usr/bin/env bash
set -e
umask 002

# Result codes
readonly ENOENT=2    # No such file or directory
readonly ESEEK=29    # Illegal seek

# Substitute environment variables
# Arguments: <input file> <ouput file>
# shellcheck disable=SC2155,SC2317
substitute_variables() {

  local input=$1
  local output=$2

  # shellcheck disable=SC2016
  local variable_regexp='\$([a-zA-Z_]{1,}[a-zA-Z0-9_]*|\{[a-zA-Z_]{1,}[a-zA-Z0-9_]*\})'

  grep -n -E -o "$variable_regexp" "$input" | \
  while IFS= read -r match; do

    local line=${match%:*}
    local variable=${match#*:}

    local name=${variable//[\$\{\}]}
    local value=$(printenv "$name")

    # Check environment variable exists
    if [ -z "$value" ]; then
      echo "Undefined variable '${name}' was found in the $(basename -- ${input}) on line ${line}"
      exit $ESEEK
    fi

    echo "Replace variable:" \
         "file=$(basename -- ${input})," \
         "line=${line}," \
         "name=${name}," \
         "value=${value}"
  done

  envsubst < "$input" \
           > "$output"
}

echo "---- Environment variables ----"
env | awk '{ print ">", $0 }'

if [ -f "config.yaml" ]; then
    echo "Updating config for PyHSS"
    substitute_variables "config.yaml" "./bin/config.yaml"
else
    echo "Failed to update the config.yaml file. The file does not exist!!!"
    exit $ENOENT
fi

cd ./bin || exit $ENOENT

echo "---- PyHSS Config ----"
cat config.yaml | awk '{ print ">", $0 }'

echo "RUN: $*"
exec "$@"
