FROM python:latest

ADD . .
RUN pip install -r requirements.txt
RUN python setup.py develop
RUN mkdir -p ~/Pydio/My\ Files /tmp/wspace
