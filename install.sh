#!/bin/bash

if which easy_install >/dev/null; then
	echo "Easy install exist, continue";
else
	curl https://bootstrap.pypa.io/ez_setup.py -o - | sudo python
	sudo easy_install pip
fi

brew install libusb
sudo ln -s `brew --prefix`/lib/libusb-* /usr/local/lib/

brew install terminal-notifier

pip install blinkstick
pip install python-daemon
pip install requests
pip install pyobjc-framework-Quartz
pip install pync
pip install psutil
