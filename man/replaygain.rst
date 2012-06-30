============
 replaygain
============

--------------------------------
 single file Replay Gain editor
--------------------------------

:Date:   2011-11-26
:Version: 1.0
:Manual section: 1
:Manual group: rgain

SYNOPSIS
========

| **replaygain** [*options*] *AUDIO_FILE* [*AUDIO_FILE* ...]
| **replaygain** --help
| **replaygain** --version

DESCRIPTION
===========

**replaygain** applies or displays Replay Gain information for audio files.

OPTIONS
=======

--version
    Display the version of the software.

-h, --help
    Display a short documentation.

-f, --force
    Recalculate Replay Gain even if the file already contains gain information.

-d, --dry-run
    Don't actually modify any files.

-r REF, --reference-loudness=REF
    Set the reference loudness to REF dB (default: 89 dB)

--mp3-format=MP3_FORMAT
    Choose the Replay Gain data format for MP3 files.  Since there is no
    commonly accepted standard for Replay Gain in MP3 files, you need to choose.
    Possible formats are :

 - *ql* (used by **Quod Libet**). This is the default value.
 - *fb2k* (read and written by **foobar2000**, also understood by **Quod Libet**)
 - *mp3gain* (tags as written by the **mp3gain** program; this doesn't modify the
   MP3 audio data as said program does).

--no-album
    Don't write any album gain information.

--show
    Don't calculate anything, simply show Replay Gain information for the
    specified files. In this mode, all options other than **--mp3-format**
    are ignored.

SEE ALSO
========

**collectiongain(1)**
