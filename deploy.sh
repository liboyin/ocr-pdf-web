#!/bin/bash

set -eo pipefail

# Initialize build flag
BUILD=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --build) BUILD=true ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
    shift
done

# Check if we need to build
if [ "$BUILD" = true ] || ! docker image inspect ocr-pdf-web >/dev/null 2>&1; then
    echo "Building Docker image..."
    docker build -t ocr-pdf-web .
else
    echo "Using existing Docker image..."
fi

# Create network if it doesn't exist
if ! docker network inspect local-network >/dev/null 2>&1; then
    echo "Creating Docker network: local-network"
    docker network create local-network
else
    echo "Docker network local-network already exists"
fi

docker run --name ocr-pdf-web-app -d --rm --network local-network -p 8502:8502 ocr-pdf-web
