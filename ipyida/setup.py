#!/usr/bin/env python
# -*- encoding: utf8 -*-
#
# Copyright (c) 2016-2018 ESET
# Author: Marc-Etienne M.Léveillé <leveille@eset.com>
# See LICENSE file for redistribution.

from distutils.core import setup

setup(name='ipyida',
      version='1.3',
      description='IDA plugin to embed the IPython console inside IDA',
      author='Marc-Etienne M.Léveillé',
      author_email='leveille@eset.com',
      url='https://www.github.com/eset/ipyida',
      packages=['ipyida'],
      install_requires=[
          'ipykernel>=4.6',
          'qtconsole>=4.3'
      ],
      license="BSD",
)
