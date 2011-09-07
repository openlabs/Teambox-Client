=======================
Python API to Teambox
=======================


Example Usage
=============


```python

from teambox import Project
project_api = Project(username="username", password="password")

# Or if you have your inhouse installation of teambox
# project_api = Project(
#	base_url="https://my-inhouse-teambox.com", 
#	username="username", password="password")

# List all projects
project_api.index()

```

Documentation
=============

The documentation with source code is hosted on github at
http://openlabs.github.com/Teambox-Client/
