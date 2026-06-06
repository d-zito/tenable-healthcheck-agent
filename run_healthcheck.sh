#!/bin/bash

# Activate virtual environment and run the healthcheck agent
cd /Users/dzito/claude_projects/tenable-healthcheck-agent
source venv/bin/activate
python src/main.py >> logs/cron_$(date +\%Y\%m\%d).log 2>&1
