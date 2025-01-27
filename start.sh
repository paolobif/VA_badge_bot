#!/bin/bash

# Start the Flask app
gunicorn app:app &

# Start the Discord bot
python main.py
