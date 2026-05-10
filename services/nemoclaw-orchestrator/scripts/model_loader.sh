#!/bin/bash
# NemoClaw Model Loader
#
# This script provides easy model loading and switching for NemoClaw.
# It supports loading GGUF models into Ollama and managing model configurations.
#
# Usage: ./model_loader.sh [command] [options]
#
# Commands:
#   list                    List all available models
#   load <model>            Load a specific model into Ollama
#   unload <model>          Unload a model from Ollama
#   status                  Show current model status
#   switch <model>          Switch to a different model (update .env)
#   test <model>            Test a model with a simple prompt
#   help                    Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
GGUF_BASE_PATH="${CHIMERA_GGUF_BASE:-$HOME/Project_Chimera_Downloads/LLM Models/gguf}"
OLLAMA_ENDPOINT="http://localhost:11434"

# Model definitions
declare -A MODELS=(
    # Ollama built-in models
    ["llama3:instruct"]="Ollama built-in - 4GB"
    ["llama3:8b"]="Ollama built-in - 4.7GB"

    # GGUF models (need to be loaded)
    ["llama-3.1-8b-instruct"]="Meta Llama 3.1 8B Instruct - 4.6GB GGUF"
    ["bsl-phase7"]="BSL Phase 7 model - GGUF"
    ["bsl-phase8"]="BSL Phase 8 model - GGUF"
    ["bsl-phase9"]="BSL Phase 9 model - GGUF"
    ["director-v4"]="Director v4 model - GGUF"
    ["director-v5"]="Director v5 model - GGUF"
    ["scenespeak-queryd"]="SceneSpeak QueryD model - GGUF"
)

declare -A GGUF_PATHS=(
    ["llama-3.1-8b-instruct"]="other/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    ["bsl-phase7"]="bsl-phases/bsl_phase7.Q4_K_M.gguf"
    ["bsl-phase8"]="bsl-phases/bsl_phase8.Q4_K_M.gguf"
    ["bsl-phase9"]="bsl-phases/bsl_phase9.Q4_K_M.gguf"
    ["director-v4"]="directors/director_v4.Q4_K_M.gguf"
    ["director-v5"]="directors/director_v5.Q4_K_M.gguf"
    ["scenespeak-queryd"]="scene-speak/scenespeak_queryd.Q4_K_M.gguf"
)

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_ollama() {
    if ! command -v ollama &> /dev/null; then
        log_error "Ollama is not installed or not in PATH"
        return 1
    fi

    if ! curl -s "$OLLAMA_ENDPOINT/api/tags" > /dev/null 2>&1; then
        log_error "Ollama service is not running at $OLLAMA_ENDPOINT"
        log_info "Start Ollama with: systemctl start ollama"
        return 1
    fi

    return 0
}

check_gguf_file() {
    local model=$1
    local gguf_path="${GGUF_PATHS[$model]}"
    local full_path="$GGUF_BASE_PATH/$gguf_path"

    if [[ ! -f "$full_path" ]]; then
        log_error "GGUF file not found: $full_path"
        return 1
    fi

    return 0
}

# Commands
cmd_list() {
    echo -e "${CYAN}=== Available Models ===${NC}"
    echo ""

    echo -e "${YELLOW}Ollama Built-in Models:${NC}"
    for model in "${!MODELS[@]}"; do
        if [[ ! "${GGUF_PATHS[$model]+isset}" ]]; then
            local status
            if ollama list 2>/dev/null | grep -q "^${model}"; then
                status="${GREEN}[LOADED]${NC}"
            else
                status="${YELLOW}[AVAILABLE]${NC}"
            fi
            echo -e "  $status ${CYAN}${model}${NC} - ${MODELS[$model]}"
        fi
    done

    echo ""
    echo -e "${YELLOW}GGUF Models (require loading):${NC}"
    for model in "${!GGUF_PATHS[@]}"; do
        local status
        if ollama list 2>/dev/null | grep -q "^${model}"; then
            status="${GREEN}[LOADED]${NC}"
        else
            status="${YELLOW}[NOT LOADED]${NC}"
        fi
        echo -e "  $status ${CYAN}${model}${NC} - ${MODELS[$model]}"
    done
}

cmd_load() {
    local model=$1

    if [[ -z "$model" ]]; then
        log_error "Please specify a model to load"
        echo "Usage: $0 load <model>"
        exit 1
    fi

    if [[ ! "${MODELS[$model]+isset}" ]]; then
        log_error "Unknown model: $model"
        echo "Use '$0 list' to see available models"
        exit 1
    fi

    # Check if it's a GGUF model
    if [[ "${GGUF_PATHS[$model]+isset}" ]]; then
        log_info "Loading GGUF model: $model"

        if ! check_gguf_file "$model"; then
            exit 1
        fi

        local gguf_path="${GGUF_PATHS[$model]}"
        local full_path="$GGUF_BASE_PATH/$gguf_path"

        log_info "Loading from: $full_path"

        if ollama create "$model" --from "$full_path"; then
            log_success "Model $model loaded successfully"
        else
            log_error "Failed to load model $model"
            exit 1
        fi
    else
        log_warning "Model $model is an Ollama built-in model"
        log_info "Pull it with: ollama pull $model"
    fi
}

cmd_unload() {
    local model=$1

    if [[ -z "$model" ]]; then
        log_error "Please specify a model to unload"
        echo "Usage: $0 unload <model>"
        exit 1
    fi

    log_info "Unloading model: $model"

    if ollama rm "$model"; then
        log_success "Model $model unloaded successfully"
    else
        log_error "Failed to unload model $model"
        exit 1
    fi
}

cmd_status() {
    echo -e "${CYAN}=== NemoClaw Model Status ===${NC}"
    echo ""

    if ! check_ollama; then
        exit 1
    fi

    echo -e "${YELLOW}Ollama Service:${NC} ${GREEN}Running${NC}"
    echo ""

    echo -e "${YELLOW}Loaded Models:${NC}"
    ollama list

    echo ""
    echo -e "${YELLOW}Current Configuration:${NC}"
    if [[ -f "$ENV_FILE" ]]; then
        grep -E "^OLLAMA_MODEL=|^ZAI_" "$ENV_FILE" | sed 's/^/  /'
    else
        log_warning ".env file not found at $ENV_FILE"
    fi
}

cmd_switch() {
    local model=$1

    if [[ -z "$model" ]]; then
        log_error "Please specify a model to switch to"
        echo "Usage: $0 switch <model>"
        exit 1
    fi

    if [[ ! "${MODELS[$model]+isset}" ]]; then
        log_error "Unknown model: $model"
        echo "Use '$0 list' to see available models"
        exit 1
    fi

    log_info "Switching to model: $model"

    # Ensure model is loaded
    if [[ "${GGUF_PATHS[$model]+isset}" ]]; then
        if ! ollama list 2>/dev/null | grep -q "^${model}"; then
            log_info "Model not loaded, loading now..."
            cmd_load "$model"
        fi
    fi

    # Update .env file
    if [[ -f "$ENV_FILE" ]]; then
        if grep -q "^OLLAMA_MODEL=" "$ENV_FILE"; then
            sed -i "s/^OLLAMA_MODEL=.*/OLLAMA_MODEL=$model/" "$ENV_FILE"
        else
            echo "OLLAMA_MODEL=$model" >> "$ENV_FILE"
        fi
        log_success "Updated .env with OLLAMA_MODEL=$model"
    else
        log_warning ".env file not found, creating it..."
        echo "OLLAMA_MODEL=$model" > "$ENV_FILE"
    fi

    log_success "Switched to model: $model"
    log_info "Restart NemoClaw service to apply changes"
}

cmd_test() {
    local model=$1

    if [[ -z "$model" ]]; then
        log_error "Please specify a model to test"
        echo "Usage: $0 test <model>"
        exit 1
    fi

    log_info "Testing model: $model"
    echo ""

    local prompt="Say hello in one sentence."

    if ollama run "$model" "$prompt" 2>/dev/null; then
        echo ""
        log_success "Model test passed"
    else
        echo ""
        log_error "Model test failed"
        exit 1
    fi
}

cmd_help() {
    cat << EOF
NemoClaw Model Loader

Usage: $0 [command] [options]

Commands:
    list                    List all available models
    load <model>            Load a specific model into Ollama
    unload <model>          Unload a model from Ollama
    status                  Show current model status
    switch <model>          Switch to a different model (update .env)
    test <model>            Test a model with a simple prompt
    help                    Show this help message

Examples:
    $0 list                              List all models
    $0 load llama-3.1-8b-instruct        Load GGUF model
    $0 switch llama-3.1-8b-instruct      Switch to GGUF model
    $0 test llama-3.1-8b-instruct       Test a model
    $0 status                            Show current status

GGUF Models:
    llama-3.1-8b-instruct    Meta Llama 3.1 8B Instruct (4.6GB)
    bsl-phase7               BSL Phase 7 model
    bsl-phase8               BSL Phase 8 model
    bsl-phase9               BSL Phase 9 model
    director-v4              Director v4 model
    director-v5              Director v5 model
    scenespeak-queryd        SceneSpeak QueryD model

Ollama Built-in Models:
    llama3:instruct          Llama 3 Instruct (4GB)
    llama3:8b                Llama 3 8B (4.7GB)
EOF
}

# Main
main() {
    if ! check_ollama; then
        case "${1:-}" in
            list|help)
                # These commands don't require Ollama running
                :
                ;;
            *)
                exit 1
                ;;
        esac
    fi

    local command="${1:-help}"
    shift || true

    case "$command" in
        list)
            cmd_list
            ;;
        load)
            cmd_load "$@"
            ;;
        unload)
            cmd_unload "$@"
            ;;
        status)
            cmd_status
            ;;
        switch)
            cmd_switch "$@"
            ;;
        test)
            cmd_test "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"
