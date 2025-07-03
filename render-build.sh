#!/usr/bin/env bash

# Create bin directory if not exists
mkdir -p bin

# Download wkhtmltopdf Linux binary
curl -L -o bin/wkhtmltopdf.tar.xz https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox-0.12.6-1_linux-generic-amd64.tar.xz

# Extract wkhtmltopdf binary only
tar -xf bin/wkhtmltopdf.tar.xz --strip-components=2 -C bin wkhtmltox/bin/wkhtmltopdf

# Make it executable
chmod +x bin/wkhtmltopdf

# Remove archive to clean up
rm bin/wkhtmltopdf.tar.xz
