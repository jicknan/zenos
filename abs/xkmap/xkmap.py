#!/usr/bin/env python
#
# xkmap.py   --  Simple GUI for 'setxkbmap'
#
# Copyright (C) 2006-2008  Michael Towers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#-------------------------------------------------------------------
# 2008.06.19

# Set this for your system (probably one of these is OK)
base_lst = "/usr/share/X11/xkb/rules/base.lst"
#base_lst = "/etc/X11/xkb/rules/base.lst"
#base_lst = "/usr/lib/X11/xkb/rules/base.lst"

# The files are the global and local keymap settings files
configall = "/etc/X11/xinit/xkmap.conf"
configuser = "~/.xkmap.conf"
#-------------------------------------------------------------------

import os, sys
from subprocess import Popen, PIPE, STDOUT

# For running utilities as root:
import pexpect

import gtk, pango

# The not yet implemented i18n bit ...
import __builtin__
def tr(s):
    return s
__builtin__._ = tr


abouttext = _('<i>xkmap</i> is a simple gui front-end for <i>setxkbmap</i>,'
                ' for setting the keyboard mapping for the Xorg graphical'
                ' windowing system. It was designed for <i>larch</i> \'live\''
                ' systems but should work on most linux systems.\n'
                'To keep it simple it doesn\'t support all the options'
                ' which are available for keyboard configuration, but just'
                ' allows setting of the model, layout and variant.\n\n'
                'This program was written for the <i>larch</i> project:\n'
                '       http://larch.berlios.de\n'
                '\nIt is free software,'
                ' released under the GNU General Public License.\n')


helptext = _("""XKMAP:
Xorg keymaps can be set immediately by clicking 'Apply'.
'Quit' exits without making any changes.

Not all keyboard mapping possibilities offered by Xorg
are supported by this utility, only the basic models,
layouts and variants in the ..../xkb/rules/base.lst
file.

It is possible to make the settings here permanent,
but it depends on how you start X. At some point
the script xkmap-set must be run. One possibility
would be to run it from your .xinitrc file, or maybe
your desktop has an Autorun folder.

One can have a global (for all users) keymap setting,
in which case the configuration will be stored in
'etc/X11/xinit/xkmap.conf'. In that case you must
be running 'xkmap' as root, or else enter the root
password when prompted.
Each user may override the global setting with his
own configuration in '~/.xkmap.conf'.
One may also specify that the changes are for immediate
use in the current session only.
""")


class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        #self.set_default_size(400,300)
        self.connect("destroy", self.exit)
        self.set_border_width(3)

        # Root password
        self.password = None

        self.notebook = gtk.Notebook()
        self.add(self.notebook)
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.notebook.show_tabs = True
        self.notebook.show_border = False

        self.setup()

    def init(self, maintabtitle):
        self.maintab = MainTab()
        self.addPage(self.maintab, gtk.Label(maintabtitle))
        self.addPage(Help(), gtk.Label(_("Help")))
        self.addPage(About(), gtk.Label(_("About")))

        self.notebook.set_current_page(0)

    def addPage(self, widget, label):
        self.notebook.append_page(widget, label)

    def mainLoop(self):
        self.show_all()
        gtk.main()

    def exit(self, widget=None, data=None):
        self.pending()
        gtk.main_quit()

    def rootrun(self, cmd):
        """Run the given command as 'root'.
        Return a pair (completion code, output).
        """
        # If not running as 'root' use pexpect to use 'su' to run the command
        if (os.getuid() == 0):
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
            o = p.communicate()[0]
            return (p.returncode, o)
        else:
            if not self.password:
                pw = popupRootPassword()
                if (pw == None):
                    return (1, _("You cancelled the operation."))
                cc, mess = asroot('true', pw)
                if (cc != 0):
                    return (cc, mess)
                self.password = pw
            return asroot(cmd, self.password)

    def setup(self):
        """This function is called during initialization of the main window.
        It can be used for setting up instance variables, etc.
        """
        pass

    def pending(self):
        """This function is called just before quitting the program.
        It can be used to do tidying up.
        """
        pass

    def get_savemode(self):
        return self.maintab.get_savemode()


def popupMessage(text, title=""):
    dialog = gtk.MessageDialog(gui,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            title)
    dialog.format_secondary_markup(text)
    dialog.set_title(_("xkmap"))
    dialog.run()
    dialog.destroy()

def popupRootPassword():
    dialog = gtk.Dialog(parent=gui,
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    label = gtk.Label(_("To complete this operation you must enter"
            " the root (administrator) password:"))
    label.set_line_wrap(True)
    label.set_alignment(0.0, 0.5)
    dialog.vbox.pack_start(label)
    label.show()
    entry = gtk.Entry(max=20)
    entry.set_visibility(False)
    dialog.vbox.pack_start(entry)
    entry.show()
    entry.connect('activate', enterKey_cb, dialog)
    if (dialog.run() == gtk.RESPONSE_ACCEPT):
        val = entry.get_text()
    else:
        val = None
    dialog.destroy()
    return val

def enterKey_cb(widget, dialog):
    """A callback for the Enter key in dialogs.
    """
    dialog.response(gtk.RESPONSE_ACCEPT)

def asroot(cmd, pw):
    """Run a command as root, using the given password.
    """
    child = pexpect.spawn('su -c "%s"' % cmd)
    child.expect(':')
    child.sendline(pw)
    child.expect(pexpect.EOF)
    o = child.before.strip()
    return (0 if (o == '') else 1, o)


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
        self.reportbuf.set_text(helptext)


class About(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self.set_border_width(5)
        box = gtk.VBox()
        box.set_border_width(10)
        label = gtk.Label()
        label.set_line_wrap(True)
        #label.set_alignment(0.0, 0.5)
        label.set_markup(abouttext + '\nCopyright (c) 2008   Michael Towers')
        box.pack_start(label)
        self.add(box)


class MainTab(gtk.VBox):
    def __init__ (self):
        gtk.VBox.__init__(self, spacing=5)
        self.block_cb = True

        title = gtk.Label()
        title.set_markup('<span size="xx-large">%s</span>' %
                _("Set Keyboard Mapping"))
        self.pack_start(title, False)

        self.pack_start(gtk.HSeparator(), False)

        self.modelframe = XCombo(_("Model"), callback=self.model_cb)
        self.pack_start(self.modelframe, False)

        self.layoutframe = XCombo(_("Layout"), callback=self.layout_cb)
        self.pack_start(self.layoutframe, False)

        self.variantframe = XCombo(_("Variant"), callback=self.variant_cb)
        self.pack_start(self.variantframe, False)

        sessiononly = gtk.RadioButton(group=None,
                label=_("Setting applies to current session only"))
        sessiononly.set_active(True)
        self.pack_start(sessiononly, False)
        self.usersave = gtk.RadioButton(group=sessiononly,
                label=_("Save setting for current user"))
        self.pack_start(self.usersave, False)
        self.allsave = gtk.RadioButton(group=self.usersave,
                label=_("Save setting for all users"))
        self.pack_start(self.allsave, False)


        buttons = gtk.HButtonBox()
        buttons.set_direction(gtk.TEXT_DIR_NONE)
        buttons.set_layout(gtk.BUTTONBOX_END)
        buttons.set_border_width(3)
        buttons.set_spacing(5)
        self.pack_end(buttons, False)

        but_apply = gtk.Button(stock=gtk.STOCK_APPLY)
        buttons.add(but_apply)
        but_apply.connect('clicked', self.apply)
        but_quit = gtk.Button(stock=gtk.STOCK_QUIT)
        buttons.add(but_quit)
        but_quit.connect('clicked', gui.exit)

        self.modelframe.set_list(i_xkbset.models)
        self.iModel = self.modelframe.select(i_xkbset.model)

        self.layoutframe.set_list(i_xkbset.layouts)
        self.iLayout = self.layoutframe.select(i_xkbset.layout)

        self.showVariants()

        self.block_cb = False

    def showVariants (self):
        layout = i_xkbset.layouts[self.iLayout].split()[0]
        self.variants = i_xkbset.getVariants(layout)
        self.variantframe.set_list(self.variants)
        self.iVariant = self.variantframe.select(i_xkbset.variant)

    def apply(self, widget, data=None):
        i_xkbset.new()

    def model_cb(self, i, val):
        self.iModel = i
        i_xkbset.model = val

    def layout_cb(self, i, val):
        if (not self.block_cb) and i != self.iLayout:
            self.iLayout = i
            i_xkbset.layout = val
            self.showVariants()

    def variant_cb(self, i, val):
        self.iVariant = i
        i_xkbset.variant = val

    def get_savemode(self):
        if self.usersave.get_active():
            return 'user'
        elif self.allsave.get_active():
            return 'all'
        else:
            return None


class Xkbset:
    def __init__(self):
        self.configuser = os.path.expanduser(configuser)
        if os.path.isfile(self.configuser):
            configfile = self.configuser
        elif os.path.isfile(configall):
            configfile = configall
        else:
            configfile = None
        if configfile:
            f = open(configfile)
            self.model, self.layout, self.variant = f.read().split()
            f.close()
        else:
            # default values
            self.model = "pc101"
            self.layout = "us"
            self.variant = "Standard"

        # Read 'base.lst'
        blf = open(base_lst)
        while blf.readline().strip() != "! model": pass

        self.models = []
        while True:
            line = blf.readline().strip()
            if not line: continue
            if line == "! layout": break
            self.models.append(line)

        self.layouts = []
        while True:
            line = blf.readline().strip()
            if not line: continue
            if line == "! variant": break
            self.layouts.append(line)

        self.layouts.sort()

        self.allVariants = {}
        while True:
            line = blf.readline().strip()
            if not line: continue
            if line == "! option": break
            parts = line.split (None, 2)
            line = parts[0] + " " + parts[2]
            layout = parts[1].rstrip (":")
            if not self.allVariants.has_key(layout):
                self.allVariants[layout] = [ "Standard" ]
            self.allVariants[layout].append(line)

        blf.close()

    def getVariants(self, layout):
        if not self.allVariants.has_key(layout):
            return [ "Standard" ]
        else:
            return self.allVariants[layout]

    def new(self):
        command = ("setxkbmap -rules xorg -model %s -layout %s" %
                (self.model, self.layout))
        if self.variant != "Standard":
            command += " -variant " + self.variant
        os.system(command)

        savemode = gui.get_savemode()
        if (savemode == 'user'):
            f = open(self.configuser, "w")
            f.write("%s %s %s\n" % (self.model, self.layout, self.variant))
            f.close()
        elif (savemode == 'all'):
            if os.path.isfile(self.configuser):
                os.remove(self.configuser)
            if (os.getuid() != 0):
                cmd = "echo '%s %s %s' >%s" % (self.model,
                        self.layout, self.variant, configall)
                gui.rootrun(cmd)

        popupMessage(_("Keyboard set to:\n"
                "  model %s\n"
                "  layout %s\n"
                "  variant %s") % (self.model, self.layout, self.variant))


class XCombo(gtk.Frame):
    def __init__(self, label=None, callback=None):
        gtk.Frame.__init__(self, label)
        self.combo = gtk.ComboBox()
        # Need some space around the combo box. The only way I've found
        # of doing this (so far) is to add an extra layout widget ...
        border = gtk.Table()
        border.attach(self.combo, 0, 1, 0, 1, xpadding=3, ypadding=3)
        self.add(border)

        self.list = gtk.ListStore(str, str)
        self.combo.set_model(self.list)
        cell1 = gtk.CellRendererText()
        #cell1.set_fixed_size(80, -1)
        cell1.set_property('width-chars', 15)
        #cell1.set_property('cell-background', 'red')
        cell1.set_property('ellipsize', pango.ELLIPSIZE_END)
        self.combo.pack_start(cell1, expand=False)
        self.combo.add_attribute(cell1, 'text', 0)
        cell2 = gtk.CellRendererText()
        cell2.set_property('foreground', '#a08000')
        self.combo.pack_start(cell2)
        self.combo.add_attribute(cell2, 'text', 1)

        self.blocked = False
        self.combo.connect('changed', self.changed_cb, callback)

    def set_list(self, values):
        self.blocked = True
        self.list.clear()
        for v in values:
            ab = v.split(None, 1)
            if (len(ab) == 1):
                a, b = v, ''
            else:
                a, b = ab
            self.list.append([a, b])
        while gtk.events_pending():
            gtk.main_iteration(False)
        self.blocked = False

    def changed_cb(self, widget, callback=None):
        if self.blocked or not callback:
            return
        i = self.combo.get_active()
        v = self.list[i][0]
        callback(i, v)

    def getval(self):
        """Return the selected value (first column only).
        """
        return self.list[self.combo.get_active()][0]

    def select(self, val):
        """Programmatically set the currently selected entry.
        Return the selected index.
        """
        i = 0
        for u in self.list:
            if (u[0] == val):
                self.combo.set_active(i)
                return i
            i += 1
        self.combo.set_active(0)
        return 0



if __name__ == "__main__":
    i_xkbset = Xkbset ()
    gui = MainWindow()
    gui.init(_("Key Maps"))
    gui.mainLoop()

