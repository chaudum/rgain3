Changes
=======

rgain3 1.1.0 (2020-11-12)
-------------------------

- Added support for Python 3.8 and 3.9
- Added this file to the source distribution
- Added files necessary for the tests to the source distribution
- Fixed some deprecation warnings

rgain3 1.0.0 (2020-01-06)
-------------------------

- Added support for Python 3.5, 3.6 and 3.7
- Dropped support for Python 2.7
- Fixed issue with MP3 files that did not contain ID3 headers

rgain 1.3.4 (2016-05-06)
------------------------

- Support an additional format of MusicBrainz tags for MP3 files.
- Album artist tags for MP3 files are now case-sensitive.
- Fix a potential bug where custom reference levels would still store the
  default reference level (89 dB).
- Update readme and PyPI description re: inactivity.

rgain 1.3.3 (2014-10-09)
------------------------

- Fixed swapped album gain and track peak tags.

rgain 1.3.2 (2014-05-24)
------------------------

- Fixed some problems with non-UTF8 file names. They should now work as long as
  any file names touched by **rgain** match the system encoding.
  (https://bitbucket.org/fk/rgain/issue/12/unicodedecodeerror-ascii-codec-cant-decode)
- Misc. bug fixes.

rgain 1.3.1 (2013-11-29)
------------------------

- Support MP4/AAC (courtesy of Yevgeny Bezman).

rgain 1.3 (2013-10-28)
----------------------

- Work around a bug in some pygobject 3.10 releases
  (https://bugzilla.gnome.org/show_bug.cgi?id=710447)
- Properly recognise file extensions even with different capitalisation.
- Overhaul album ID algorithm to be hopefully better at grouping files that
  belong to an album and, conversely, not mis-grouping files. Note that this
  change will invalidate any cache files you might still have so your entire
  collection will be re-scanned next time you run **collectiongain**.
- Assorted bug fixes.

rgain 1.2.1 (2013-10-18)
------------------------

- Fix issue with reading MP3 reference loudness tags.

rgain 1.2 (2013-05-04)
----------------------

- Port to GStreamer 1.0.
- Support default GStreamer command-line options for **replaygain** and
  **collectiongain**. All known GStreamer options can be listed by using the
  **--help-gst** flag.
