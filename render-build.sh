#!/usr/bin/env bash

# Create bin directory to hold wkhtmltopdf
mkdir -p bin

# Download precompiled wkhtmltopdf binary (static version)
curl -L -o bin/wkhtmltopdf.tar.xz https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox-0.12.6-1-linux-generic-amd64.tar.xz

# Extract just the wkhtmltopdf executable
tar -xf bin/wkhtmltopdf.tar.xz --strip-components=2 -C bin wkhtmltox/bin/wkhtmltopdf

# Make it executable
chmod +x bin/wkhtmltopdf

# Optional: clean up archive
rm bin/wkhtmltopdf.tar.xz
