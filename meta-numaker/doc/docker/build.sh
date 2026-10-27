#!/bin/bash
# Build Docker image and create container for OpenBMC development

PROJECT_NAME=openbmc-numaker

if [ "$(whoami)" = "root" ]; then
    echo "ERROR: do not run this script as root. Exiting..."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"

SHARED_DIR="$HOME/shared"
echo "Docker shared folder will mount $SHARED_DIR"

if [ ! -d "$SHARED_DIR" ]; then
    mkdir -p "$SHARED_DIR"
    echo "Created shared directory: $SHARED_DIR"
fi

if [ -n "$REPO_ROOT" ] && [ -d "$REPO_ROOT" ]; then
    echo "Detected host OpenBMC repository: $REPO_ROOT"
fi

# Generate Dockerfile with current user's UID/username
cp Dockerfile Dockerfile_build
sed -i "s/--uid 30000/--uid $(id -u)/g" Dockerfile_build
sed -i "s/--create-home build/--create-home $(id -nu)/g" Dockerfile_build
sed -i "s|USER build|USER $(id -nu)|g" Dockerfile_build
sed -i "s|WORKDIR /home/build|WORKDIR /home/$(id -nu)|g" Dockerfile_build
sed -i "s|\"build ALL|\"$(id -nu) ALL|g" Dockerfile_build

# Build image (skip if already exists)
if ! sudo docker images | grep -q "${PROJECT_NAME}-$(id -nu)"; then
    echo "Building Docker image: ${PROJECT_NAME}-$(id -nu):v1 ..."
    if ! sudo docker build -f Dockerfile_build -t "${PROJECT_NAME}-$(id -nu):v1" .; then
        echo "ERROR: Failed to build Docker image."
        rm -f Dockerfile_build
        exit 1
    fi
else
    echo "Image ${PROJECT_NAME}-$(id -nu) already exists."
fi

# Create container (skip if already exists)
if ! sudo docker ps -a | grep -q "${PROJECT_NAME}_$(id -nu)"; then
    echo "Creating container: ${PROJECT_NAME}_$(id -nu) ..."
    
    DOCKER_MOUNTS=("-v" "$SHARED_DIR:/home/$(id -nu)/shared")
    CONTAINER_WORKDIR="/home/$(id -nu)"
    if [ -n "$REPO_ROOT" ] && [ -d "$REPO_ROOT" ]; then
        echo "Mounting host repo: $REPO_ROOT -> /home/$(id -nu)/openbmc"
        DOCKER_MOUNTS+=("-v" "$REPO_ROOT:/home/$(id -nu)/openbmc")
        CONTAINER_WORKDIR="/home/$(id -nu)/openbmc"
    fi

    if ! sudo docker create -it \
        -w "$CONTAINER_WORKDIR" \
        "${DOCKER_MOUNTS[@]}" \
        --name "${PROJECT_NAME}_$(id -nu)" \
        "${PROJECT_NAME}-$(id -nu):v1" bash; then
        echo "ERROR: Failed to create container."
        rm -f Dockerfile_build
        exit 1
    fi
else
    echo "Container ${PROJECT_NAME}_$(id -nu) already exists."
fi

rm -f Dockerfile_build
echo "Done. Use ./join.sh to enter the container."
