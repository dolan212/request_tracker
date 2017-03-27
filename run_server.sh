#!/bin/sh

ENV=$(cat .venv)
. $ENV/bin/activate
python manage.py runserver $1
