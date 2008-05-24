#!/usr/bin/env python
#
# larchinmain.py - larchin main window
#
# (c) Copyright 2008 Michael Towers <gradgrind[at]online[dot]de>
#
# This file is part of the larch project.
#
#    larch is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    larch is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with larch; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#----------------------------------------------------------------------------
# 2008.02.14

# Add a Quit button?

from glob import glob
import re
import gtk, gobject

from stage import Stage
from dialogs import popupError, popupMessage, popupWarning, popupEditor

class Larchin(gtk.Window):
    def __init__(self):

        for m in glob("%s/modules/stages/*.py" % basePath):
            execfile(m, globals(), {})

        gtk.Window.__init__(self)
        self.set_default_size(600,400)
        self.connect("destroy", self.exit)
        self.set_border_width(3)

        self.header = gtk.Label()
        self.header.set_use_markup(True)

        self.mainWidget = gtk.Notebook()
        self.mainWidget.set_show_tabs(False)

        self.lButton = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.rButton = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.hButton = gtk.Button(stock=gtk.STOCK_HELP)
        buttons = gtk.HButtonBox()
        buttons.pack_start(self.lButton)
        buttons.pack_start(self.hButton)
        buttons.pack_end(self.rButton)

        box1 = gtk.VBox()
        box1.pack_start(self.header, expand=False, padding=3)
        box1.pack_start(self.mainWidget)
        box1.pack_start(buttons, expand=False, padding=3)

        self.add(box1)

        self.hButton.connect("clicked", self.help)
        self.lButton.connect("clicked", self.sigprocess, self.back)
        self.rButton.connect("clicked", self.sigprocess, self.forward)

        self.watchcursor = gtk.gdk.Cursor(gtk.gdk.WATCH)

        self.busy = False

    def mainLoop(self):
        self.show_all()
        gtk.main()

    def exit(self, widget=None, data=None):
        install.tidyup()
        gtk.main_quit()

    def enable_forward(self, on):
        self.rButton.set_sensitive(on)

    def sigprocess(self, widget, slot, arg=None):
        if self.busy:
            return
        self.busy = True
        self.busy_on()

        slot(arg)

        self.busy_off()
        self.busy = False

    def busy_on(self, fade=True):
        if not self.window:
            return
#        gdk_win = gtk.gdk.Window(mainWindow.window,
#                gtk.gdk.screen_width(),
#                gtk.gdk.screen_height(),
#                gtk.gdk.WINDOW_CHILD,
#                0,
#                gtk.gdk.INPUT_ONLY)
#        gdk_win.set_cursor(self.watchcursor)
#        gdk_win.show()
        self.window.set_cursor(self.watchcursor)

# (*) The sensitivity switch mucks up repeated
# clicks on a single button (the mouse must leave and reenter the button
# before clicking works again). gtk bug 56070
        if fade:
            self.mainWidget.set_sensitive(False)
        self.eventloop()

    def busy_off(self, fade=True):
        if not self.window:
            return
#        gdk_win.set_cursor(None)
#        gdk_win.destroy()
        self.window.set_cursor(None)

# See above (*)
        if fade:
            self.mainWidget.set_sensitive(True)

    def eventloop(self, t=0):
        while gtk.events_pending():
                gtk.main_iteration(False)
        if (t > 0.0):
                self.timedout = False
                gobject.timeout_add(int(t*1000), self.timeout)
                while not self.timedout:
                    gtk.main_iteration(True)

    def timeout(self):
        self.timedout = True
        # Cancel this timer
        return False

    def goto(self, stagename):
        """This is the main function for entering a new stage.
        It stacks the widget (using a gtk.Notebook) so that it can be
        returned to later.
        """
        sclass = stages[stagename]
        sw = sclass()
        self.mainWidget.append_page(sw)
        self.setStage(sw)

    def setStage(self, sw):
        self.stage = sw
        llabel = sw.labelL()
        self.lButton.set_label(llabel)
        self.rButton.set_label(sw.labelR())
        n = self.mainWidget.get_n_pages()
        self.lButton.set_sensitive(llabel != "")
        self.header.set_label('<span foreground="blue" size="20000">%s</span>'
                % self.stage.stageTitle())
        self.stage.show_all()
        self.mainWidget.set_current_page(-1)
        self.eventloop()

    def help(self, widget, data=None):
        self.stage.help()

    def back(self, data):
        """This goes back to the stage previous to the current one in the
        actually executed call sequence.
        """
        n = self.mainWidget.get_n_pages()
        stage = self.mainWidget.get_nth_page(n-2)
        self.mainWidget.remove_page(n-1)
        stage.reinit()
        self.setStage(stage)

    def forward(self, data):
        self.stage.forward()
