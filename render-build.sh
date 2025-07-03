#!/usr/bin/env bash

mkdir -p bin
curl -L -o bin/wkhtmltopdf.tar.xz https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox-0.12.6-1_linux-generic-amd64.tar.xz
tar -xf bin/wkhtmltopdf.tar.xz --strip-components=2 -C bin wkhtmltox/bin/wkhtmltopdf
chmod +x bin/wkhtmltopdf
rm bin/wkhtmltopdf.tar.xz
