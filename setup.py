#!/usr/bin/env python

from setuptools import setup

setup(name='gem', 
      version='0.1', 
      description="Geocoding Engine Machine", 
      packages=['gem'],
      data_files=[('gem', ['gem/gazetteer.db'])])
