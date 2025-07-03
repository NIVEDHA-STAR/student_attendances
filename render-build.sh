#!/usr/bin/env bash

# Prepare bin folder
mkdir -p bin

# Download precompiled static Linux wkhtmltopdf
curl -L -o bin/wkhtmltopdf.tar.xz \
  https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox-0.12.6-1_linux-generic-amd64.tar.xz

# Extract only the binary into bin/
tar -xf bin/wkhtmltopdf.tar.xz --strip-components=2 -C bin wkhtmltox/bin/wkhtmltopdf

# Make it executable
chmod +x bin/wkhtmltopdf

# Cleanup archive
rm bin/wkhtmltopdf.tar.xz
