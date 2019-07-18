from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution("rgain").version
except DistributionNotFound:
    # rgain package is not installed
    __version__ = None
