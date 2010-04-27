# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, 2010 Felix Krull <f_krull@gmx.de>
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

from rgain import rgio
from rgain.script import ou, un, Error, common_options
from rgain.script.replaygain import do_gain


# all of collectiongain
def relpath(path, base):
    size = len(base)
    if os.path.basename(base):
        # this means ``base`` does not end with a separator
        size += 1
    return path[size:]


def read_cache(cache_file):
    if not os.path.isfile(cache_file):
        files = {}
    else:
        try:
            f = open(cache_file, "rb")
            files = pickle.load(f)
        except Exception, exc:
            print ou(u"Error while reading the cache - %s" % exc)
        finally:
            try:
                f.close()
            except NameError:
                pass
    
    return files


def write_cache(cache_file, files):
    cache_dir = os.path.dirname(cache_file)
    
    try:
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir, 0755)
        f = open(cache_file, "wb")
        pickle.dump(files, f, 2)
    except Exception, exc:
        print ou(u"Error while writing the cache - %s" % exc)
    finally:
        try:
            f.close()
        except NameError:
            pass


def validate_cache(files):
    for filepath, record in files.items():
        if (isinstance(filepath, basestring) and
            hasattr(record, "__getitem__") and
            hasattr(record, "__len__") and
            len(record) == 3 and
            (isinstance(record[0], basestring) or
             record[0] is None) and
            (isinstance(record[1], int) or
             isinstance(record[1], float)) and
            isinstance(record[2], bool)
        ):
            continue
        else:
            # funny record, purge it
            del files[filepath]


def get_album_id(music_dir, filepath):
    properpath = os.path.join(music_dir, filepath)
    ext = os.path.splitext(filepath)[1]
    try:
        tags = mutagen.File(properpath)
    except Exception, exc:
        raise Error(u"%s: error - %s" % (filepath, exc))
    
    if ext == ".mp3":
        if "TALB" in tags:
            album = tags["TALB"].text[0]
        else:
            album = None
    else:
        album = tags.get("album", [""])[0]
    
    if album:
        if ext == ".mp3":
            artist = None
            for frame in tags.itervalues():
                if isinstance(frame, TXXX) and "albumartist" in frame.desc:
                    # these heuristics are a bit fragile
                    artist = frame.text[0]
                    break
            if not artist:
                # TODO: is this correct?
                if "TPE1" in tags:
                    artist = tags["TPE1"].text[0]
        else:
            artist = tags.get("albumartist") or tags.get("artist")
            if artist:
                artist = artist[0]
        
        if not artist:
            artist = u""
        album_id = u"%s - %s" % (artist, album)
    else:
        album_id = None
    
    return album_id


def collect_files(music_dir, files, cache, supported_formats):
    i = 0
    for dirpath, dirnames, filenames in os.walk(music_dir):
        for filename in filenames:
            filepath = un(relpath(os.path.join(dirpath, filename), music_dir),
                                  sys.getfilesystemencoding())
            properpath = os.path.join(dirpath, filename)
            mtime = os.path.getmtime(properpath)
            
            # check the cache
            if filepath in cache:
                cache[filepath] = True
                record = files[filepath]
                if mtime <= record[1]:
                    # the file's still ok
                    continue
            
            ext = os.path.splitext(filename)[1]
            if ext in supported_formats:
                i += 1
                print ou(u"  [%i] %s |" % (i, filepath)),
                album_id = get_album_id(music_dir, filepath)
                print ou(album_id or u"<single track>")
                # fields here: album_id, mtime, already_processed
                files[filepath] = (album_id, mtime, False)


def transform_cache(files, ignore_cache=False):
    # transform ``files`` into a usable data structure
    albums = {}
    single_tracks = []
    for filepath, (album_id, mtime, processed) in files.iteritems():
        if album_id is not None:
            albums.setdefault(album_id, []).append(filepath)
        else:
            single_tracks.append(filepath)
    
    # purge anything that's marked as processed, if desired
    if not ignore_cache:
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


def do_gain_all(music_dir, albums, single_tracks, files, ref_level=89,
              force=False, dry_run=False, mp3_format="ql", stop_on_error=False):
    if single_tracks:
        do_gain((os.path.join(music_dir, path) for path in single_tracks),
                ref_level, force, dry_run, False, mp3_format)
        # update cache information
        if not dry_run:
            update_cache(files, music_dir, single_tracks, None)
        print
    
    for album_id, album_files in albums.iteritems():
        print ou(u"%s:" % album_id),
        do_gain((os.path.join(music_dir, path) for path in album_files),
                ref_level, force, dry_run, True, mp3_format)
        # update cache
        if not dry_run:
            update_cache(files, music_dir, album_files, album_id)
        print


def do_collectiongain(music_dir, ref_level=89, force=False, dry_run=False,
                      mp3_format="ql", ignore_cache=False):
    music_dir = un(music_dir, sys.getfilesystemencoding())
    
    music_abspath = os.path.abspath(music_dir)
    musicpath_hash = md5(music_abspath).hexdigest()
    cache_file = os.path.join(os.path.expanduser("~"), ".cache",
                              "collectiongain-cache.%s" % musicpath_hash)
    
    # load the cache
    files = read_cache(cache_file)
    
    # yeah, side-effects are bad, I know
    validate_cache(files)
    cache = dict.fromkeys(files.iterkeys(), False)
    
    print "Collecting files ..."
    
    # whenever this part is stopped (KeyboardInterrupt/other exception), the
    # cache is written to disk so all progress persists
    try:
        collect_files(music_dir, files, cache,
                      rgio.BaseFormatsMap(mp3_format).supported_formats)
        # clean cache
        for filepath, visited in cache.items():
            if not visited:
                del cache[filepath]
                del files[filepath]
        # hopefully gets rid of at least one huge data structure
        del cache
    
        albums, single_tracks = transform_cache(files, ignore_cache)
        print
        
        # gain everything that has survived the cleansing
        do_gain_all(music_dir, albums, single_tracks, files, ref_level, force,
                  dry_run, mp3_format)
    finally:
        validate_cache(files)
        write_cache(cache_file, files)
    
    print "All finished."


def collectiongain_options():
    opts = common_options()
    
    opts.add_option("--ignore-cache", help="Don't trust implicit assumptions "
                    "about what was already done, instead check all files for "
                    "Replay Gain data explicitly.", dest="ignore_cache",
                    action="store_true")
    
    opts.set_defaults(ignore_cache=False)
    
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
    optparser = collectiongain_options()
    opts, args = optparser.parse_args()
    if len(args) != 1:
        optparser.error("pass one directory path")
    
    try:
        do_collectiongain(args[0], opts.ref_level, opts.force, opts.dry_run,
                          opts.mp3_format, opts.ignore_cache)
    except Error, exc:
        print >> sys.stderr, ou(unicode(exc))
        sys.exit(1)
    except KeyboardInterrupt:
        print "Interrupted."


if __name__ == "__main__":
    collectiongain()

