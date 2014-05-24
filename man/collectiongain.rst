================
 collectiongain
================

------------------------------------------
 large scale Replay Gain calculating tool
------------------------------------------

:Date: DATE
:Version: VERSION
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
music files inside *music_dir*. Files belonging to the same album will be identified
using the file tags and album Replay Gain data will be calculated for them.

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
    Choose the Replay Gain data format for MP3 files. The default setting should
    be compatible with most decent software music players, so it is generally
    not necessary to mess with this setting. See below for more information.

--ignore-cache
    Do not use the file cache at all.

--regain
    Fully reprocess everything. Same as ``--force --ignore-cache``.

-j JOBS, --jobs=JOBS
    Run JOBS jobs simultaneously. Must be >= 1. By default, this is set to the
    number of CPU cores in the system to provide best performance.

MP3 formats
===========
Proper Replay Gain support for MP3 files is a bit of a
mess: on the one hand, there is the **mp3gain** application [1] which was
relatively widely used (I don't know if it still is) -- it directly modifies the
audio data which has the advantage that it works with pretty much any player,
but it also means you have to decide ahead of time whether you want track gain
or album gain. Besides, it's just not very elegant. On the other hand, there are
at least two commonly used ways to store proper Replay Gain information in ID3v2
tags [2].

Now, in general you don't have to worry about this when using this package: by
default, **replaygain** and **collectiongain** will read and write Replay Gain
information in the two most commonly used formats. However, if for whatever
reason you need more control over the MP3 Replay Gain information, you can use
the **--mp3-format** option (supported by both programs) to change the
behaviour. Possible choices with this switch are:

 - *replaygain.org* (alias: *fb2k*)
   Replay Gain information is stored in ID3v2 TXXX frames. This format is
   specified on the replaygain.org website as the recommended format for MP3
   files. Notably, this format is also used by the foobar2000 music player for
   Windows [3].

 - *legacy* (alias: *ql*)
   Replay Gain information is stored in ID3v2.4 RVA2 frames. This format is
   described as "legacy" by replaygain.org; however, it is still the primary
   format for at least the Quod Libet music player [4] and possibly others. It
   should be noted that this format does not support volume adjustments of more
   than 64 dB: if the calculated gain value is smaller than -64 dB or greater
   than or equal to +64 dB, it is clamped to these limit values.

 - *default*
   This is the default implementation used by both **replaygain** and
   **collectiongain**. When writing Replay Gain data, both the *replaygain.org*
   as well as the *legacy* format are written. As for reading, if a file
   contains data in both formats, both data sets are read and then compared. If
   they match up, that Replay Gain information is returned for the file.
   However, if they don't match, no Replay Gain data is returned to signal that
   this file does not contain valid (read: consistent) Replay Gain information.

[1] http://mp3gain.sourceforce.net

[2] http://wiki.hydrogenaudio.org/index.php?title=ReplayGain_specification#ID3v2

[3] http://foobar2000.org

[4] http://code.google.com/p/quodlibet

SEE ALSO
========

**replaygain(1)**
