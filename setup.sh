# !/bin/bash

rm -fr .venv/
python3.6 -m venv .venv --prompt Harvester
.venv/bin/pip install --upgrade setuptools
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
