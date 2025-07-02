#!/usr/bin/env bash

# Step 1: Make a bin folder to hold the wkhtmltopdf binary
mkdir -p bin

# Step 2: Download wkhtmltopdf Linux binary
curl -L -o bin/wkhtmltopdf https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltopdf_0.12.6-1.bionic_amd64

# Step 3: Make it executable
chmod +x bin/wkhtmltopdf
