# doinstall_gui.py - extra widgets for the installation stage
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
# 2008.02.08

import gtk

class Report(gtk.ScrolledWindow):
    """
    """
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.view = gtk.TextView()
        self.view.set_editable(False)
        #view.set_wrap_mode(gtk.WRAP_WORD)
        self.add(self.view)
        self.show()
        self.view.show()

        self.reportbuf = self.view.get_buffer()

    def report(self, text):
        self.reportbuf.insert(self.reportbuf.get_end_iter(), text+'\n')
        self.view.scroll_mark_onscreen(self.reportbuf.get_insert())
        mainWindow.eventloop()

    def backline(self):
        lc = self.reportbuf.get_line_count()
        li = self.reportbuf.get_iter_at_line(lc-2)
        ei = self.reportbuf.get_end_iter()
        self.reportbuf.delete(li, ei)

class Progress(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self, _("System copy progress"))
        self.set_border_width(20)
        vb = gtk.VBox(spacing=10)
        vb.set_border_width(5)
        hb = gtk.HBox()
        vb.pack_start(hb)
        lb = gtk.Label(_("Installed (MiB): "))
        self.isz = gtk.Entry()
        self.isz.set_editable(False)
        hb.pack_end(self.isz, False)
        hb.pack_end(lb, False)

        self.pb = gtk.ProgressBar()
        vb.pack_start(self.pb)
        self.add(vb)
        self.set_sensitive(False)
        self.set(None, 0.0)

    def start(self):
        self.set_sensitive(True)
        self.set(None, 0.0)

    def ended(self):
        self.set_sensitive(False)

    def set(self, size, fraction):
        self.pb.set_fraction(fraction)
        if size:
            self.isz.set_text(str(size))
        mainWindow.eventloop()

