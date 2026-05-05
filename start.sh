#!/bin/bash

mkdir logs
touch logs/control.log logs/garbage.log logs/read.log logs/write.log

echo "1. Starting Control"
echo "1.0 Create .venv"
python3 -m venv control/.venv
echo "1.1 Downloading pip libraries"
./.venv/bin/pip3 install -r control/requirements.txt
echo "1.2 Starting Control"
./.venv/bin/python3 control/control_api.py > logs/control.log 2>&1 &

echo "2. Starting Garbage"
echo "2.0 Create .venv"
python3 -m venv garbage/.venv
echo "2.1 Downloading pip libraries"
./.venv/bin/pip3 install -r garbage/requirements.txt
echo "2.2 Starting Control"
./.venv/bin/python3 garbage/garbage_collector.py > logs/garbage.log 2>&1 &

echo "3. Starting Read"
echo "3.0 Create .venv"
python3 -m venv read/.venv
echo "3.1 Downloading pip libraries"
./.venv/bin/pip3 install -r read/requirements.txt
echo "3.2 Starting Read"
./.venv/bin/python3 read/read_api.py > logs/read.log 2>&1 &

echo "4. Starting Write"
echo "4.0 Create .venv"
python3 -m venv write/.venv
echo "4.1 Downloading pip libraries"
./.venv/bin/pip3 install -r write/requirements.txt
echo "4.2 Starting Write"
./.venv/bin/python3 write/write_api.py > logs/write.log 2>&1 &