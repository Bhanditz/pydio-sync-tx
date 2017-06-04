# pydio-sync-tx
Temporary Repository for massive pydio-sync refactoring

# License
Copyright 2017, Abstrium SAS.  All rights reserved.

# For Developers

## Installation

After cloning the repository, install the python package

```
cd pydio-sync-tx/
python setup.py develop
```

Initialize a couple of workspaces.  `~/Pydio/My Files` is standard.  The other is a temporary stand-in for the sync server.
This will eventually be handled by the application itself.

```
mkdir -p /tmp/wspace ~/Pydio/My\ Files
```

Running the application should initialize the data directory and job configuration.

```
twistd -noy pydio-sync.tac
```

## Running unit tests

From project root:

```
$ trial pydio
```
