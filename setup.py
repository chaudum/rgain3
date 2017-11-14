#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

from datetime import date
import os
import sys
import tempfile

try:
    from setuptools import Command, Distribution, setup
except ImportError:
    print("setuptools unavailable, falling back to distutils.",
          file=sys.stderr)
    from distutils.core import Command, Distribution, setup
from distutils.command.build import build

from rgain import __version__

try:
    import docutils.core

    class ManpagesDistribution(Distribution):
        def __init__(self, attrs=None):
            self.rst_manpages = None
            self.rst_manpages_update_info = False
            self.rst_manpages_version = None
            self.rst_manpages_date = None
            Distribution.__init__(self, attrs)

    class build_manpages(Command):
        description = "Generate man pages."
        user_options = [
            ("outputdir=", "b", "output directory for man pages"),
        ]

        def initialize_options(self):
            self.rst_manpages = None
            self.rst_manpages_update_info = False
            self.rst_manpages_version = "1.0"
            self.rst_manpages_date = date.today()
            self.outputdir = None

        def finalize_options(self):
            if not self.outputdir:
                self.outputdir = os.path.join("build", "man")
            self.rst_manpages = self.distribution.rst_manpages
            self.rst_manpages_update_info = \
                self.distribution.rst_manpages_update_info
            self.rst_manpages_version = self.distribution.rst_manpages_version
            self.rst_manpages_date = self.distribution.rst_manpages_date

        def run(self):
            if not self.rst_manpages:
                return
            if not os.path.exists(self.outputdir):
                os.makedirs(self.outputdir, mode=0o755)
            for infile, outfile in self.rst_manpages:
                if self.rst_manpages_update_info:
                    print("Updating %s info..." % infile, end="")
                    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                        with open(infile, "r") as f:
                            for line in f:
                                if line.startswith(":Date:"):
                                    dt = self.rst_manpages_date
                                    tmp.write(
                                        ":Date: %s-%s-%s\n" %
                                        (dt.year, dt.month, dt.day))
                                elif line.startswith(":Version:"):
                                    tmp.write(":Version: %s\n" %
                                              self.rst_manpages_version)
                                else:
                                    tmp.write(line)
                    real_infile = tmp.name
                    print("ok")
                else:
                    real_infile = infile

                print("Converting %s to %s ..." % (infile, outfile), end="")
                docutils.core.publish_file(
                    source_path=real_infile,
                    destination_path=os.path.join(self.outputdir, outfile),
                    writer_name="manpage")
                if real_infile != infile:
                    os.remove(real_infile)
                print("ok")

    build.sub_commands.append(("build_manpages", None))
    manpages_args = {
        "rst_manpages": [
            ("man/replaygain.rst", "replaygain.1"),
            ("man/collectiongain.rst", "collectiongain.1"),
        ],
        "rst_manpages_update_info": True,
        "rst_manpages_version": __version__,
        "rst_manpages_date": date.today(),
        "cmdclass": {"build_manpages": build_manpages},
        "distclass": ManpagesDistribution,
    }
except ImportError:
    print("docutils not found, manpages won't be generated.", file=sys.stderr)
    manpages_args = {}

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
        "Programming Language :: Python :: 2",
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
    requires=["pygobject", "mutagen"],

    **manpages_args
)
