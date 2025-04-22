#!/bin/bash

CASES_DIR="./case_studies"

# List all available cases (subdirectories with a docker-compose.yml)
get_all_cases() {
  find "$CASES_DIR" -maxdepth 1 -mindepth 1 -type d | while read -r dir; do
    if [ -f "$dir/docker-compose.yaml" ] || [ -f "$dir/docker-compose.yml" ]; then
      basename "$dir"
    fi
  done
}

# Function to display help
show_help() {
  echo "Usage: $0 {up|down|ps} {case1 case2 ... | all}"
  echo ""
  echo "Available case studies:"
  for case in $(get_all_cases); do
    echo "- $case"
  done
}

# If no arguments provided or 'help' is the first argument, display help and exit.
if [ "$#" -eq 0 ] || [ "$1" == "help" ]; then
  show_help
  exit 0
fi

COMMAND=$1
shift

# Expand 'all' into the full list
if [ "$1" == "all" ]; then
  shift
  CASES=$(get_all_cases)
else
  CASES="$@"
fi

# Validate command
if [[ "$COMMAND" != "up" && "$COMMAND" != "down" && "$COMMAND" != "ps" ]]; then
  echo "Usage: $0 {up|down|ps} {case1 case2 ... | all}"
  exit 1
fi

# Execute command for each case
for CASE in $CASES; do
  CASE_PATH="$CASES_DIR/$CASE"

  if [ -f "$CASE_PATH/docker-compose.yaml" ] || [ -f "$CASE_PATH/docker-compose.yml" ]; then
    echo "==> $COMMAND: $CASE"
    if [ "$COMMAND" == "ps" ]; then
      (cd "$CASE_PATH" && docker compose ps)
    elif [ "$COMMAND" == "down" ]; then
      (cd "$CASE_PATH" && docker compose "$COMMAND")
    elif [ "$COMMAND" == "up" ]; then        
      (cd "$CASE_PATH" && docker compose "$COMMAND" -d)
    fi
  else
    echo "!! Skipping '$CASE' — no docker-compose.yml found."
  fi
done