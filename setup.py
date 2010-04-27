#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name="rgain",
    version="1.0.1",
    description="Multi-format Replay Gain utilities",
    author="Felix Krull",
    author_email="f_krull@gmx.de",
    url="http://bitbucket.org/fk/rgain",
    license="GNU General Public License (v2 or later)",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 2",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    long_description="""\
A set of Python modules and utility programmes to deal with Replay Gain
information -- calculate it (with GStreamer), read and write it (with Mutagen).
It has support for Ogg Vorbis (or probably anything stored in an Ogg container),
Flac, WavPack (oddly enough) and MP3 (in different incarnations). There‘s also
a command-line programme, ``replaygain``, that works very similar to its like-
named cousins, most prominently ``vorbisgain`` and ``mp3gain`` -- only that it
works for all those supported formats alike. ``collectiongain`` on the other
hand is a kind of fire-and-forget tool for big amounts of music files.
""",
    
    packages=["rgain", "rgain.script"],
    scripts=["scripts/replaygain", "scripts/collectiongain"],
    
    requires=["pygst", "mutagen"],
)

