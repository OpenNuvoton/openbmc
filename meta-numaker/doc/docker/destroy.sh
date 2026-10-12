#!/bin/bash
# Destroy Docker container and image for OpenBMC development (orthogonal to build.sh)

PROJECT_NAME=openbmc-numaker
CONTAINER_NAME="${PROJECT_NAME}_$(id -nu)"
IMAGE_NAME="${PROJECT_NAME}-$(id -nu):v1"

if [ "$(whoami)" = "root" ]; then
    echo "ERROR: do not run this script as root. Exiting..."
    exit 1
fi

MODE="all"

while [ "$#" -gt 0 ]; do
    case "$1" in
        -c|--container-only)
            MODE="container"
            shift
            ;;
        -i|--image-only)
            MODE="image"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Teardown script orthogonal to build.sh for ${PROJECT_NAME}."
            echo ""
            echo "Options:"
            echo "  (no arguments)        Remove both container and image (full destroy)"
            echo "  -c, --container-only  Stop and remove container only (keep image for fast re-create)"
            echo "  -i, --image-only      Remove Docker image only"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

# 1. Stop and remove container
if [ "$MODE" = "all" ] || [ "$MODE" = "container" ]; then
    if sudo docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
        if sudo docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
            echo "Stopping container: ${CONTAINER_NAME} ..."
            sudo docker stop "${CONTAINER_NAME}"
        fi
        echo "Removing container: ${CONTAINER_NAME} ..."
        sudo docker rm "${CONTAINER_NAME}"
    else
        echo "Container ${CONTAINER_NAME} does not exist (skipped)."
    fi
fi

# 2. Remove Docker image
if [ "$MODE" = "all" ] || [ "$MODE" = "image" ]; then
    if sudo docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}\$"; then
        echo "Removing Docker image: ${IMAGE_NAME} ..."
        sudo docker rmi "${IMAGE_NAME}"
    else
        echo "Image ${IMAGE_NAME} does not exist (skipped)."
    fi
fi

# Clean up any leftover temporary build files
rm -f Dockerfile_build

echo "Done. Shared directory on host remains intact."
