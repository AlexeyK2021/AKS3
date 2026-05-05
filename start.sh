#!/bin/bash


echo "1. Starting Control"
cd control
echo "1.0 Create .venv"
python3 -m venv .venv
echo "1.1 Downloading pip libraries"
./.venv/bin/pip3 install -r requirements.txt
echo "1.2 Starting Control"
./.venv/bin/python3 control_api.py > ../logs/control.log 2>&1 &

echo "2. Starting Garbage"
cd garbage
echo "2.0 Create .venv"
python3 -m venv .venv
echo "2.1 Downloading pip libraries"
./.venv/bin/pip3 install -r requirements.txt
echo "2.2 Starting Control"
./.venv/bin/python3 garbage_collector.py > ../logs/garbage.log 2>&1 &

echo "3. Starting Read"
cd read
echo "3.0 Create .venv"
python3 -m venv .venv
echo "3.1 Downloading pip libraries"
./.venv/bin/pip3 install -r requirements.txt
echo "3.2 Starting Read"
./.venv/bin/python3 read_api.py > ../logs/read.log 2>&1 &

echo "4. Starting Write"
cd write
echo "4.0 Create .venv"
python3 -m venv .venv
echo "4.1 Downloading pip libraries"
./.venv/bin/pip3 install -r requirements.txt
echo "4.2 Starting Write"
./.venv/bin/python3 write_api.py > ../logs/write.log 2>&1 &