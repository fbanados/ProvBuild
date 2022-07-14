#!/bin/bash
echo "Make sure you are running this script in the repo folder!"
sudo apt install -y python2 python-pip
sudo ln -s /usr/bin/python2 /usr/bin/python
pip2 install -r requirements.txt
echo "You can now run the server with 'python app.py'"
