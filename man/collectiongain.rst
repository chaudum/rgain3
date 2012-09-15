================
 collectiongain
================

------------------------------------------
 large scale Replay Gain calculating tool
------------------------------------------

:Date:   2011-11-26
:Version: 1.0
:Manual section: 1
:Manual group: rgain

SYNOPSIS
========

| **collectiongain** [*options*] *music_dir*
| **collectiongain** --help
| **collectiongain** --version

DESCRIPTION
===========

**collectiongain** is a script calculating the Replay Gain values of a large set of
music files inside *music_dir*. Each audio file will be rectified against the
other files of the same album, which are identified using the file tags.

OPTIONS
=======

--version
    Display the version of the software.

-h, --help
    Display a short summary of the available options.

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

--ignore-cache
    Don't trust implicit assumptions about what was already done, instead check
    all files for Replay Gain data explicitly.

-j JOBS, --jobs=JOBS
    Run JOBS jobs simultaneously. Must be >= 1. By default, this is set to the
    number of CPU cores in the system to provide best performance.

SEE ALSO
========

**replaygain(1)**
