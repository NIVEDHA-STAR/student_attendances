#!/usr/bin/env bash

# Create bin folder
mkdir -p bin

# Download wkhtmltopdf (precompiled static Linux version)
curl -L -o bin/wkhtmltopdf.tar.xz https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox-0.12.6-1_linux-generic-amd64.tar.xz

# Extract the binary from the tar
tar -xf bin/wkhtmltopdf.tar.xz --strip-components=2 -C bin wkhtmltox/bin/wkhtmltopdf

# Make it executable
chmod +x bin/wkhtmltopdf

# Clean up archive
rm bin/wkhtmltopdf.tar.xz
