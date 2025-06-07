#!/bin/bash

set -o pipefail
# Consider 'set -e' for stricter error checking, but it might make debugging harder initially.

# --- Configuration ---
DEFAULT_EXP_NAME="exp-$(shuf -i 10000-99999 -n 1)"
DEFAULT_MAX_PARALLEL_TESTS=5
HOST_RESULTS_DIR="./results" # Relative to script execution directory (project root)
TOOLS_DIR="./tools"
CASE_STUDIES_DIR="./case_studies"

# --- Tool Specific Configurations ---
# For each tool, define:
# 1. _service_name: The service name in its docker-compose.yml
# 2. _command_template: The command to run. Use placeholders:
#    {TARGET_URL} - will be replaced with http://host.docker.internal:PORT/ENDPOINT
#    {OUTPUT_FILE_PATH} - will be replaced with the full path *inside the container* where output should go.
# 3. _output_filename: The name of the file the tool will generate.
declare -A TOOL_CONFIGS

TOOL_CONFIGS["clairvoyance_service_name"]="clairvoyance"
TOOL_CONFIGS["clairvoyance_command_template"]="poetry run clairvoyance {TARGET_URL} -o {OUTPUT_FILE_PATH}"
TOOL_CONFIGS["clairvoyance_output_filename"]="clairvoyance_schema.json"

TOOL_CONFIGS["Clairvoyance-Next_service_name"]="clairvoyance-next" # Assuming service name in its compose file
TOOL_CONFIGS["Clairvoyance-Next_command_template"]="poetry run clairvoyance {TARGET_URL} -o {OUTPUT_FILE_PATH}" # Example, adjust if different
TOOL_CONFIGS["Clairvoyance-Next_output_filename"]="clairvoyance_next_schema.json"

# Add KrakQL or other tools here following the same pattern
# TOOL_CONFIGS["Krakql_service_name"]="krakql"
# TOOL_CONFIGS["Krakql_command_template"]="python krakql_runner.py --url {TARGET_URL} --output {OUTPUT_FILE_PATH}"
# TOOL_CONFIGS["Krakql_output_filename"]="krakql_output.json"


# --- Helper Functions ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

get_all_tools() {
    find "$TOOLS_DIR" -maxdepth 1 -mindepth 1 -type d \
        -exec test -f '{}/docker-compose.yml' \; -print0 | xargs -0 -I {} basename '{}' | sort -u
}

get_all_case_studies() {
    find "$CASE_STUDIES_DIR" -maxdepth 1 -mindepth 1 -type d \
        \( -exec test -f '{}/docker-compose.yml' \; -o -exec test -f '{}/docker-compose.yaml' \; \) \
        -a -exec test -f '{}/ENDPOINT' \; -print0 | xargs -0 -I {} basename '{}' | sort -u
}

# --- Argument Parsing ---
EXP_NAME="$DEFAULT_EXP_NAME"
REQUESTED_TOOLS_STR=""
REQUESTED_CASE_STUDIES_STR=""
MAX_PARALLEL_TESTS="$DEFAULT_MAX_PARALLEL_TESTS"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -exp_name) EXP_NAME="$2"; shift ;;
        -tools) REQUESTED_TOOLS_STR="$2"; shift ;;
        -case_studies) REQUESTED_CASE_STUDIES_STR="$2"; shift ;;
        -max_parallel_tests) MAX_PARALLEL_TESTS="$2"; shift ;;
        *) log "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

log "Experiment Name: $EXP_NAME"
log "Max Parallel Tests: $MAX_PARALLEL_TESTS"

# --- Resolve Tool and Case Study Lists ---
ALL_AVAILABLE_TOOLS=($(get_all_tools))
ALL_AVAILABLE_CASE_STUDIES=($(get_all_case_studies))

if [[ -z "$REQUESTED_TOOLS_STR" || "$REQUESTED_TOOLS_STR" == "all" ]]; then
    SELECTED_TOOLS=("${ALL_AVAILABLE_TOOLS[@]}")
else
    IFS=',' read -r -a SELECTED_TOOLS <<< "$REQUESTED_TOOLS_STR"
fi

if [[ -z "$REQUESTED_CASE_STUDIES_STR" || "$REQUESTED_CASE_STUDIES_STR" == "all" ]]; then
    SELECTED_CASE_STUDIES=("${ALL_AVAILABLE_CASE_STUDIES[@]}")
else
    IFS=',' read -r -a SELECTED_CASE_STUDIES <<< "$REQUESTED_CASE_STUDIES_STR"
fi

if [ ${#SELECTED_TOOLS[@]} -eq 0 ]; then
    log "No tools selected or found. Exiting."
    exit 1
fi
if [ ${#SELECTED_CASE_STUDIES[@]} -eq 0 ]; then
    log "No case studies selected or found. Exiting."
    exit 1
fi

log "Selected Tools: ${SELECTED_TOOLS[*]}"
log "Selected Case Studies: ${SELECTED_CASE_STUDIES[*]}"

# --- Results Tracking ---
declare -A TEST_RESULTS # TEST_RESULTS["${tool}_${case_study}"]="✅" or "❌"

# --- Main Test Execution Function (to be run in background) ---
run_single_test() {
    local tool_name="$1"
    local case_study_name="$2"
    local current_exp_name="$3"
    local test_id="${tool_name}_${case_study_name}"

    log "[$test_id] Starting test."

    local cs_project_name="${current_exp_name}_${case_study_name}_${tool_name}"
    local tool_project_name="${current_exp_name}_${tool_name}_${case_study_name}" # For tool's docker compose project

    local case_study_dir="${CASE_STUDIES_DIR}/${case_study_name}"
    local tool_dir="${TOOLS_DIR}/${tool_name}"

    local host_test_results_dir="${HOST_RESULTS_DIR}/${current_exp_name}/${tool_name}/${case_study_name}"
    mkdir -p "$host_test_results_dir"
    # Path for tool output *inside the tool container* (assuming /results is mounted from host's HOST_RESULTS_DIR)
    local tool_output_filename_template="${TOOL_CONFIGS[${tool_name}_output_filename]}"
    if [ -z "$tool_output_filename_template" ]; then
        log "[$test_id] ERROR: Output filename not configured for tool $tool_name."
        TEST_RESULTS["$test_id"]="❌ (Config)"
        return 1
    fi
    local tool_output_file_container_path="/results/${current_exp_name}/${tool_name}/${case_study_name}/${tool_output_filename_template}"


    # 1. Start Case Study
    log "[$test_id] Starting case study '$case_study_name' (project: $cs_project_name)..."
    if ! (cd "$case_study_dir" && docker compose -p "$cs_project_name" up -d --wait --remove-orphans); then
        log "[$test_id] ERROR: Failed to start case study '$case_study_name'."
        TEST_RESULTS["$test_id"]="❌ (CS Start)"
        (cd "$case_study_dir" && docker compose -p "$cs_project_name" down -v --remove-orphans &>/dev/null) || true
        return 1
    fi
    log "[$test_id] Case study '$case_study_name' started."

    # 2. Get Case Study Port and Endpoint
    local cs_service_name="$case_study_name" # Assumption: service name matches directory name
    local cs_graphql_port_container
    cs_graphql_port_container=$(docker compose -f "${case_study_dir}/docker-compose.yml" config --format json | jq -r ".services.\"$cs_service_name\".ports[0].target" 2>/dev/null)
    if [ -z "$cs_graphql_port_container" ] || [ "$cs_graphql_port_container" == "null" ]; then
        log "[$test_id] ERROR: Could not determine container port for $cs_service_name in $case_study_name."
        TEST_RESULTS["$test_id"]="❌ (CS Port)"
        (cd "$case_study_dir" && docker compose -p "$cs_project_name" down -v --remove-orphans &>/dev/null) || true
        return 1
    fi

    local cs_graphql_port_host
    cs_graphql_port_host=$(docker compose -p "$cs_project_name" -f "${case_study_dir}/docker-compose.yml" port "$cs_service_name" "$cs_graphql_port_container" 2>/dev/null | cut -d':' -f2)
    if [ -z "$cs_graphql_port_host" ]; then
        log "[$test_id] ERROR: Failed to get host port for case study '$case_study_name'."
        TEST_RESULTS["$test_id"]="❌ (CS Port)"
        (cd "$case_study_dir" && docker compose -p "$cs_project_name" down -v --remove-orphans &>/dev/null) || true
        return 1
    fi

    local cs_endpoint_path
    cs_endpoint_path=$(cat "${case_study_dir}/ENDPOINT")
    local target_url="http://host.docker.internal:${cs_graphql_port_host}${cs_endpoint_path}"
    log "[$test_id] Case study target URL: $target_url"

    # 3. Run Tool
    local tool_service_name_template="${TOOL_CONFIGS[${tool_name}_service_name]}"
    local tool_command_template="${TOOL_CONFIGS[${tool_name}_command_template]}"

    if [ -z "$tool_service_name_template" ] || [ -z "$tool_command_template" ]; then
        log "[$test_id] ERROR: Service name or command template not configured for tool $tool_name."
        TEST_RESULTS["$test_id"]="❌ (Config)"
        (cd "$case_study_dir" && docker compose -p "$cs_project_name" down -v --remove-orphans &>/dev/null) || true
        return 1
    fi

    local final_tool_command="$tool_command_template"
    final_tool_command="${final_tool_command//\{TARGET_URL\}/$target_url}"
    final_tool_command="${final_tool_command//\{OUTPUT_FILE_PATH\}/$tool_output_file_container_path}"

    log "[$test_id] Running tool '$tool_name' (project: $tool_project_name) with command: $final_tool_command"
    # The tool's docker-compose.yml must mount the host's results dir to /results in container
    # e.g., volumes: - ../../results:/results (relative to tool's docker-compose.yml)
    if ! (cd "$tool_dir" && docker compose -p "$tool_project_name" run --rm "$tool_service_name_template" $final_tool_command); then
        log "[$test_id] ERROR: Tool '$tool_name' failed for case study '$case_study_name'."
        TEST_RESULTS["$test_id"]="❌ (Tool Fail)"
        # Continue to check CS health and cleanup
    else
        log "[$test_id] Tool '$tool_name' completed for case study '$case_study_name'."
    fi

    # 4. Check Case Study Health Post-Tool
    # A simple check: is the main service still "running" or "healthy"?
    # This might need refinement based on how health is truly determined.
    local cs_main_service_status
    cs_main_service_status=$(docker compose -p "$cs_project_name" -f "${case_study_dir}/docker-compose.yml" ps --filter "service=$cs_service_name" --format json | jq -r '.[0].Health // .[0].State' 2>/dev/null)
    log "[$test_id] Case study status after tool run: $cs_main_service_status"

    if [[ "$cs_main_service_status" == "healthy" || ( -z "$cs_main_service_status" && "$cs_main_service_status" == "running" ) ]]; then
        if [[ "${TEST_RESULTS[$test_id]}" != "❌ (Tool Fail)" ]]; then # Don't override if tool already failed
             TEST_RESULTS["$test_id"]="✅"
        fi
    else
        log "[$test_id] Case study '$case_study_name' unhealthy after tool run."
        TEST_RESULTS["$test_id"]="❌ (CS Unhealthy)"
    fi
    
    # If TEST_RESULTS was not set at all (e.g. tool ran fine, CS is healthy)
    if [ -z "${TEST_RESULTS[$test_id]}" ]; then
        TEST_RESULTS["$test_id"]="✅" # Default to success if no prior failure
    fi


    # 5. Cleanup Case Study
    log "[$test_id] Stopping case study '$case_study_name' (project: $cs_project_name)..."
    (cd "$case_study_dir" && docker compose -p "$cs_project_name" down -v --remove-orphans &>/dev/null) || \
        log "[$test_id] Warning: Failed to cleanly stop case study $cs_project_name. Manual check might be needed."
    
    log "[$test_id] Finished test. Result: ${TEST_RESULTS[$test_id]}"
}
export -f run_single_test log # Export functions for subshells if using GNU Parallel
export -A TEST_RESULTS TOOL_CONFIGS # Export associative arrays
export CASE_STUDIES_DIR TOOLS_DIR HOST_RESULTS_DIR # Export variables

# --- Parallel Execution ---
active_jobs=0
task_counter=0
total_tasks=$((${#SELECTED_TOOLS[@]} * ${#SELECTED_CASE_STUDIES[@]}))

log "Total test combinations to run: $total_tasks"

for tool in "${SELECTED_TOOLS[@]}"; do
    for case_study in "${SELECTED_CASE_STUDIES[@]}"; do
        task_counter=$((task_counter + 1))
        log "Queueing task $task_counter/$total_tasks: Tool '$tool', Case Study '$case_study'"

        if ! command -v jq &> /dev/null; then
            log "ERROR: jq is not installed. Please install jq to run this script."
            exit 1
        fi
        
        # Check if tool config exists
        if [ -z "${TOOL_CONFIGS[${tool}_service_name]}" ]; then
            log "ERROR: Configuration for tool '$tool' not found in TOOL_CONFIGS. Skipping."
            TEST_RESULTS["${tool}_${case_study}"]="❌ (No Config)"
            continue
        fi


        # Check if case study dir and ENDPOINT file exist
        if [ ! -d "${CASE_STUDIES_DIR}/${case_study}" ] || [ ! -f "${CASE_STUDIES_DIR}/${case_study}/ENDPOINT" ]; then
            log "ERROR: Case study directory or ENDPOINT file missing for '$case_study'. Skipping."
            TEST_RESULTS["${tool}_${case_study}"]="❌ (CS Files)"
            continue
        fi
        # Check if tool dir and docker-compose.yml exist
        if [ ! -d "${TOOLS_DIR}/${tool}" ] || [ ! -f "${TOOLS_DIR}/${tool}/docker-compose.yml" ]; then
            log "ERROR: Tool directory or docker-compose.yml missing for '$tool'. Skipping."
            TEST_RESULTS["${tool}_${case_study}"]="❌ (Tool Files)"
            continue
        fi


        if (( active_jobs >= MAX_PARALLEL_TESTS )); then
            log "Max parallel jobs ($MAX_PARALLEL_TESTS) reached. Waiting for a job to finish..."
            wait -n # Wait for any background job to finish
            active_jobs=$((active_jobs - 1))
        fi

        run_single_test "$tool" "$case_study" "$EXP_NAME" &
        active_jobs=$((active_jobs + 1))
    done
done

log "All tasks queued. Waiting for remaining jobs to complete..."
wait # Wait for all background jobs to finish
log "All jobs completed."

# --- Print Summary Table ---
log "Experiment Results Summary ($EXP_NAME):"

# Header
printf "| %-20s " "Tool"
for cs in "${SELECTED_CASE_STUDIES[@]}"; do
    printf "| %-20s " "$cs"
done
printf "|\n"

# Separator
printf "|-%-20s-" "--------------------"
for cs in "${SELECTED_CASE_STUDIES[@]}"; do
    printf "|-%-20s-" "--------------------"
done
printf "|\n"

# Rows
for tool in "${SELECTED_TOOLS[@]}"; do
    printf "| %-20s " "$tool"
    for cs in "${SELECTED_CASE_STUDIES[@]}"; do
        result="${TEST_RESULTS[${tool}_${cs}]}"
        if [ -z "$result" ]; then result="❓"; fi # Should not happen if all paths set a result
        printf "| %-20s " "$result"
    done
    printf "|\n"
done

log "Experiment finished. Results are in $HOST_RESULTS_DIR/$EXP_NAME"