#!/usr/bin/env python
#
# larchquit.py  - a logout gui for larch live systems,
#                 with session save options, where appropriate
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
# 2008.04.17

import gtk
import os

class Logout(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self)
        #self.set_default_size(400,300)
        self.connect("destroy", actions.exit)
        self.set_border_width(3)

        notebook = gtk.Notebook()
        self.add(notebook)
        notebook.set_tab_pos(gtk.POS_TOP)
        notebook.show_tabs = True
        notebook.show_border = False

        self.quitmenu = QuitMenu()
        notebook.append_page(self.quitmenu, gtk.Label(_("Quit Menu")))
        #notebook.append_page(Configure(), gtk.Label(_("Configure")))
        notebook.append_page(Help(), gtk.Label(_("Help")))
        notebook.append_page(About(), gtk.Label(_("About")))

        notebook.set_current_page(0)

    def mainLoop(self):
        self.show_all()
        gtk.main()

    def get_save(self):
        return self.quitmenu.get_save()


class Help(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self.set_border_width(5)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.view = gtk.TextView()
        self.view.set_editable(False)
        #view.set_wrap_mode(gtk.WRAP_WORD)
        sw.add(self.view)
        self.add(sw)
        self.view.show()

        self.reportbuf = self.view.get_buffer()


class About(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self.set_border_width(5)
        box = gtk.VBox()
        box.set_border_width(10)
        label = gtk.Label()
        label.set_line_wrap(True)
        #label.set_alignment(0.0, 0.5)
        label.set_markup(_('<i>larchquit</i> is a desktop quit utility'
                ' designed for <i>larch</i> \'live\' systems.\n'
                'In addition to the normal quit options, it will - on'
                ' suitably configured boot media - present'
                ' \'session-saving\' options to save the current state'
                ' back to the boot medium.\n\n'
                'This program was written for the <i>larch</i> project:\n'
                '       http://larch.berlios.de\n'
                '\nIt is free software,'
                ' released under the GNU General Public License.\n\n') +
                'Copyright (c) 2008   Michael Towers')
        box.pack_start(label)
        self.add(box)


class Configure(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self.set_border_width(10)
        label = gtk.Label()
        label.set_line_wrap(True)
        label.set_markup(_('<b>Not Yet implemented</b>'))
        self.add(label)


class QuitMenu(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, spacing=20)
        self.set_border_width(10)

        # A separate frame for shutdown functions
        frame = gtk.Frame()
        fvbox = gtk.VBox(spacing=10)

        # A layout box for session saving stuff
        fhbox = gtk.HBox(spacing=20)
        fhbox.set_border_width(10)

        self.relogin = gtk.CheckButton(_("Login this user at next system start"))

        # a sub-box for the session-saving options
        fobox = gtk.VBox()

        self.b_save = gtk.RadioButton(None, _("Save state"))
        fobox.pack_start(self.b_save)

        self.b_merge = gtk.RadioButton(self.b_save, _("Merge overlays"))
        fobox.pack_start(self.b_merge)

        self.b_forget = gtk.RadioButton(self.b_save, _("Forget state"))
        fobox.pack_start(self.b_forget)

        self.b_save.set_active(True)

        fhbox.pack_start(self.relogin, False)
        fhbox.pack_end(fobox, False)

        # Try to discover whether session-saving is possible
        if (os.system("/opt/larch-live/session-save/checksave") == 0):
            self.b_save.set_active(True)
            self.relogin.set_active(True)
        else:
            fhbox.set_sensitive(False)
            self.b_forget.set_active(True)
            self.relogin.set_active(False)

        finfo = gtk.Label()
        finfo.set_line_wrap(True)
        #finfo.set_alignment(0.0, 0.5)
        finfo.set_markup(_('Note that the data persistence options will only'
                ' be available when the system has been configured to support'
                ' saving information from the current session.\n'
                'This is the default for <i>larch</i> systems running from'
                ' USB-sticks, but not for CD/DVD devices (as these are'
                ' not normally writable).'))

        # Layout box with reboot and halt buttons
        fbbox = gtk.HBox(spacing=0)

        b_reboot = gtk.Button(_("Reboot"))
        fbbox.pack_start(b_reboot, False, padding=5)
        b_reboot.connect("clicked", actions.shutdown, "r")

        b_shutdown = gtk.Button(_("Shut down"))
        fbbox.pack_start(b_shutdown, False, padding=5)
        b_shutdown.connect("clicked", actions.shutdown, "h")

        # Pack the shutdown frame
        fvbox.pack_start(finfo)
        fvbox.pack_start(fhbox)
        fvbox.pack_end(fbbox, padding=5)
        frame.add(fvbox)

        # Add logout and cancel buttons
        hbox = gtk.HBox(spacing=10)

        b_logout = gtk.Button(_("Logout"))
        hbox.pack_start(b_logout, False)
        b_logout.connect("clicked", actions.logout)

        b_cancel = gtk.Button(_("Cancel"))
        hbox.pack_end(b_cancel, False)
        b_cancel.connect("clicked", actions.exit)

        self.pack_start(frame, False)
        self.pack_end(hbox, False)

    def get_save(self):
        if self.relogin.get_active():
            relogin = os.environ["LOGNAME"]
        else:
            relogin = ""
        if self.b_forget.get_active():
            return ("-", relogin)
        elif self.b_merge.get_active():
            return ("M", relogin)
        else:
            return ("S", relogin)


class Actions:
    def exit(self, widget=None, data=None):
        gtk.main_quit()

    def logout(self, widget=None, data="0"):
        os.system("echo '%s' > /tmp/xlogout" % data)
        if (session == "xfce"):
            os.system("sh -c 'sleep 0.5; xfce4-session-logout' &")
        else:
            error(_("Unsupported session type: %s") % session)
        self.exit()

    def shutdown(self, widget, data):
        sesssionsave, username = gui.get_save()
        if username:
            os.system("echo '%s' > /tmp/newuser" % username)
        self.logout(data=data+sesssionsave)

def error(message):
    md = gtk.MessageDialog(flags=gtk.DIALOG_MODAL |
            gtk.DIALOG_DESTROY_WITH_PARENT, type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_CLOSE, message_format=message)
    md.run()

if __name__ == "__main__":
    import sys
    import __builtin__
    def tr(s):
        return s
    __builtin__._ = tr

    if (len(sys.argv) != 2):
        error(_("Invalid arguments to larchquit.py"))
    else:
        session = sys.argv[1]

        actions = Actions()
        gui = Logout()
        gui.mainLoop()
