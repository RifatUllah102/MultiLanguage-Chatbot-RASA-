#!/bin/bash
set -x

# Make the script runnable from any directory
cd `dirname "$0"`

# Error handling
set -o errexit          # Exit on most errors
set -o errtrace         # Make sure any error trap is inherited
set -o pipefail         # Use last non-zero exit code in a pipeline

#if [ ! -f "docker-compose.yml" ]; then
#  echo "docker-compose.yml not found. Have you deleted it by any chance?"
#  exit 1;
#fi

function start() {
  echo "Starting all services .."

  docker-compose -f "$1/docker-compose.yml" up -d
  if [ $? -eq 0 ]; then
    echo "All done"
  else
    echo "One or more services failed to start. The bot might not work as expected."
  fi
}

function stop() {
  echo "Shutting down .."
  docker-compose down
  if [ $? -eq 0 ]; then
    echo "All done"
  else
    echo "One or more services failed to shut down. Check for running Docker containers and shut them down"
  fi
}

function train() {
  if [ $# -ne 2 ]; then
    echo "Please provide project location (ex: examples/rasa_demo) and the target language (ex: en)"
  else
    train_model_locale "$1" "$2"
  fi
}

function train_model_locale() {
  config_root="$1/config/models/$2"
  config="$config_root/config.yml"
  domain="$config_root/domain.yml"
  data="$config_root/data"

  if [ ! -f "$config" ] || [ ! -f "$domain" ] || [ ! -d "$data" ]; then
    echo "Missing config and / or data for model '$1', locale '$2'. Make sure to add them and try again."
    exit 1
  fi

  docker run -v $(pwd):/app \
    rasa/rasa:1.6.0-full train \
    --config "$config" \
    --domain "$domain" \
    --data "$data" \
    --out "$1/models" \
    --fixed-model-name "chat-model-$2"
}

function interactive_learning() {
  if [ $# -ne 2 ]; then
    echo "Please provide model directory and locale, for example: demo en"
    exit 1
  fi

  start $1

  if [ $? -eq 0 ]; then
    config_root="$1/config/models/$2"
    echo "Starting interactive learning session .."
    docker-compose -f "$1/docker-compose.yml" run rasa interactive --verbose -c "$config_root" -m "$config_root/models/chat-model-$2.tar.gz" --endpoints "$1/config/endpoints.yml"
    echo "All done, happy learning ;-)"
  else
    echo "Services failed to start, exiting .."
    exit 1
  fi

}

function show_help() {
    echo "Usage:"
    echo "  start             .. starts all services. Once done, visit http://localhost:8080"
    echo "  stop              .. stops all services and discards docker containers"
    echo "  train [locale]    .. (re)trains the models using stories and nlu data."
    echo "                       takes an optional argument - a locale, currently *en* or *de*, to retrain a selected model"
    echo "                       when no arguments are passed, all models will be retrained"
    echo "  interactive       .. runs an interactive learning session, where you can help the bot learn to correctly recognize intents"
}

case "$1" in
  -h | --help)
    show_help
    exit 0
    ;;
  "start")
    start
    ;;
  "stop")
    stop
    ;;
  "train")
    train "$2" "$3"
    ;;
  "interactive")
    interactive_learning "$2" "$3"
    ;;
esac
