#!/bin/bash
if which brew >/dev/null; then
	echo "Brew exist, continuing...";
else
	/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
fi

if which pip >/dev/null; then
	echo "Pip exist, continuing...";
else
	brew install python
	brew install pip
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
