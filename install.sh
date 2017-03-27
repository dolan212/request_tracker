#!/bin/sh

VE_NAME="dylan_ve"

if [! -d "$VE_NAME" ]; then
	virtualenv -q $VE_NAME --no-site-packages
	echo "Virtualenv created with name $VE_NAME."
fi

. $VE_NAME/bin/activate
pip install -r requirements.txt $VE_NAME
echo "Requirements installed."
echo $VE_NAME > .venv


