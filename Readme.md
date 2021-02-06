# Install
sudo vim /lib/systemd/system/mqttsensor-py.service
sudo systemctl daemon-reload
sudo systemctl enable mqttsensor-py.service
sudo systemctl start mqttsensor-py.service

# Start/Restart/Status
sudo systemctl status mqttsensor-py.service
sudo systemctl stop mqttsensor-py.service
sudo systemctl start mqttsensor-py.service
sudo systemctl restart mqttsensor-py.service

