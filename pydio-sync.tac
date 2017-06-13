import os
import os.path as osp

import yaml

from shutil import copyfile
from appdirs import user_data_dir

from twisted.application import service

# from pydio.web import UIServer, APIServer
from pydio.sched import Scheduler

APP_NAME = "pydio-sync"
USR_DATA_DIR = user_data_dir(
    appname=APP_NAME, appauthor="Abstrium SAS", roaming=True
)
TMP_DATA_DIR = '/tmp/wspace/'

# Initialize temp data directory if it doesn't exists
if not osp.exists(TMP_DATA_DIR):
	os.makedirs(TMP_DATA_DIR)

# Initialize user data directory if it hasn't been created
if not osp.exists(USR_DATA_DIR):
	os.makedirs(USR_DATA_DIR)

# Update config file
copyfile("config.yml", osp.join(USR_DATA_DIR, "config.yml"))

# Load app configuration
with open(osp.join(USR_DATA_DIR, "config.yml")) as f:
    cfg = yaml.safe_load(f)

# This is the core part of any tac file, the creation of the root-level
# application object.
application = service.Application(APP_NAME)

# load the scheduler component
sched = Scheduler(cfg)
sched.setServiceParent(application)

# load the webUI component
# ...
