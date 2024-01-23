#!/bin/bash
# this file is meant to be used by glitch for initializing server
pip3 install flask gunicorn
gunicorn main:app -b 0.0.0.0:3000
