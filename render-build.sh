#!/usr/bin/env bash

# Download wkhtmltopdf precompiled binary
mkdir -p bin
curl -L -o bin/wkhtmltopdf https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltopdf_0.12.6-1.buster_amd64.deb

# Install .deb and extract binary
sudo apt-get update && sudo apt-get install -y gdebi-core
sudo gdebi -n bin/wkhtmltopdf

# Make it executable
chmod +x /usr/local/bin/wkhtmltopdf
