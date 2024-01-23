#!/bin/bash
# this file is meant to be used by glitch for initializing server
pip3 install poetry
poetry install
poetry shell
gunicorn main:app
