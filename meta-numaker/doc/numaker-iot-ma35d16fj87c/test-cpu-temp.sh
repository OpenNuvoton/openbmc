#!/bin/bash
# ==============================================================================
# NuMaker-IoT-MA35D16FJ87C OpenBMC - Continuous CPU Temperature Monitor
#
# Continuously queries the MA35 SoC internal temperature sensor via Redfish:
#   Endpoint: /redfish/v1/Chassis/system/Sensors/temperature_cpu_thermal
#
# Usage:
#   ./test-cpu-temp.sh [OPTIONS] [BMC_IP] [INTERVAL]
#
# Options:
#   -H, --host <IP|host>    BMC hostname or IP (default: numaker-iot-ma35d16fj87c.local)
#   -u, --user <user>       Redfish username (default: root)
#   -p, --pass <pass>       Redfish password (default: 0penBmc)
#   -i, --interval <sec>    Polling interval in seconds (default: 1.0, e.g. 0.5, 2)
#   -c, --count <num>       Read N times and exit (default: 0 = continuous / infinite)
#   -l, --log [file]        Log readings to CSV file (default: numaker-iot-ma35d16fj87c-temp.csv)
#   --csv                   Output data rows directly in CSV format (stdout)
#   -h, --help              Show this help message
#
# Press [Ctrl+C] at any time to gracefully stop and view the summary statistics.
# ==============================================================================

set -o pipefail

# --- Default Configurations ---
DEFAULT_BMC_IP="numaker-iot-ma35d16fj87c.local"
DEFAULT_USER="root"
DEFAULT_PASS="0penBmc"
DEFAULT_INTERVAL=1.0

BMC_IP="${BMC_IP:-$DEFAULT_BMC_IP}"
USER="${BMC_USER:-$DEFAULT_USER}"
PASS="${BMC_PASS:-$DEFAULT_PASS}"
INTERVAL="${INTERVAL:-$DEFAULT_INTERVAL}"
MAX_COUNT=0
LOG_FILE=""
CSV_STDOUT=0

SENSOR_ENDPOINT="/redfish/v1/Chassis/system/Sensors/temperature_cpu_thermal"

# Threshold defaults (will be updated dynamically from Redfish if available)
WARN_THRESHOLD=95.0
CRIT_THRESHOLD=105.0

# Terminal Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Statistics
SAMPLE_COUNT=0
ERROR_COUNT=0
MIN_TEMP=""
MAX_TEMP=""
SUM_TEMP=0.0
START_TIME=$(date +%s)

# Helper: Show Help
show_help() {
    cat << EOF
NuMaker-IoT-MA35D16FJ87C OpenBMC - Continuous CPU Temperature Monitor

Usage:
  $(basename "$0") [OPTIONS] [BMC_IP] [INTERVAL]

Options:
  -H, --host <IP|host>    BMC hostname or IP (default: ${DEFAULT_BMC_IP})
  -u, --user <user>       BMC username (default: ${DEFAULT_USER})
  -p, --pass <pass>       BMC password (default: ${DEFAULT_PASS})
  -i, --interval <sec>    Polling interval in seconds (default: ${DEFAULT_INTERVAL}s)
  -c, --count <num>       Number of readings before exit (default: 0 = continuous)
  -l, --log [file]        Save readings to CSV file (default: numaker-iot-ma35d16fj87c-temp.csv)
  --csv                   Output CSV data stream directly to stdout
  -h, --help              Display this help message

Examples:
  # 1. Run continuous monitoring with default settings (1s interval):
  ./$(basename "$0")

  # 2. Monitor with custom IP and 2-second interval:
  ./$(basename "$0") 192.168.1.100 2

  # 3. Monitor continuously and log to CSV:
  ./$(basename "$0") -l ma35d16fj87c_temp.csv

  # 4. Read 60 times (1 minute) with 1-second interval:
  ./$(basename "$0") -c 60 -i 1

Press [Ctrl+C] at any time to stop monitoring and view summary report.
EOF
}

# --- Command Line Argument Parsing ---
POSITIONAL_1=""
POSITIONAL_2=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -H|--host)
            BMC_IP="$2"
            shift 2
            ;;
        -u|--user)
            USER="$2"
            shift 2
            ;;
        -p|--pass|--password)
            PASS="$2"
            shift 2
            ;;
        -i|--interval)
            INTERVAL="$2"
            shift 2
            ;;
        -c|--count)
            MAX_COUNT="$2"
            shift 2
            ;;
        -l|--log)
            if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                LOG_FILE="$2"
                shift 2
            else
                LOG_FILE="numaker-iot-ma35d16fj87c-temp.csv"
                shift 1
            fi
            ;;
        --csv)
            CSV_STDOUT=1
            shift
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}" >&2
            show_help
            exit 1
            ;;
        *)
            if [ -z "$POSITIONAL_1" ]; then
                POSITIONAL_1="$1"
                BMC_IP="$1"
            elif [ -z "$POSITIONAL_2" ]; then
                POSITIONAL_2="$1"
                INTERVAL="$1"
            fi
            shift
            ;;
    esac
done

# Initialize CSV log file if enabled
if [ -n "$LOG_FILE" ]; then
    echo "Timestamp,Sample,Temperature_C,Min_C,Max_C,Avg_C,Health,State" > "$LOG_FILE"
fi

# Print summary on exit
print_summary() {
    local END_TIME=$(date +%s)
    local ELAPSED=$((END_TIME - START_TIME))

    if [ "$CSV_STDOUT" -eq 1 ]; then
        exit 0
    fi

    echo -e "\n${BLUE}================================================================${NC}"
    echo -e "       ${BOLD}CPU Temperature Monitoring Session Summary${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo -e "  Target Board:     ${CYAN}NuMaker-IoT-MA35D16FJ87C (${BMC_IP})${NC}"
    echo -e "  Sensor URI:       ${DIM}${SENSOR_ENDPOINT}${NC}"
    echo -e "  Elapsed Time:     ${ELAPSED} seconds"
    echo -e "  Total Readings:   ${SAMPLE_COUNT} (Failed: ${ERROR_COUNT})"

    if [ "$SAMPLE_COUNT" -gt 0 ] && [ -n "$MIN_TEMP" ]; then
        local AVG_TEMP=$(awk -v sum="$SUM_TEMP" -v cnt="$SAMPLE_COUNT" 'BEGIN { if (cnt > 0) printf "%.3f", sum/cnt; else print "N/A" }')
        echo -e "  Min Temperature:  ${GREEN}${MIN_TEMP} °C${NC}"
        echo -e "  Max Temperature:  ${YELLOW}${MAX_TEMP} °C${NC}"
        echo -e "  Avg Temperature:  ${CYAN}${AVG_TEMP} °C${NC}"
        echo -e "  Thresholds:       Warning=${WARN_THRESHOLD}°C, Critical=${CRIT_THRESHOLD}°C"
    else
        echo -e "  ${YELLOW}No valid temperature readings recorded.${NC}"
    fi

    if [ -n "$LOG_FILE" ]; then
        echo -e "  CSV Log File:     ${GREEN}${LOG_FILE}${NC} ($(wc -l < "$LOG_FILE") lines)"
    fi
    echo -e "${BLUE}================================================================${NC}"
}

# Trap SIGINT and SIGTERM for graceful exit
trap 'print_summary; exit 0' INT TERM

# Render ASCII/Unicode temperature gauge bar: scale 25°C - 105°C, 15 chars wide
render_gauge() {
    local val=$1
    awk -v cur="$val" -v min_s=25 -v max_s=105 -v w=15 'BEGIN {
        pct = (cur - min_s) / (max_s - min_s);
        if (pct < 0) pct = 0;
        if (pct > 1) pct = 1;
        filled = int(pct * w + 0.5);
        bar = "";
        for (i = 0; i < filled; i++) bar = bar "■";
        for (i = filled; i < w; i++) bar = bar "·";
        print bar;
    }'
}

# Print Banner (if not purely piping CSV)
if [ "$CSV_STDOUT" -eq 1 ]; then
    echo "Timestamp,Sample,Temperature_C,Min_C,Max_C,Avg_C,Health,State"
else
    echo -e "${BLUE}================================================================${NC}"
    echo -e "   ${BOLD}NuMaker-IoT-MA35D16FJ87C - Real-Time CPU Temperature Monitor${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo -e "  ${BOLD}Target BMC:${NC}       ${CYAN}https://${BMC_IP}${NC}"
    echo -e "  ${BOLD}Sensor Endpoint:${NC}  ${DIM}${SENSOR_ENDPOINT}${NC}"
    echo -e "  ${BOLD}Poll Interval:${NC}    ${INTERVAL}s"
    if [ "$MAX_COUNT" -gt 0 ]; then
        echo -e "  ${BOLD}Planned Count:${NC}    ${MAX_COUNT} readings"
    else
        echo -e "  ${BOLD}Mode:${NC}             ${GREEN}Continuous (unlimited)${NC}"
    fi
    if [ -n "$LOG_FILE" ]; then
        echo -e "  ${BOLD}Log File:${NC}         ${GREEN}${LOG_FILE}${NC}"
    fi
    echo -e "  ${BOLD}Control:${NC}          Press ${YELLOW}[Ctrl+C]${NC} to exit and view summary"
    echo -e "${BLUE}----------------------------------------------------------------${NC}"
fi

# Main Polling Loop
while true; do
    # Check if max count reached
    if [ "$MAX_COUNT" -gt 0 ] && [ "$SAMPLE_COUNT" -ge "$MAX_COUNT" ]; then
        break
    fi

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Query Redfish Sensor Endpoint
    # Returns HTTP code on the last line, JSON body above
    CURL_OUT=$(curl -k -s -u "${USER}:${PASS}" \
        --connect-timeout 4 \
        --max-time 6 \
        -w "\n%{http_code}" \
        "https://${BMC_IP}${SENSOR_ENDPOINT}" 2>/dev/null)

    HTTP_CODE=$(echo "$CURL_OUT" | tail -n1)
    JSON_BODY=$(echo "$CURL_OUT" | sed '$d')

    if [ "$HTTP_CODE" -eq 200 ] && [ -n "$JSON_BODY" ]; then
        # Parse fields (support jq if available, fallback to awk/grep)
        if command -v jq &>/dev/null; then
            READING=$(echo "$JSON_BODY" | jq -r '.Reading // empty' 2>/dev/null)
            HEALTH=$(echo "$JSON_BODY" | jq -r '.Status.Health // "OK"' 2>/dev/null)
            STATE=$(echo "$JSON_BODY" | jq -r '.Status.State // "Enabled"' 2>/dev/null)
            CAUTION_DYN=$(echo "$JSON_BODY" | jq -r '.Thresholds.UpperCaution.Reading // empty' 2>/dev/null)
            CRIT_DYN=$(echo "$JSON_BODY" | jq -r '.Thresholds.UpperCritical.Reading // empty' 2>/dev/null)
            [ -n "$CAUTION_DYN" ] && WARN_THRESHOLD="$CAUTION_DYN"
            [ -n "$CRIT_DYN" ] && CRIT_THRESHOLD="$CRIT_DYN"
        else
            READING=$(echo "$JSON_BODY" | grep -o '"Reading": *[0-9.]*' | awk '{print $2}')
            HEALTH=$(echo "$JSON_BODY" | grep -o '"Health": *"[^"]*"' | cut -d'"' -f4)
            STATE=$(echo "$JSON_BODY" | grep -o '"State": *"[^"]*"' | cut -d'"' -f4)
            [ -z "$HEALTH" ] && HEALTH="OK"
            [ -z "$STATE" ] && STATE="Enabled"
        fi

        if [ -n "$READING" ] && [[ "$READING" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
            SAMPLE_COUNT=$((SAMPLE_COUNT + 1))

            # Update Min / Max / Running Sum
            STATS=$(awk -v cur="$READING" -v min="$MIN_TEMP" -v max="$MAX_TEMP" -v sum="$SUM_TEMP" -v cnt="$SAMPLE_COUNT" 'BEGIN {
                if (min == "" || cur < min) min = cur;
                if (max == "" || cur > max) max = cur;
                sum += cur;
                avg = sum / cnt;
                printf "%.3f %.3f %.3f %.3f\n", min, max, avg, sum;
            }')
            MIN_TEMP=$(echo "$STATS" | awk '{print $1}')
            MAX_TEMP=$(echo "$STATS" | awk '{print $2}')
            AVG_TEMP=$(echo "$STATS" | awk '{print $3}')
            SUM_TEMP=$(echo "$STATS" | awk '{print $4}')

            # Write to CSV log file if enabled
            if [ -n "$LOG_FILE" ]; then
                echo "${TIMESTAMP},${SAMPLE_COUNT},${READING},${MIN_TEMP},${MAX_TEMP},${AVG_TEMP},${HEALTH},${STATE}" >> "$LOG_FILE"
            fi

            if [ "$CSV_STDOUT" -eq 1 ]; then
                echo "${TIMESTAMP},${SAMPLE_COUNT},${READING},${MIN_TEMP},${MAX_TEMP},${AVG_TEMP},${HEALTH},${STATE}"
            else
                # Determine display color and alert status
                IS_CRIT=$(awk -v cur="$READING" -v crit="$CRIT_THRESHOLD" 'BEGIN { print (cur >= crit) ? 1 : 0 }')
                IS_WARN=$(awk -v cur="$READING" -v warn="$WARN_THRESHOLD" 'BEGIN { print (cur >= warn) ? 1 : 0 }')

                if [ "$IS_CRIT" -eq 1 ]; then
                    TEMP_COLOR="${RED}${BOLD}"
                    STATUS_TAG="[CRITICAL ALERT >= ${CRIT_THRESHOLD}°C]"
                elif [ "$IS_WARN" -eq 1 ]; then
                    TEMP_COLOR="${YELLOW}${BOLD}"
                    STATUS_TAG="[WARNING >= ${WARN_THRESHOLD}°C]"
                else
                    TEMP_COLOR="${GREEN}"
                    STATUS_TAG="[${HEALTH}]"
                fi

                GAUGE=$(render_gauge "$READING")

                # Formatted sample output line
                printf "[%s] #%05d | Temp: %b%6.3f °C%b [%b%s%b] | Min: %6.3f°C | Max: %6.3f°C | Avg: %6.3f°C | %b%s%b\n" \
                    "$TIMESTAMP" \
                    "$SAMPLE_COUNT" \
                    "$TEMP_COLOR" "$READING" "$NC" \
                    "$TEMP_COLOR" "$GAUGE" "$NC" \
                    "$MIN_TEMP" \
                    "$MAX_TEMP" \
                    "$AVG_TEMP" \
                    "$TEMP_COLOR" "$STATUS_TAG" "$NC"
            fi
        else
            ERROR_COUNT=$((ERROR_COUNT + 1))
            if [ "$CSV_STDOUT" -eq 0 ]; then
                echo -e "[${TIMESTAMP}] ${RED}[ERROR] Invalid reading payload received from sensor${NC}"
            fi
        fi
    else
        ERROR_COUNT=$((ERROR_COUNT + 1))
        if [ "$CSV_STDOUT" -eq 0 ]; then
            echo -e "[${TIMESTAMP}] ${RED}[ERROR] Failed to connect to BMC (HTTP ${HTTP_CODE:-000}) - Retrying in ${INTERVAL}s...${NC}"
        fi
    fi

    # Wait for the specified interval before the next poll
    sleep "$INTERVAL"
done

print_summary
exit 0
