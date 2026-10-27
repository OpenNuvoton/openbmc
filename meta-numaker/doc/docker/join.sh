#!/bin/bash
# Enter the OpenBMC development container

PROJECT_NAME=openbmc-numaker
CONTAINER_NAME="${PROJECT_NAME}_$(id -nu)"

if ! sudo docker ps -a | grep -q "${CONTAINER_NAME}"; then
    echo "Container ${CONTAINER_NAME} does not exist."
    echo "Run ./build.sh first to create it."
    exit 1
fi

sudo docker start "${CONTAINER_NAME}" >/dev/null

# Enter container: default to mounted repo (~/openbmc) if present, otherwise home
sudo docker exec -u "$(id -nu)" -w "/home/$(id -nu)/openbmc" -it "${CONTAINER_NAME}" bash 2>/dev/null || \
sudo docker exec -u "$(id -nu)" -it "${CONTAINER_NAME}" bash
