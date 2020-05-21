**This repository is a fork of Felix Krull's `rgain` repository on Bitbucket
which aims to port the codebase to a modern Python 3 version.**

# rgain3 -- ReplayGain tools and Python library

This Python package provides modules to read, write and calculate Replay Gain
as well as 2 scripts that utilize these modules to do Replay Gain.

[Replay Gain][1] is a proposed standard (and has been for some time -- but it's
widely accepted) that's designed to solve the problem of varying volumes between
different audio files. I won't lay it all out for you here, go read it yourself.

## Requirements

- Python >= 3.5 -- http://python.org/
- GStreamer -- http://gstreamer.org/
- Cairo 2D -- https://www.cairographics.org/

To install these dependencies on Debian or Ubuntu (16.10 or newer):

 ```console
$ apt install \
      gir1.2-gstreamer-1.0 \
      gstreamer1.0-plugins-base \
      gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-bad \
      gstreamer1.0-plugins-ugly \
      libcairo2-dev \
      libgirepository1.0-dev \
      python3
```

You will also need GStreamer decoding plugins for any audio formats you want to
use.

## Installation

Just install it like any other Python package using `pip`:

 ```console
$ python3 -m pip install --user rgain3
 ```

## `replaygain`

This is a program like, say, **vorbisgain** or **mp3gain**, the difference
being that instead of supporting a mere one format, it supports several:

- Ogg Vorbis (or probably anything you can put into an Ogg container)
- Flac
- WavPack
- MP4 (commonly using the AAC codec)
- MP3

Basic usage is simple:

```console
$ replaygain AUDIOFILE1 AUDIOFILE2 ...
```

There are some options; see them by running:

```console
$ replaygain --help
```

## `collectiongain`

This program is designed to apply Replay Gain to whole music collections, plus
the ability to simply add new files, run **collectiongain** and have it
replay-gain those files without asking twice.

To use it, simply run:

```console
$ collectiongain PATH_TO_MUSIC
```

and re-run it whenever you add new files. Run:

```console
$ collectiongain --help
```

to see possible options.

If, however, you want to find out how exactly **collectiongain** works, read on
(but be warned: It's long, boring, technical, incomprehensible and awesome).
**collectiongain** runs in two phases: The file collecting phase and the actual
run. Prior to analyzing any audio data, **collectiongain** gathers all audio files in
the directory and determines a so-called album ID for each from the file's tags:

- If the file contains a Musicbrainz album ID, that is used.
- Otherwise, if the file contains an *album* tag, it is joined with either

  * a MusicBrainz album artist ID, if that exists
  * an *albumartist* tag, if that exists,
  * or the *artist* tag
  * or nothing if none of the above tags exist.

  The resulting artist-album combination is the album ID for that file.
- If the file doesn't contain a Musicbrainz album ID or an *album* tag, it is
  presumed to be a single track without album; it will only get track gain, no
  album gain.

Since this step takes a relatively long time, the album IDs are cached between
several runs of **collectiongain**. If a file was modified or a new file was
added, the album ID will be (re-)calculated for that file only.
The program will also cache an educated guess as to whether a file was already
processed and had Replay Gain added -- if **collectiongain** thinks so, that
file will totally ignored for the actual run. This flag is set whenever the file
is processed in the actual run phase (save for dry runs, which you can enable
with the **--dry-run** switch) and is cleared whenever a file was changed. You
can pass the **ignore-cache** switch to make **collectiongain** totally ignore
the cache; in that case, it will behave as if no cache was present and read your
collection from scratch.

For the actual run, **collectiongain** will simply look at all files that have
survived the cleansing described above; for files that don't contain Replay Gain
information, **collectiongain** will calculate it and write it to the files (use
the **--force** flag to calculate gain even if the file already has gain data).
Here comes the big moment of the album ID: files that have the same album ID are
considered to be one album (duh) for the calculation of album gain. If only one
file of an album is missing gain information, the whole album will be
recalculated to make sure the data is up-to-date.

## MP3 formats

Proper Replay Gain support for MP3 files is a bit of a mess: on the one hand,
there is the **mp3gain** [application][2] which was relatively widely used (I
don't know if it still is) -- it directly modifies the audio data which has the
advantage that it works with pretty much any player, but it also means you have
to decide ahead of time whether you want track gain or album gain. Besides, it's
just not very elegant. On the other hand, there are at least two commonly used
ways [to store proper Replay Gain information in ID3v2 tags][3].

Now, in general you don't have to worry about this when using this package: by
default, **replaygain** and **collectiongain** will read and write Replay Gain
information in the two most commonly used formats. However, if for whatever
reason you need more control over the MP3 Replay Gain information, you can use
the **--mp3-format** option (supported by both programs) to change the
behaviour. Possible choices with this switch are:

*replaygain.org* (alias: *fb2k*)
  Replay Gain information is stored in ID3v2 TXXX frames. This format is
  specified on the replaygain.org website as the recommended format for MP3
  files. Notably, this format is also used by the [foobar2000 music player for
  Windows][4].
*legacy* (alias: *ql*)
  Replay Gain information is stored in ID3v2.4 RVA2 frames. This format is
  described as "legacy" by replaygain.org; however, it is still the primary
  format for at least the [Quod Libet music player][5] and possibly others. It
  should be noted that this format does not support volume adjustments of more
  than 64 dB: if the calculated gain value is smaller than -64 dB or greater
  than or equal to +64 dB, it is clamped to these limit values.
*default*
  This is the default implementation used by both **replaygain** and
  **collectiongain**. When writing Replay Gain data, both the *replaygain.org*
  as well as the *legacy* format are written. As for reading, if a file
  contains data in both formats, both data sets are read and then compared. If
  they match up, that Replay Gain information is returned for the file.
  However, if they don't match, no Replay Gain data is returned to signal that
  this file does not contain valid (read: consistent) Replay Gain information.

# Development

Fork and clone this repository. Inside the checkout create a `virtualenv` and install `rgain3` in develop mode:

Note that developing from source requires the Python headers and therefore the
`python3.x-dev` system package to be installed.

```console
$ python3 -m venv env
$ source env/bin/activate
(env) $ python -m pip install -Ue .
```

### Running Tests

To run the tests with the Python version of your current virtualenv, simply
invoke `pytest` installing `test` extras:

```console
(env) $ python -m pip install -Ue ".[test]"
(env) $ pytest
```

You can run tests for all supported Python version using `tox` like so:

```console
(env) $ tox
```

# Copyright

With the exception of the manpages, all files are::

- Copyright (c) 2009-2015 Felix Krull <f_krull@gmx.de>
- Copyright (c) 2019-2020 Christian Haudum <developer@christianhaudum.at>

The manpages were originally written for the Debian project and are::

- Copyright (c) 2011 Simon Chopin <chopin.simon@gmail.com>
- Copyright (c) 2012-2015 Felix Krull <f_krull@gmx.de>


[1]: https://wiki.hydrogenaud.io/index.php?title=ReplayGain
[2]: http://mp3gain.sourceforce.net
[3]: http://wiki.hydrogenaudio.org/index.php?title=ReplayGain_specification#ID3v2
[4]: http://foobar2000.org
[5]: http://code.google.com/p/quodlibet
