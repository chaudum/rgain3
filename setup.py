#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys

from rgain import __version__
from rgain.distutils import manpages_args

try:
    from setuptools import setup
except ImportError:
    print("setuptools unavailable, falling back to distutils.", file=sys.stderr)
    from distutils.core import setup


setup(
    name="rgain",
    version=__version__,
    description="Multi-format Replay Gain utilities",
    author="Felix Krull",
    author_email="f_krull@gmx.de",
    url="http://bitbucket.org/fk/rgain",
    license="GNU General Public License (v2 or later)",
    classifiers=[
        "Development Status :: 7 - Inactive",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    long_description="""\
A set of Python modules and utility programmes to deal with Replay Gain
information -- calculate it (with GStreamer), read and write it (with Mutagen).
It has support for Ogg Vorbis (or probably anything stored in an Ogg
container), Flac, WavPack, MP4 (aka AAC) and MP3 (in different incarnations).
There‘s also a command-line programme, ``replaygain``, that works very similar
to its like-named cousins, most prominently ``vorbisgain`` and ``mp3gain`` --
only that itworks for all those supported formats alike. ``collectiongain``
on the other hand is a kind of fire-and-forget tool for big amounts of music
files.

NOTE: rgain is currently not being developed; for more information or if you'd
like to help remedying this situation, see:
https://bitbucket.org/fk/rgain/issues/26/wanted-new-maintainer
""",

    packages=["rgain", "rgain.script"],
    scripts=["scripts/replaygain", "scripts/collectiongain"],
    install_requires=["pygobject", "mutagen"],
    python_requires=">=3.5",

    **manpages_args
)
