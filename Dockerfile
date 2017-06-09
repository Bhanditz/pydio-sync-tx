FROM python
ADD . /
RUN pip install -r requirements.txt
RUN mkdir -p /tmp/wspace ~/Pydio/My\ Files
RUN python setup.py develop
CMD twistd -noy pydio-sync.tac
