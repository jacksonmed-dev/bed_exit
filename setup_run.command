#!/usr/bin/env bash

source ./venv/bin/activate

pip3 install -r requirements.txt

python3 ./test_write.py
