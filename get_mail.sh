#!/bin/sh

ENV=$(cat .venv)
. $WORKON_HOME/$ENV/bin/activate
cat /dev/stdin | python manage.py get_email
