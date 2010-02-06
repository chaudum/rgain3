# -*- coding: utf-8 -*-
# 
# Copyright (c) 2009 Felix Krull <f_krull@gmx.de>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
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

import os

import gtk
import glib
import gobject

from plugins.songsmenu import SongsMenuPlugin

from rgain import rgcalc, rgio


#class ReplayGainCheck(gobject.GObject):
#    
#    __gsignals__ = {
#        "all-checked": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
#                         (gobject.TYPE_PYOBJECT,)),
#        "file-checked": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
#                         (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,
#                          gobject.TYPE_PYOBJECT)),
#    }
#    
#    def __init__(self, filenames, formats_map, no_album=False):
#        gobject.GObject.__init__(self)
#        self.filenames = filenames
#        self.files_to_process = []
#        self.no_album = no_album
#        self.formats_map = formats_map
#        
#        if self.filenames:
#            glib.idle_add(self.check_replay_gain, 0,
#                          priority=glib.PRIORITY_HIGH)
#    
#    def check_replay_gain(self, index):
#        filename = self.filenames[index]
#        trackdata, albumdata = self.formats_map.read_gain(filename)
#        self.emit("file-checked", filename, trackdata, albumdata)
#        if not albumdata and not self.no_album:
#            # no album data, process everything
#            self.files_to_process = self.filenames[:]
#            self.emit("all-checked", self.files_to_process)
#            return False
#        
#        if not trackdata:
#            self.files_to_process.append(filename)
#        
#        index += 1
#        if index >= len(self.filenames):
#            # all done
#            self.emit("all-checked", self.files_to_process)
#        else:
#            glib.idle_add(self.check_replay_gain, index,
#                          priority=glib.PRIORITY_HIGH)
#        
#        return False


class ReplayGainBackend(gobject.GObject):
    
    STATE_NONE = 0
    STATE_CHECKING = 1
    STATE_ANALYZING = 2
    STATE_WRITING = 3
    STATE_STOPPED = 4
    
    TASK_CHECK = 1
    TASK_ANALYZE = 2
    TASK_WRITE = 3
    
    __gsignals__ = {
        "state-changed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_INT,)),
        #"progress-updated": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        #                     (gobject.TYPE_DOUBLE, gobject.TYPE_STRING,
        #                      gobject.TYPE_STRING)),
        "task-started": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                         (gobject.TYPE_INT, gobject.TYPE_STRING,
                          gobject.TYPE_DOUBLE),)
        "task-finished": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_INT, gobject.TYPE_STRING,
                           gobject.TYPE_DOUBLE),)
        "finished": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                     (gobject.TYPE_BOOL,)),
    }
    
    def __init__(self, filenames, formats_map, ref_lvl=89, force=False,
                 no_album=False):
        gobject.GObject.__init__(self)
        self.filenames = filenames
        self.formats_map = formats_map
        self.ref_lvl = ref_lvl
        self.force = force
        self.no_album = no_album
        
        self.files_to_process = []
        self.state = self.STATE_NONE
        self.paused = False
        self.index = 0
    
    def start(self):
        if not self.force:
            self._install_check_callback()
            self._change_state(self.STATE_CHECKING)
        else:
            self.files_to_process = self.filenames
            self._start_analyze()
    
    
    def pause(self, pause):
        self.paused = pause
        if self.state == self.STATE_NONE:
            raise RuntimeError("backend is in STATE_NONE, cannot pause")
        elif self.state == self.STATE_CHECKING:
            if not pause:
                # re-install check callback
                self._install_check_callback()
        elif self.state == self.STATE_ANALYZING:
            self.rg.pause(pause)
        elif self.state == self.STATE_WRITING:
            if not pause:
                # re-install write callback
                self._install_write_callback()
        
        elif self.state == self.STATE_STOPPED:
            raise RuntimeError("backend is in STATE_STOPPED, cannot pause")
    
    def stop(self):
        if self.state == self.STATE_NONE:
            raise RuntimeError("backend is in STATE_NONE, cannot stop")
        elif self.state == self.STATE_CHECKING:
            self._finish(True)
        elif self.state == self.STATE_ANALYZING:
            self.rg.stop()
            self._finish(True)
        elif self.state == self.STATE_WRITING:
            self._finish(True)
        elif self.state == self.STATE_STOPPED:
            raise RuntimeError("backend is in STATE_STOPPED, cannot stop")
    
    
    def _change_state(self, new_state):
        self.state = new_state
        self.emit("state-changed", new_state)
    
    def _finish(self, was_canceled=False):
        self._change_state(self.STATE_STOPPED)
        self.emit("finished", was_canceled)
    
    # phase 1 - check
    def _install_check_callback(self):
        glib.idle_add(self._check_replay_gain, priority=glib.PRIORITY_HIGH)
    
    def _check_replay_gain(self):
        if self.paused or self.state == self.STATE_STOPPED:
            # paused or stopped -- either way, we don't want to get called
            # routinely for now
            return False
        
        # do actual check
        filename = self.filenames[self.index]
        #self.emit("task-started", self.TASK_CHECK, filename, 0)
        trackdata, albumdata = self.formats_map.read_gain(filename)
        self.emit("task-finished", self.TASK_CHECK, filename, 0)
        if not albumdata and not self.no_album:
            # no album data, process everything
            self.files_to_process = self.filenames
            self._start_analyze()
            return False
        
        if not trackdata:
            self.files_to_process.append(filename)
        
        self.index += 1
        if self.index >= len(self.filenames):
            self._start_analyze()
            return False
        else:
            return True
    
    # phase 2 - analyze
    def _start_analyze(self):
        self.done = 0
        self.total = len(files_to_process)
        self.rg = rgcalc.ReplayGain(self.files_to_process, True, self.ref_lvl)
        self.rg.connect("track-started", self._on_track_started)
        self.rg.connect("track-finished", self.on_track_finished)
        self.rg.connect("all-finished", self._on_all_finished)
        self.rg.start()
        self._change_state(self.STATE_ANALYZING)
    
    def _on_track_started(self, evsrc, filename):
        self.emit("task-started", self.TASK_ANALYZE, filename,
                  float(self.done) / float(self.total))
    
    def _on_track_finished(self, evsrc, filename, trackdata):
        self.done += 1
        self.emit("task-finished", self.TASK_ANALYZE, filename,
                  float(self.done) / float(self.total))
    
    def _on_all_finished(self, evsrc, trackdata, albumdata):
        self.index = 0
        self._install_write_callback()
        self._change_state(self.STATE_WRITING)
    
    
    # phase 3 - write
    def _install_write_callback(self):
        glib.idle_add(self._write_replay_gain, priority=glib.PRIORITY_HIGH)
    
    def _write_replay_gain(self):
        if self.paused or self.state == self.STATE_STOPPED:
            # paused or stopped -- either way, we don't want to get called
            # routinely for now
            return False
        
        # write
        filename = self.files_to_process[self.index]
        trackdata = self.rg.track_data[filename]
        if not self.no_album:
            albumdata = self.rg.album_data
        else:
            albumdata = None
        #self.emit("task-started", self.TASK_WRITE, filename, 1)
        self.formats_map.write_gain(filename, trackdata, albumdata)
        self.emit("task-finished", self.TASK_WRITE, filename, 1)
        
        self.index += 1
        if self.index >= len(self.files_to_process):
            # all done
            self._finish()
            return False
        else:
            return True


class ReplayGainUI(object):
    
    def __init__(self, songs):
        self.songs = songs
        self.filenames = [song["~filename"] for song in songs]
        self.builder = gtk.Builder()
        # TODO
        self.builder.add_from_file("/home/fk/Desktop/code/rgain/ql-plugin/replaygain-ui.xml")
        
        self.backend = None
        self.current_task = None
        
        self.rgain_window = self.builder.get_object("rgain-window")
        self.buttons_box = self.builder.get_object("box-buttons")
        self.progress_label = self.builder.get_object("label-progress")
        self.progress_bar = self.builder.get_object("progressbar")
        
        # set up default values
        self.builder.get_object("settings-reflvl").set_value(89)
        
        self.builder.connect_signals(self)
        self.rgain_window.show_all()
    
    # 1 - Settings
    def on_cancel_button_clicked(self, button):
        if self.backend is None or self.backend.state in (
            ReplayGainBackend.STATE_NONE,
            ReplayGainBackend.STATE_STOPPED,
        ):
            self.rgain_window.destroy()
        else:
            self.backend.stop()
    
    def on_ok_button_clicked(self, button):
        force = self.builder.get_object("settings-force").get_active()
        no_album = self.builder.get_object( "settings-no-album").get_active()
        ref_lvl = self.builder.get_object("settings-reflvl").get_value_as_int()
        
        # some UI changes
        self.builder.get_object("box-settings").set_sensitive(False)
        self.buttons_box.remove(self.builder.get_object("button-ok"))
        button_pause = self.builder.get_object("button-pause")
        self.buttons_box.pack_start(button_pause)
        
        self.backend = ReplayGainBackend(self.filenames,
                                         rgio.BaseFormatsMap("ql"), ref_lvl,
                                         force, no_album)
        
    
    def on_state_changed(self, backend, new_state):
        if new_state == ReplayGainBackend.STATE_CHECKING:
            
    
    def on_task_started(self, backend, task_type, filename, progress):
        self.current_task = (task_type, filename)
        self.progress_bar.set_fraction(progress)
        
    
    
    def display_current_task(self, task):
        if task_type == ReplayGainBackend.TASK_CHECK:
            self.progress_bar.set_text("Checking for Replay Gain …")
            self.progress_label.set_label("<i>Checked %s</i>" %
                                          os.path.basename(filename))
        elif task_type
        
        # get config from controls
        #self.get_config()
        
        # disable settings panel
        #
        
        # swap buttons
        #self.buttons_box.remove(self.builder.get_object("button-cancel"))
        #
        #
        #button_stop = self.builder.get_object("button-stop")
        #self.buttons_box.pack_start(button_stop)
        #
        
        # initiate checks or analysis
        #if not self.force:
        #    # TODO: is this good or stupid?
        #    button_pause.set_sensitive(False)
        #    button_stop.set_sensitive(False)
            
        #    self.progress_bar.set_text("Checking for Replay Gain …")
        #    self.current_task = "Checking for Replay Gain …"
        #    check = ReplayGainCheck(self.filenames, self.formats_map,
        #                            self.no_album)
        #    check.connect("all-checked", self.on_all_checked)
        #else:
        #    self.start_analyze(self.filenames)
    
    # 2 - Calculating
    def on_pause_button_toggled(self, button):
        # TODO
        self.rg.pause(button.get_active())
        if button.get_active():
            self.progress_label.set_label("%s<i> (Paused)</i>" %
                                          self.current_task)
        else:
            self.current_task = self.current_task
    
    def on_stop_button_clicked(self, button):
        self.rg.stop()
        self.finish("Canceled", False)
    
    # 2.1 - Checking
    def on_all_checked(self, evsrc, files_to_process):
        if files_to_process:
            self.start_analyze(files_to_process)
        else:
            self.finish("Nothing to do")
    
    
    # 2.2 - Analyzing
    def start_analyze(self, files_to_process):
        self.rg = rgcalc.ReplayGain(files_to_process, True, self.ref_lvl)
        self.current = 0
        self.total = len(files_to_process)
        self.rg.connect("track-started", self.on_track_started)
        self.rg.connect("track-finished", self.on_track_finished)
        self.rg.start()
        self.builder.get_object("button-stop").set_sensitive(True)
        self.builder.get_object("button-pause").set_sensitive(True)
    
    def on_track_started(self, evsrc, filename):
        self.current_task = "Analyzing %s" % filename
        self.current += 1
        self.progress_bar.set_text("Analyzing: %s of %s" %
                                   (self.current, self.total))
    
    def on_track_finished(self, evsrc, filename):
        self.progress_bar.set_fraction(float(self.current) / float(self.total))
    
    def _get_current_task(self):
        return getattr(self, "_current_task", "")
    
    def _set_current_task(self, task):
        self._current_task = task
        self.progress_label.set_label("<i>%s</i>" % task)
    
    current_task = property(_get_current_task, _set_current_task)
    
    
    # 3 - Finishing
    def finish(self, message="Done", purge_progress=True):
        self.current_task = ""
        if purge_progress:
            self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text(message)
        self.builder.get_object("button-stop").set_sensitive(False)
        self.builder.get_object("button-pause").set_sensitive(False)
        
        def destroy_self():
            self.rgain_window.destroy()
            return False
        
        glib.timeout_add_seconds(1, destroy_self)
    
#    # 2nd button generation
#    def on_pause_clicked(self, button):
#        # pause
#        pass
#    
#    def on_stop_clicked(self, button):
#        # stop
#        pass
#    
#    # 3rd button generation
#    def on_close_clicked(self, button):
#        self.rgain_window.destroy()
#    
#    # check-time handlers
#    def on_file_checked(self, src, filename, trackdata, albumdata):
#        self.progress_label.set_label("<i>Checked %s</i>" % filename)
#    
#    def on_all_checked(self, src, files_to_process):
#        print files_to_process
#    
#    # analyze-time stuff
#    def start_analyze(self, files_to_process, ref_lvl):
#        rg = rgcalc.ReplayGain(files_to_process, True, ref_lvl)
#        self.rg = rg
#        rg.connect("track-started", self.on_track_started)
#        rg.connect("track-finished", self.on_track_finished)
#        rg.connect("all-finished", self.on_all_finished)
#        rg.start()
#    
#    def on_track_started(self, src, filename):
#        pass
#    
#    def on_track_finished(self, src, filename):
#        pass
#    
#    def on_all_finished(self, src):
#        print src.track_data
#        print src.album_data


class ReplayGainPlugin(SongsMenuPlugin):
    PLUGIN_ID = "Replay Gain"
    PLUGIN_NAME = _("Calculate Replay Gain")
    PLUGIN_DESC = "Calculate and write Replay Gain for the selected files."
    PLUGIN_VERSION = "1.0"
    
    plugin_songs = ReplayGainUI

