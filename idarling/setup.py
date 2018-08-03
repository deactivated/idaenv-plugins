#!/usr/bin/env python

import sys
from setuptools import setup


# Install PyQt5 for the server if installing into Python 3
requires = []
if sys.version_info[0] == 3:
    requires.append("PyQt5")


setup(name='idarling',
      version='0.1',
      description='Collaborative Reverse Engineering plugin for IDA Pro',
      url='https://github.com/IDArlingTeam/IDArling/',
      packages=['idarling'],
      install_requires=requires,
      entry_points={
          "idapython_plugins": [
              "idarling=idarling.plugin:Plugin"
          ],
          "console_scripts": [
              "idarling_server=idarling.server:main"
          ]
      })
