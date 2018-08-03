#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright (c) 2016-2018 ESET
# Author: Marc-Etienne M.Léveillé <leveille@eset.com>
# See LICENSE file for redistribution.

from setuptools import setup

setup(name='ipyida',
      version='1.3',
      description='IDA plugin to embed the IPython console inside IDA',
      author='Marc-Etienne M.Léveillé',
      author_email='leveille@eset.com',
      url='https://www.github.com/eset/ipyida',
      packages=['ipyida'],
      install_requires=[
          'ipython>=4.6,<6',
          'ipykernel>=4.6',
          'qtconsole>=4.3',
          'pyzmq>=17.0.0',
      ],
      license="BSD",
      entry_points={
          "idapython_plugins": [
              "ipyida=ipyida.ida_plugin:IPyIDAPlugIn"
          ]
      })
