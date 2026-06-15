#!/bin/bash
# Enter the OpenBMC development container

PROJECT_NAME=openbmc-numaker

if ! sudo docker ps -a | grep -q "${PROJECT_NAME}_$(id -nu)"; then
    echo "Container ${PROJECT_NAME}_$(id -nu) does not exist."
    echo "Run ./build.sh first to create it."
    exit 1
fi

sudo docker start "${PROJECT_NAME}_$(id -nu)"
sudo docker exec -u "$(id -nu)" -it "${PROJECT_NAME}_$(id -nu)" bash
