#!/usr/bin/python
# -*- coding: utf-8 -*-

from contextlib import closing
import os
from distutils.core import Command, Distribution, setup
from distutils.command.build import build
from distutils.errors import DistutilsOptionError
import docutils.core

class ManpagesDistribution(Distribution):
    def __init__(self, attrs=None):
        self.rst_manpages = None
        Distribution.__init__(self, attrs)

class build_manpages(Command):
    description = "Generate man pages."
    user_options = [
        ("outputdir=", "b", "output directory for man pages"),
    ]
    
    def initialize_options(self):
        self.rst_manpages = None
        self.outputdir = None
    
    def finalize_options(self):
        if not self.outputdir:
            self.outputdir = os.path.join("build", "man")
        self.rst_manpages = self.distribution.rst_manpages
    
    def run(self):
        if not self.rst_manpages:
            return
        if not os.path.exists(self.outputdir):
            os.makedirs(self.outputdir, mode=0755)
        for infile, outfile in self.rst_manpages:
            print "Converting %s to %s ..." % (infile, outfile),
            docutils.core.publish_file(source_path=infile,
                    destination_path=os.path.join(self.outputdir, outfile),
                    writer_name="manpage")
            print "ok"

build.sub_commands.append(("build_manpages", None))

setup(
    name="rgain",
    version="1.1",
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
    rst_manpages=[
        ("man/replaygain.rst", "replaygain.1"),
        ("man/collectiongain.rst", "collectiongain.1"),
    ],
    
    requires=["pygst", "mutagen"],
    
    cmdclass={"build_manpages": build_manpages},
    distclass=ManpagesDistribution
)

