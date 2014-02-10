# -*- coding: utf-8 -*-
#
# Copyright (c) 2009-2014 Felix Krull <f_krull@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import contextlib
import multiprocessing
import cStringIO
import sys
import os.path
try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5
try:
    import cPickle as pickle
except ImportError:
    import pickle

import mutagen
from mutagen.id3 import TXXX

from rgain import albumid, rgio
from rgain.script import *
from rgain.script.replaygain import do_gain

CURRENT_CACHE_VERSION = 1

# all of collectiongain
def relpath(path, base):
    size = len(base)
    if os.path.basename(base):
        # this means ``base`` does not end with a separator
        size += 1
    return path[size:]

def cache_entry_valid(filepath, record):
    return (
        isinstance(filepath, basestring)
        and hasattr(record, "__getitem__")
        and hasattr(record, "__len__")
        and len(record) == 3
        and (isinstance(record[0], basestring)
             or record[0] is None)
        and (isinstance(record[1], int)
             or isinstance(record[1], float))
        and isinstance(record[2], bool))

def read_cache(cache_file):
    if os.path.isfile(cache_file):
        try:
            with open(cache_file, "rb") as f:
                cache = pickle.load(f)
                if not isinstance(cache, tuple) or len(cache) != 2:
                    print ou(u"Invalid cache, ignoring it")
                    return {}
                cache_version = cache[0]
                if cache_version != CURRENT_CACHE_VERSION:
                    print ou(u"Old cache format, ignoring it")
                    return {}
                files = cache[1]
                if not isinstance(files, dict):
                    print ou(u"Invalid cache, ignoring it")
                    return {}
                to_remove = set()
                for filepath, record in files.iteritems():
                    if not cache_entry_valid(filepath, record):
                        to_remove.add(filepath)
                for filepath in to_remove:
                    # remove fishy entries
                    del files[filepath]
                return files
        except Exception, exc:
            print ou(u"Error while reading the cache, continuing without it - "
                     u"%s" % exc)
    
    return {}

def write_cache(cache_file, files):
    cache_dir = os.path.dirname(cache_file)
    try:
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir, 0755)
        with open(cache_file, "wb") as f:
            pickle.dump((CURRENT_CACHE_VERSION, files), f, 2)
    except Exception, exc:
        print ou(u"Error while writing the cache - %s" % exc)


def collect_files(music_dir, files, visited_cache, is_supported_format):
    i = 0
    for dirpath, dirnames, filenames in os.walk(music_dir):
        for filename in filenames:
            filepath = un(relpath(os.path.join(dirpath, filename), music_dir),
                                  getfilesystemencoding())
            properpath = os.path.join(dirpath, filename)
            mtime = os.path.getmtime(properpath)

            # check the cache
            if filepath in visited_cache:
                visited_cache[filepath] = True
                record = files[filepath]
                if mtime <= record[1]:
                    # the file's still ok
                    continue

            ext = os.path.splitext(filename)[1]
            if is_supported_format(ext):
                i += 1
                print ou(u"  [%i] %s |" % (i, filepath)),
                try:
                    tags = mutagen.File(os.path.join(music_dir, filepath))
                    if tags is None:
                        raise Exception()
                    album_id = albumid.get_album_id(tags)
                    print ou(album_id or u"<single track>")
                    # fields here: album_id, mtime, already_processed
                    files[filepath] = (album_id, mtime, False)
                except:
                    # TODO: Maybe optionally abort here?
                    print ou(u"IGNORED: unreadable file or unsupported format")

def transform_cache(files):
    # transform ``files`` into lists of things to process
    albums = {}
    single_tracks = []
    for filepath, (album_id, mtime, processed) in files.iteritems():
        if album_id is not None:
            albums.setdefault(album_id, []).append(filepath)
        else:
            single_tracks.append(filepath)

    # purge anything that's marked as processed
    for album_id, album_files in albums.items():
        keep = False
        for filepath in album_files:
            if not files[filepath][2]:
                keep = True
                break
        if not keep:
            del albums[album_id]

    for filepath in single_tracks[:]:
        if files[filepath][2]:
            single_tracks.remove(filepath)

    return albums, single_tracks


def update_cache(files, music_dir, tracks, album_id):
    for filepath in tracks:
        mtime = os.path.getmtime(os.path.join(music_dir, filepath))
        files[filepath] = (album_id, mtime, True)

@contextlib.contextmanager
def stdstreams(stdout, stderr):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout
    sys.stderr = stderr
    try:
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

def do_gain_async(queue, job_key, files, ref_level, force, dry_run, album,
        mp3_format):
    output = cStringIO.StringIO()
    try:
        with stdstreams(output, output):
            if album:
                print ou(u"%s:" % job_key[1]),
            do_gain(files, ref_level, force, dry_run, album, mp3_format)
            print
    except BaseException, exc:
        # We can't reliably serialise and pass the exception information to the
        # driver process so we stringify it here.
        # And yes, we want to catch KeyboardInterrupt et al.
        queue.put((job_key, output.getvalue(), unicode(exc)))
    else:
        queue.put((job_key, output.getvalue(), None))


def do_gain_all(music_dir, albums, single_tracks, files, ref_level=89,
              force=False, dry_run=False, mp3_format=None, jobs=0,
              stop_on_error=False):
    pool = multiprocessing.Pool(None if jobs == 0 else jobs)
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    num_jobs = 0

    print "Dispatching jobs ..."
    if single_tracks:
        pool.apply_async(do_gain_async, [queue, (single_tracks, None),
            [os.path.join(music_dir, path) for path in single_tracks],
            ref_level, force, dry_run, False, mp3_format])
        num_jobs += 1

    for album_id, album_files in albums.iteritems():
        #print ou(u"%s:" % album_id),
        pool.apply_async(do_gain_async, [queue, (album_files, album_id),
            [os.path.join(music_dir, path) for path in album_files],
            ref_level, force, dry_run, True, mp3_format])
        num_jobs += 1
    pool.close()

    print "Now waiting for results ..."
    failed_jobs = []
    try:
        all_jobs = num_jobs
        successful = 0
        while num_jobs > 0:
            job_key, output, exc = queue.get()
            num_jobs -= 1
            if exc:
                failed_jobs.append((job_key, output, exc))
            else:
                successful += 1
                print output.strip()
                print "Successfully finished %s of %s." % (successful, all_jobs)
                print
            # Update cache.
            if not dry_run:
                tracks, album_id = job_key
                update_cache(files, music_dir, tracks, album_id)
    finally:
        try:
            pool.terminate()
        except Exception:
            # terminate ends rather horribly so we just silence it.
            pass
        if len(failed_jobs) > 0:
            print "Unfortunately, there were some errors:"
            for key, output, exc in failed_jobs:
                print output.strip()
                print >> sys.stderr, ou(exc)
                print
        print "%s successful, %s failed." % (successful, len(failed_jobs))


def do_collectiongain(music_dir, ref_level=89, force=False, dry_run=False,
                      mp3_format=None, ignore_cache=False, jobs=0):
    music_dir = un(music_dir, getfilesystemencoding())

    music_abspath = os.path.abspath(music_dir)
    musicpath_hash = md5(music_abspath.encode("utf-8")).hexdigest()
    cache_file = os.path.join(os.path.expanduser("~"), ".cache",
                              "collectiongain-cache.%s" % musicpath_hash)

    # load the cache, if desired
    if not ignore_cache:
        files = read_cache(cache_file)
    else:
        files = {}

    print "Collecting files ..."
    # whenever this part is stopped (KeyboardInterrupt/other exception), the
    # cache is written to disk so all progress persists
    try:
        visited_cache = dict.fromkeys(files.iterkeys(), False)
        collect_files(music_dir, files, visited_cache,
                      rgio.BaseFormatsMap(mp3_format).is_supported_format)
        # clean cache
        for filepath, visited in visited_cache.items():
            if not visited:
                del visited_cache[filepath]
                del files[filepath]
        # hopefully gets rid of at least one huge data structure
        del visited_cache

        albums, single_tracks = transform_cache(files)

        # gain everything that has survived the cleansing
        do_gain_all(music_dir, albums, single_tracks, files, ref_level, force,
                  dry_run, mp3_format, jobs)
    finally:
        write_cache(cache_file, files)

    print "All finished."


def collectiongain_options():
    opts = common_options()

    opts.add_option("--ignore-cache", help="Do not use the file cache at all.",
                    dest="ignore_cache", action="store_true")
    opts.add_option("--regain", help="Fully reprocess everything. Same as "
                    "'--force --ignore-cache'.",
                    dest="regain", action="store_true")
    opts.add_option("-j", "--jobs", help="Specifies the number of jobs to run "
                    "simultaneously. Must be >= 1. By default, this is set to "
                    "the number of CPU cores in the system to provide best "
                    "performance.", dest="jobs", action="store", type="int")

    opts.set_defaults(ignore_cache=False, jobs=None)

    opts.set_usage("%prog [options] MUSIC_DIR")
    opts.set_description("Calculate Replay Gain for a large set of audio files "
                         "without asking many questions. This program "
                         "calculates an album ID for any audo file in "
                         "MUSIC_DIR. Then, album gain will be applied to all "
                         "files with the same album ID. The album ID is "
                         "created from file tags as follows: If an 'album' tag "
                         "is present, it is joined with the contents of an "
                         "'albumartist' tag, or, if that isn't set, the "
                         "contents of the 'artist' tag, or nothing if there is "
                         "no 'artist' tag as well. On the other hand, if no "
                         "'album' tag is present, the file is assumed to be a "
                         "single track without album; in that case, no album "
                         "gain will be calculated for that file.")
    
    return opts


def collectiongain():
    init_gstreamer()
    optparser = collectiongain_options()
    opts, args = optparser.parse_args()
    if len(args) != 1:
        optparser.error("pass one directory path")
    if opts.jobs is not None and opts.jobs < 1:
        optparser.error("jobs must be at least 1")
    if opts.regain:
        opts.force = opts.ignore_cache = True
    
    try:
        do_collectiongain(args[0], opts.ref_level, opts.force, opts.dry_run,
                          opts.mp3_format, opts.ignore_cache, opts.jobs)
    except Error, exc:
        print
        print >> sys.stderr, ou(unicode(exc))
        sys.exit(1)
    except KeyboardInterrupt:
        print "Interrupted."


if __name__ == "__main__":
    collectiongain()

