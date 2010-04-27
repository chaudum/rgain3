#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name="rgain",
    version="1.0",
    description="Multi-format Replay Gain utilities",
    author="Felix Krull",
    author_email="f_krull@gmx.de",
    
    packages=["rgain", "rgain.script"],
    scripts=["scripts/replaygain", "scripts/collectiongain"],
    
    requires=["pygst", "mutagen"],
)

