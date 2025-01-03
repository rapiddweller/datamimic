#!/bin/bash

echo "Run script to set local env"
# Check if ".env.example" file exists
if [[ -e .env.example ]]; then
	cp .env.example .env
	echo "Renamed .env.example to .env"
else
	echo "No '.env.example' file found in the current directory. Please set up the .env file manually"
fi
