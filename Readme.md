# Install
1. python -m venv /home/pi/venv3.7
2. source /home/pi/venv3.7/bin/activate
3. pip install -r requirements.txt

# Start
python main.py

# Run as a Service
## install
1. sudo cp mqttsensor-py.service /lib/systemd/system/
2. sudo systemctl daemon-reload
3. sudo systemctl enable mqttsensor-py.service
4. sudo systemctl start mqttsensor-py.service
## start, restart, status
- sudo systemctl status mqttsensor-py.service
- sudo systemctl stop mqttsensor-py.service
- sudo systemctl start mqttsensor-py.service
- sudo systemctl restart mqttsensor-py.service

