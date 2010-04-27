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

"""Replay Gain analysis using GStreamer. See ``ReplayGain`` class for full
documentation or use the ``calculate`` function.
"""

import os.path

import pygst
pygst.require("0.10")
import gst
import gobject

from rgain import GainData

GST_TAG_REFERENCE_LEVEL = "replaygain-reference-level"

def to_utf8(string):
    if isinstance(string, unicode):
        return string.encode("utf-8")
    else:
        return string.decode("utf-8").encode("utf-8")

class ReplayGain(gobject.GObject):
    
    """Perform a Replay Gain analysis on some files.
    
    This class doesn't actually write any Replay Gain information - that is left
    as an exercise to the user. It only analyzes the files and presents the
    result.
    Basic usage is as follows:
     - instantiate the class, passing it a list of file names and optionally the
       reference loudness level to use (defaults to 89 dB),
     - connect to the signals the class provides,
     - get yourself a glib main loop (e.g. ``gobject.MainLoop`` or the one from
       GTK),
     - call ``replaygain_instance.start()`` to start processing,
     - start your main loop to dispatch events and
     - wait.
    Once you've done that, you can retrieve the data from ``track_data`` (which
    is a dict: keys are file names, values are ``GainData`` instances) and
    ``album_data`` (a 'GainData' instance, even though it may contain only
    ``None`` values if album gain isn't calculated). Note that the values don't
    contain any kind of unit, which might be needed.
    """
    
    __gsignals__ = {
        "all-finished": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                         (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        "track-started": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_STRING,)),
        "track-finished": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)),
    }
    
    
    def __init__(self, files, force=False, ref_lvl=89):
        gobject.GObject.__init__(self)
        self.files = files
        self.force = force
        self.ref_lvl = ref_lvl
        
        self._setup_pipeline()
        self._setup_rg_elem()
        
        self._files_iter = iter(self.files)
        
        # this holds all track gain data
        self.track_data = {}
        self.album_data = GainData(0)
    
    def start(self):
        """Start processing.
        
        For it to work correctly, you'll need to run some gobject main loop
        (e.g. the Gtk one) or process any events manually (though I have no
        idea how or if that works).
        """
        if not self._next_file():
            raise ValueError("do never, ever run this thing without any files")
        self.pipe.set_state(gst.STATE_PLAYING)
    
    def pause(self, pause):
        if pause:
            self.pipe.set_state(gst.STATE_PAUSED)
        else:
            self.pipe.set_state(gst.STATE_PLAYING)
    
    def stop(self):
        self.pipe.set_state(gst.STATE_NULL)
    
    
    # internal stuff
    def _setup_pipeline(self):
        """Setup the pipeline."""
        self.pipe = gst.Pipeline("replaygain")
        
        # elements
        self.decbin = gst.element_factory_make("decodebin", "decbin")
        self.pipe.add(self.decbin)
        self.conv = gst.element_factory_make("audioconvert", "conv")
        self.pipe.add(self.conv)
        self.res = gst.element_factory_make("audioresample", "res")
        self.pipe.add(self.res)
        self.rg = gst.element_factory_make("rganalysis", "rg")
        self.pipe.add(self.rg)
        self.sink = gst.element_factory_make("fakesink", "sink")
        self.pipe.add(self.sink)
        
        # link
        gst.element_link_many(self.conv, self.res, self.rg, self.sink)
        self.decbin.connect("pad-added", self._on_pad_added)
        self.decbin.connect("pad-removed", self._on_pad_removed)
        
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)
    
    def _setup_rg_elem(self):
        # there's no way to specify 'forced', as it's usually useless
        self.rg.set_property("forced", True)
        self.rg.set_property("reference-level", self.ref_lvl)
    
    def _next_file(self):
        """Load the next file to analyze.
        
        Returns False if everything is done and the pipeline shouldn't be
        started again; True otherwise.
        """
        # only when there already is a source
        if hasattr(self, "src"):
            self.src.unlink(self.decbin)
            self.pipe.remove(self.src)
        
        # set the next file
        try:
            fname = self._files_iter.next()
        except StopIteration:
            self.emit("all-finished", self.track_data, self.album_data)
            return False
        
        # make a new src element
        self.src = gst.element_factory_make("filesrc", "src")
        self.src.set_property("location", to_utf8(fname))
        
        self._current_file = fname
        
        self.pipe.add(self.src)
        self.src.link(self.decbin)
        
        self.rg.set_property("num-tracks", 1)
        
        self.emit("track-started", to_utf8(fname))
        
        return True
    
    def _process_tags(self, msg):
        """Process a tag message."""
        tags = msg.parse_tag()
        trackdata = self.track_data.setdefault(self._current_file, GainData(0))
        
        # process just every tag
        for tag in tags.keys():
            if tag == gst.TAG_TRACK_GAIN:
                trackdata.gain = tags[tag]
            elif tag == gst.TAG_TRACK_PEAK:
                trackdata.peak = tags[tag]
            elif tag == GST_TAG_REFERENCE_LEVEL:
                trackdata.ref_level = tags[tag]
            
            elif tag == gst.TAG_ALBUM_GAIN:
                self.album_data.gain = tags[tag]
            elif tag == gst.TAG_ALBUM_PEAK:
                self.album_data.peak = tags[tag]
    
    
    # event handlers
    def _on_pad_added(self, decbin, new_pad):
        try:
            decbin.link(self.conv)
        except gst.LinkError:
            # this one didn't work. Hopefully the next try's better
            pass
    
    def _on_pad_removed(self, decbin, old_pad):
        decbin.unlink(self.conv)
    
    def _on_message(self, bus, msg):
        if msg.type == gst.MESSAGE_TAG:
            if not msg.src == self.rg:
                return
            self._process_tags(msg)
        elif msg.type == gst.MESSAGE_EOS:
            self.emit("track-finished", to_utf8(self._current_file),
                      self.track_data[self._current_file])
            self.rg.set_locked_state(True)
            self.pipe.set_state(gst.STATE_NULL)
            ret = self._next_file()
            if ret:
                self.rg.set_locked_state(False)
                self.pipe.set_state(gst.STATE_PLAYING)



def calculate(*args, **kwargs):
    """Analyze some files.
    
    This is only a convenience interface to the ``ReplayGain`` class: it takes
    the same arguments, but setups its own main loop and returns the results
    once everything's finished.
    """
    def on_finished(evsrc, trackdata, albumdata):
        # all done
        loop.quit()
    
    rg = ReplayGain(*args, **kwargs)
    rg.connect("all-finished", on_finished)
    loop = gobject.MainLoop()
    rg.start()
    loop.run()
    return (rg.track_data, rg.album_data)

