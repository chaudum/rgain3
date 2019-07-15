import os
import sys
import tempfile
from datetime import date
from distutils.command.build import build

from rgain import __version__

try:
    from setuptools import Command, Distribution
except ImportError:
    print("setuptools unavailable, falling back to distutils.", file=sys.stderr)
    from distutils.core import Command, Distribution

try:
    import docutils.core
except ImportError:
    print("docutils not found, manpages won't be generated.", file=sys.stderr)
    DOCUTILS_AVAILABLE = False
else:
    DOCUTILS_AVAILABLE = True


class ManpagesDistribution(Distribution):
    def __init__(self, *args, **kwargs):
        self.rst_manpages = None
        self.rst_manpages_update_info = False
        self.rst_manpages_version = None
        self.rst_manpages_date = None
        super().__init__(*args, **kwargs)


class ManpageBuildCommand(Command):
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
                print("Updating {} info...".format(infile), end="")
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

            print("Converting {} to {} ...".format(infile, outfile), end="")
            docutils.core.publish_file(
                source_path=real_infile,
                destination_path=os.path.join(self.outputdir, outfile),
                writer_name="manpage")
            if real_infile != infile:
                os.remove(real_infile)
            print("ok")


if DOCUTILS_AVAILABLE:
    build.sub_commands.append(("ManpageBuildCommand", None))
    manpages_args = {
        "rst_manpages": [
            ("man/replaygain.rst", "replaygain.1"),
            ("man/collectiongain.rst", "collectiongain.1"),
        ],
        "rst_manpages_update_info": True,
        "rst_manpages_version": __version__,
        "rst_manpages_date": date.today(),
        "cmdclass": {"build_manpages": ManpageBuildCommand},
        "distclass": ManpagesDistribution,
    }
else:
    manpages_args = {}
