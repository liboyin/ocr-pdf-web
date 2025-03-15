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

docker run --name ocr-pdf-web-app -d --rm -p 8502:8502 ocr-pdf-web
