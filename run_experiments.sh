#!/bin/bash

# --- Configuration ---
# Generate a 5-digit random number for default experiment name
DEFAULT_EXP_NAME="exp-$(printf "%05d" $((RANDOM % 90000 + 10000)))"
DEFAULT_MAX_PARALLEL_TESTS=5 # Default maximum number of parallel tests to run
RESULTS_DIR="./results" # Host path for all experiment outputs
TOOLS_DIR="./tools" # Directory containing all tools
CASE_STUDIES_DIR="./case_studies" # Directory containing all case studies

# --- Temporary Directory for test results (status markers) ---
TMP_RESULTS_DIR=$(mktemp -d "/tmp/${DEFAULT_EXP_NAME}_results_XXXXXX")
if [ ! -d "$TMP_RESULTS_DIR" ]; then
    echo "Failed to create temporary directory. Exiting."
    exit 1
fi

cleanup() {
    log "Cleaning up temporary results directory: $TMP_RESULTS_DIR"
    rm -rf "$TMP_RESULTS_DIR"
}
trap cleanup EXIT SIGINT SIGTERM

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
        -exec test -f '{}/docker-compose.yml' \; \
        -a -exec test -f '{}/ENDPOINT' \; -print0 | xargs -0 -I {} basename '{}' | sort -u
}

# --- Argument Parsing ---
EXP_NAME="$DEFAULT_EXP_NAME" 
INPUT_TOOLS_LIST="" # Comma-separated list of tools to run, or "all" for all available tools
INPUT_CASE_STUDIES_LIST="" # Comma-separated list of case studies to run, or "all" for all available case studies
MAX_PARALLEL_TESTS="$DEFAULT_MAX_PARALLEL_TESTS" # Maximum number of parallel tests (a test consists of a pair <tool, case_study>) to run

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --exp_name) EXP_NAME="$2"; shift ;;
        --tools) INPUT_TOOLS_LIST="$2"; shift ;;
        --case_studies) INPUT_CASE_STUDIES_LIST="$2"; shift ;;
        --max_parallel_tests) MAX_PARALLEL_TESTS="$2"; shift ;;
        -h|--help) 
            echo "Usage: $0 [--exp_name EXP_NAME] [--tools TOOL1,TOOL2,... | all] [--case_studies CS1,CS2,... | all] [--max_parallel_tests N]"
            echo "Default experiment name: $DEFAULT_EXP_NAME"
            echo "Default max parallel tests: $DEFAULT_MAX_PARALLEL_TESTS"
            echo "Available tools: $(get_all_tools | tr '\n' ', ')"
            echo "Available case studies: $(get_all_case_studies | tr '\n' ', ')"
            exit 0 ;;
        *) log "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

log "Experiment Name: $EXP_NAME" 
log "Max Parallel Tests: $MAX_PARALLEL_TESTS"
log "Temporary result markers will be stored in: $TMP_RESULTS_DIR"
log "Tool outputs will be in: $RESULTS_DIR/$EXP_NAME"

# --- Resolve Tool and Case Study Lists ---
ALL_AVAILABLE_TOOLS=($(get_all_tools))
ALL_AVAILABLE_CASE_STUDIES=($(get_all_case_studies))

if [ "$INPUT_TOOLS_LIST" == "all" ]; then
    SELECTED_TOOLS=("${ALL_AVAILABLE_TOOLS[@]}")
else
    IFS=',' read -r -a SELECTED_TOOLS <<< "$INPUT_TOOLS_LIST"
fi

if [ "$INPUT_CASE_STUDIES_LIST" == "all" ]; then
    SELECTED_CASE_STUDIES=("${ALL_AVAILABLE_CASE_STUDIES[@]}")
else
    IFS=',' read -r -a SELECTED_CASE_STUDIES <<< "$INPUT_CASE_STUDIES_LIST"
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


# --- Main Test Execution Function (to be run in background) ---
run_single_test() {
    local tool_name="$1"
    local case_study_name="$2"
    local current_exp_name="$3"
    local current_tmp_results_dir="$4"

    local test_id="${tool_name}_${case_study_name}" # Unique identifier for this test
    local result_file="${current_tmp_results_dir}/${test_id}.result" # For ✅/❌ status

    log "[$test_id] Starting test."

    local case_study_project_name="${current_exp_name}_${case_study_name}_${tool_name}"
    local tool_project_name="${current_exp_name}_${tool_name}_${case_study_name}"

    local case_study_dir="${CASE_STUDIES_DIR}/${case_study_name}"
    local tool_dir="${TOOLS_DIR}/${tool_name}"

    # Directory *inside the tool's container* where it should place its output files.
    # The tool's docker-compose.yml MUST map the host's $RESULTS_DIR to /results in the container.
    local tool_output_dir_container_path="/results/${current_exp_name}/${tool_name}/${case_study_name}"

    # Default result to failure, overwrite on success
    echo "❌ (Setup)" > "$result_file"

    # 1. Start Case Study
    log "[$test_id] Starting case study '$case_study_name' which will be targeted by tool '$tool_name'."
    if ! (cd "$case_study_dir" && docker compose -p "$case_study_project_name" up -d --wait --remove-orphans &>/dev/null); then # -p sets the project name (format: [experiment name]_[case study name]_[tool name]), -d runs in detached mode, --wait waits for the service to be healthy
        # If the case study fails to start, we log the error and clean up.
        log "[$test_id] ERROR: Failed to start case study '$case_study_name'."
        echo "❌ (Case Study Start)" > "$result_file"
        (cd "$case_study_dir" && docker compose -p "$case_study_project_name" down -v --remove-orphans &>/dev/null) || true
        return 1
    fi
    log "[$test_id] Case study '$case_study_name' for the tool '$tool_name' started successfully."

    # 2. Get Case Study Port and Endpoint
    local case_study_port
    local raw_port_info

    log "[$test_id] Attempting to get exposed host port for service '$case_study_name' in project '$case_study_project_name'."

    # Get port mapping(s) for the service.
    case_study_port=$(docker ps --filter "label=com.docker.compose.project=$case_study_project_name" --filter "label=com.docker.compose.service=$case_study_name" --format "{{.Ports}}" 2>/dev/null | cut -d',' -f1 | sed -n 's/.*:\([0-9]*\)->.*/\1/p')


    if [ -z "$case_study_port" ] || ! [[ "$case_study_port" =~ ^[0-9]+$ ]]; then
        # If the pipeline failed (e.g., 'docker compose port' gave no output, or awk failed to parse),
        # case_study_port will be empty or non-numeric.
        log "[$test_id] ERROR: Failed to get or parse a valid host port for service '$case_study_name'. Parsed value: '$case_study_port'."
        echo "❌ (Case Study: Port Error)" > "$result_file"
        (cd "$case_study_dir" && docker compose -p "$case_study_project_name" down -v --remove-orphans &>/dev/null) || true
        return 1
    fi

    local case_study_endpoint_path
    case_study_endpoint_path=$(cat "${case_study_dir}/ENDPOINT")
    local target_url="http://host.docker.internal:${case_study_port}${case_study_endpoint_path}"
    log "[$test_id] Case study target URL: $target_url"

    # 3. Run Tool
    local tool_command_args # This will hold the arguments part of the command

    # Define tool command arguments based on tool_name
    # {TARGET_URL} and {OUTPUT_DIR_PATH} are available placeholders and will be replaced later.
    if [ "$tool_name" == "clairvoyance" ] || [ "$tool_name" == "Clairvoyance-Next" ]; then
        # Clairvoyance tools expect an output file path. They will create 'schema.json' inside the provided dir.
        tool_command_args="poetry run clairvoyance {TARGET_URL} -o {OUTPUT_DIR_PATH}/schema.json"
        log "[$test_id] Using specific command for tool '$tool_name'."
    # Add elif blocks for other tools with specific command structures
    # elif [ "$tool_name" == "AnotherTool" ]; then
    #    tool_command_args="--input {TARGET_URL} --out-dir {OUTPUT_DIR_PATH}"
    else
        # Default: tool's entrypoint takes target URL as its main argument.
        # Output directory is implicitly known by the tool via its mapped /results volume.
        tool_command_args="{TARGET_URL}"
        log "[$test_id] Using default command for tool '$tool_name'."
    fi

    # Replace placeholders in the chosen command template
    tool_command_args="${tool_command_args//\{TARGET_URL\}/$target_url}"
    tool_command_args="${tool_command_args//\{OUTPUT_DIR_PATH\}/$tool_output_dir_container_path}"

    log "[$test_id] Running tool '$tool_name' for case study '$case_study_name' with service '$tool_name' and args: $tool_command_args"
    if ! (cd "$tool_dir" && docker compose -p "$tool_project_name" run -T --rm "$tool_name" $tool_command_args &>/dev/null); then
        log "[$test_id] ERROR: Tool '$tool_name' failed for case study '$case_study_name'."
        echo "❌ (Tool Fail)" > "$result_file"
    else
        log "[$test_id] Tool '$tool_name' completed for case study '$case_study_name'."
        echo "✅" > "$result_file" # Mark success based on tool exit code
    fi

    # 4. Check Case Study Health Post-Tool
    local cs_main_service_status
    cs_main_service_status=$(docker compose -p "$case_study_project_name" -f "${case_study_dir}/docker-compose.yml" ps --format '{{if .Health}}{{.Health}}{{else}}{{.State}}{{end}}' 2>/dev/null)
    log "[$test_id] Case study status after tool run: $cs_main_service_status"

    # If the case study service is not 'healthy' or not 'running', it's a critical failure.
    # This overrides any previous status in $result_file (e.g., if the tool reported ✅).
    if ! [[ "$cs_main_service_status" == "healthy" || "$cs_main_service_status" == "running" ]]; then
        log "[$test_id] Case study '$case_study_name' is not healthy/running (Status: $cs_main_service_status). Marking as unhealthy."
        echo "❌ (Case Study Unhealthy after Tool Run)" > "$result_file"
    fi
    
    # 5. Cleanup Case Study
    log "[$test_id] Stopping case study '$case_study_name' for the tool '$tool_name'."
    (cd "$case_study_dir" && docker compose -p "$case_study_project_name" down -v &>/dev/null) || true # The true is to ignore errors if the compose file was not found or the service was already stopped.

    log "[$test_id] Finished test. Result: $(cat "$result_file")"
}
export -f run_single_test log
export CASE_STUDIES_DIR TOOLS_DIR RESULTS_DIR # Export simple and default config variables

# --- Parallel Execution ---
job_pids=() # Array to store PIDs of background jobs
task_counter=0
total_tasks=$((${#SELECTED_TOOLS[@]} * ${#SELECTED_CASE_STUDIES[@]}))

log "Total test combinations to run: $total_tasks"

for tool in "${SELECTED_TOOLS[@]}"; do
    for case_study in "${SELECTED_CASE_STUDIES[@]}"; do
        task_counter=$((task_counter + 1))
        log "Queueing task $task_counter/$total_tasks: Tool '$tool', Case Study '$case_study'"

        if [ ! -d "${CASE_STUDIES_DIR}/${case_study}" ] || [ ! -f "${CASE_STUDIES_DIR}/${case_study}/ENDPOINT" ]; then
            log "ERROR: Case study directory, docker-compose.yml or ENDPOINT file missing for '$case_study'. Skipping."
            echo "❌ (Case Study Not Supported)" > "${TMP_RESULTS_DIR}/${tool}_${case_study}.result"
            continue
        fi

        if [ ! -d "${TOOLS_DIR}/${tool}" ] || [ ! -f "${TOOLS_DIR}/${tool}/docker-compose.yml" ]; then
            log "ERROR: Tool directory or docker-compose.yml missing for '$tool'. Skipping."
            echo "❌ (Tool Not Supported)" > "${TMP_RESULTS_DIR}/${tool}_${case_study}.result"
            continue
        fi

        # Manage parallel jobs
        while (( ${#job_pids[@]} >= MAX_PARALLEL_TESTS )); do
            log "Max parallel jobs ($MAX_PARALLEL_TESTS) reached. Checking for finished jobs..."
            found_finished_job=0
            for i in "${!job_pids[@]}"; do
                pid_to_check="${job_pids[$i]}"
                if ! kill -0 "$pid_to_check" 2>/dev/null; then
                    wait "$pid_to_check"
                    unset 'job_pids[$i]'
                    found_finished_job=1
                    log "Job with PID $pid_to_check finished."
                    break
                fi
            done
            job_pids=("${job_pids[@]}") # Re-index
            if (( found_finished_job == 0 )); then
                sleep 1
            fi
        done

        run_single_test "$tool" "$case_study" "$EXP_NAME" "$TMP_RESULTS_DIR" &
        job_pids+=($!)
        log "Launched job for $tool on $case_study with PID $! Current active jobs: ${#job_pids[@]}"
    done
done

log "All tasks queued. Waiting for remaining ${#job_pids[@]} jobs to complete..."
for pid in "${job_pids[@]}"; do
    wait "$pid"
done
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
        result_file_path="${TMP_RESULTS_DIR}/${tool}_${cs}.result"
        result_content="❓"
        if [ -f "$result_file_path" ]; then
            result_content=$(cat "$result_file_path")
            if [ -z "$result_content" ]; then result_content="❓ (Empty)"; fi
        fi
        printf "| %-20s " "$result_content"
    done
    printf "|\n"
done

# Save a CSV version of the results
RESULTS_CSV_FILE="${RESULTS_DIR}/${EXP_NAME}/results.csv"
mkdir -p "$(dirname "$RESULTS_CSV_FILE")"
{
    echo "Tool,${SELECTED_CASE_STUDIES[*]}"
    for tool in "${SELECTED_TOOLS[@]}"; do
        line="$tool"
        for cs in "${SELECTED_CASE_STUDIES[@]}"; do
            result_file_path="${TMP_RESULTS_DIR}/${tool}_${cs}.result"
            if [ -f "$result_file_path" ]; then
                line+=",$(cat "$result_file_path")"
            else
                line+=",❓ (No Result)"
            fi
        done
        echo "$line"
    done
} > "$RESULTS_CSV_FILE"
log "Results saved to $RESULTS_CSV_FILE"

# --- Cleanup Temporary Results Directory ---
rm -rf "$TMP_RESULTS_DIR"

log "Experiment finished. Tool outputs are in $RESULTS_DIR/$EXP_NAME. Summary printed in the file $RESULTS_CSV_FILE."