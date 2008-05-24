#!/usr/bin/env python
#
# localed - A gui to configure supported locales in Arch Linux
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
# 2008.04.27

import os, sys, re, time
from subprocess import Popen, PIPE, STDOUT
import gtk

# For running utilities as root:
import pexpect

STARTFLAG = "###+++ autogen"
ENDFLAG = "###--- autogen"

basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# The not yet implemented i18n bit ...
import __builtin__
def tr(s):
    return s
__builtin__._ = tr


abouttext = _('<i>localed</i> is a simple gui program for setting the'
                ' supported glibc locales and the currently selected'
                ' locale. It was designed for <i>larch</i> \'live\''
                ' systems but is just as applicable to other Arch Linux'
                ' installations.\n\n'
                'This program was written for the <i>larch</i> project:\n'
                '       http://larch.berlios.de\n'
                '\nIt is free software,'
                ' released under the GNU General Public License.\n')


helptext = _("""LOCALED:
To move a locale from the 'supported' to the 'unsupported'
column, or vice versa, select it (multiple selection is
possible) and click on the appropriate arrow button.

The locale data will only be generated (i.e. the
system will only be updated) when you click on the
'Apply' button.
'Cancel' exits without making any (further) changes.
Clicking on the 'Revert' button causes non-applied
changes to be reverted, by reloading the system state.

The locale selected at boot (in /etc/rc.conf) can also
be set here, from the available ones, by choosing the
desired entry from the combo-box 'System locale'. If
the value in rc.conf is not one of those deemed to be
acceptable by this program (that doesn't necessarily
mean the value really is invalid) it will appear in red.
The locales available for selection are those from
'locale -a' which contain a '.' (so that the encoding is
clear), together with 'POSIX' and 'C'.
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

    def startrootcmd(self, cmd):
        """This function starts up a root command using pexpect, using
        'su' and passing the password if necessary (self.password must
        already be valid).
        """
        if (os.getuid() == 0):
            self.childp = pexpect.spawn(cmd)
        else:
            self.childp = pexpect.spawn('su -c "%s"' % cmd)
            self.childp.expect(':')
            self.childp.sendline(self.password)

    def getline(self):
        """This function gets a line of output from the pexpect command
        started by startrootcmd. When the command finishes 'None' is returned.
        """
        i = self.childp.expect (['\r\n', pexpect.EOF])
        if i==0:
            return self.childp.before
        else:
            return None


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
    def __init__(self):
        self.localegen = rootdir + '/etc/locale.gen'
        if not os.path.isfile(self.localegen):
            popupError(_("File '%s' not found") % self.localegen,
                _("Bad arguments"))
            quit()
        self.rcconf = rootdir + '/etc/rc.conf'

        gtk.VBox.__init__(self, False)
        header = gtk.Label()
        header.set_markup(_("<b><big>Configure supported locales</big></b>"))
        self.pack_start(header, False, padding=20)
        hbox = gtk.HBox(False, spacing=5)
        self.pack_start(hbox)

        self.sublistbox = SubListBox(_("Supported"), _("Unsupported"))
        hbox.pack_start(self.sublistbox)

        sep1 = gtk.VSeparator()
        hbox.pack_start(sep1)

        vbox = gtk.VBox(False, spacing=5)
        hbox.pack_start(vbox)

        tframe = gtk.Frame(_("Output"))
        scroll = gtk.ScrolledWindow()
        scroll.set_border_width(5)
        tframe.add(scroll)
        self.textview = gtk.TextView()
        self.textview.set_editable(False)
        scroll.add(self.textview)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_size_request(250, 250)
        vbox.pack_start(tframe)

        frame = gtk.Frame()
        frame.set_label(_("System locale"))
        self.combolist = gtk.ListStore(str)
        self.lcombo = gtk.ComboBoxEntry(self.combolist, 0)
        self.lcomboentry = self.lcombo.child
        self.lcomboclr0 = self.lcomboentry.get_style().text[gtk.STATE_NORMAL]
        self.lcomboclr1 = gtk.gdk.color_parse('#FF0000')
        self.lcomboentry.connect('changed', self.entry_cb)
        self.lcomboentry.set_editable(False)
        #doesn't work: self.lcombo.set_border_width(5)
        pbox = gtk.Table()
        pbox.attach(self.lcombo, 0, 1, 0, 1, xpadding=5, ypadding=5)

        frame.add(pbox)
        vbox.pack_start(frame, False)

        bbox = gtk.HButtonBox()
        vbox.pack_end(bbox, False)
        bbox.set_layout(gtk.BUTTONBOX_END)
        rbutton = gtk.Button(stock=gtk.STOCK_REVERT_TO_SAVED)
        rbutton.connect('clicked', self.revert_cb)
        bbox.add(rbutton)
        cbutton = gtk.Button(stock=gtk.STOCK_CANCEL)
        cbutton.connect('clicked', gui.exit)
        bbox.add(cbutton)
        abutton = gtk.Button(stock=gtk.STOCK_APPLY)
        abutton.connect('clicked', self.apply_cb)
        bbox.add(abutton)

        self.process = None

    def readlocales(self):
        self.sublistbox.clear()
        self.cleanfile = ''     # build up a fully commented-out template
        locales = []    # list of locales, also used for duplicate checking
        lactive = []    # list of 'active/selected' flags for locales
        mask = False    # flag used to skip over automatically generated lines

        rx = re.compile("[#]? *([a-z][a-z]_.*)")
        fh = open(self.localegen, "r")
        for line in fh:
            l = line.strip()
            if l.startswith(STARTFLAG):
                mask = True
                continue
            elif l.startswith(ENDFLAG):
                mask = False
                continue
            rm = rx.match(l)
            active = (l != '') and not l.startswith('#')
            if rm:
                val = rm.group(1)
                if not val in locales:
                    locales.append(val)
                    lactive.append(active)
            if mask:
                continue
            if active:
                l = '#' + l
            self.cleanfile += l + '\n'
        fh.close()
        #print self.cleanfile

        # add locales to widget, after sorting (just in case ...)
        l0 = [(locales[i], lactive[i]) for i in range(len(locales))]
        l0.sort()
        for l, a in l0:
            self.sublistbox.additem(l, a)

        self.listUpdated()

    def getlocalenames(self):
        """Fetch a list of locale names suitable for use in rc.conf setting
        ('LOCALE'). This is not exhaustive, it just takes the locales
        from 'locale -a' which contain a '.' (so that the encoding is clear)
        and adds 'POSIX' and 'C'.
        """
        if rootdir:
            o = gui.rootrun('chroot %s locale -a' % rootdir)[1]
        else:
            o = Popen(['locale', '-a'], stdout=PIPE).communicate()[0]
        ll = [ l for l in o.splitlines() if '.' in l ]
        return ['C', 'POSIX'] + ll

    def entry_cb(self, w, data=None):
        # The text in the entry is painted red when it is not in the list.
        # If the value differs from the current value in rc.conf, that is
        # updated.
        current = self.lcomboentry.get_text()
        if current in self.getlocalenames():
            self.lcomboentry.modify_text(gtk.STATE_NORMAL, self.lcomboclr0)
            cl = self.getcurrent()
            if (current != cl):
                # Edit rc.conf
                gui.rootrun("sed -i 's|^LOCALE=.*|LOCALE=\"%s\"|' %s" %
                        (current, self.rcconf))

        else:
            self.lcomboentry.modify_text(gtk.STATE_NORMAL, self.lcomboclr1)

    def listUpdated(self):
        locales = self.getlocalenames()
        self.combolist.clear()
        for l in locales:
            self.combolist.append((l,))

        self.entry_cb(self.lcomboentry)

    def getcurrent(self):
        locale = None
        fh = open(self.rcconf, "r")
        for line in fh:
            l = line.strip()
            lsplit = l.split('=', 1)
            if (len(lsplit) != 2) or (lsplit[0] != 'LOCALE'):
                continue
            locale = lsplit[1]
            if (((locale[0] == '"') and (locale[-1] == '"')) or
                    ((locale[0] == "'") and (locale[-1] == "'"))):
                locale = locale[1:-1]
            break
        fh.close()
        return locale

    def output(self, text):
        buf = self.textview.get_buffer()
        iter = buf.get_end_iter()
        buf.insert(iter, text)

    def revert_cb(self, w=None, data=None):
        if self.process:
            return
        self.readlocales()
        locale = self.getcurrent()
        if (locale == None):
            popupError(_("No locale in %s!!!") % self.rcconf)
            gui.exit()

        self.lcomboentry.set_text(locale)


    def apply_cb(self, w, data=None):
        # Generate locales
        # Ideally this should start the process and set up a callback to
        # print the output when it is available (line-by-line)
        if self.process:
            return
        else:
            self.process = True

        # Edit locale.gen
        gui.rootrun("mv %s %s" % (self.localegen, self.localegen + '.old'))
        while gtk.events_pending():
            gtk.main_iteration(False)
        newlocales = ""
        for l in self.sublistbox.getsupported():
            newlocales += l + '\n'
        gui.rootrun("cat <<EOF >%s\n%s\n%s%s\n%sEOF" % (self.localegen,
                STARTFLAG, newlocales, ENDFLAG, self.cleanfile))
        while gtk.events_pending():
            gtk.main_iteration(False)

        if rootdir:
            gui.startrootcmd("chroot %s locale-gen" % rootdir)
        else:
            gui.startrootcmd("locale-gen")

        while True:
            op = gui.getline()
            if (op == None):
                break
            self.output(op + '\n')
            while gtk.events_pending():
               gtk.main_iteration(False)

        self.process = None

        # Adjust the list of selectable locales
        self.listUpdated()


def popupError(text, title=""):
    dialog = gtk.MessageDialog(None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            title)
    dialog.format_secondary_text(text)
    dialog.set_title(_("localed Error"))
    dialog.run()
    dialog.destroy()


class SubListBox(gtk.HBox):
    def __init__(self, header1=None, header2=None):
        gtk.HBox.__init__(self, False)
        columnwidth = 150

        # create a ListStore with one string column and one boolean (filter)
        # column to use as the model
        self.liststore = gtk.ListStore(str, bool)

        # 1st list ('supported')
        sw_sel = gtk.ScrolledWindow()
        sw_sel.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw_sel.set_shadow_type(gtk.SHADOW_IN)
        sw_sel.set_size_request(columnwidth, -1)

        self.sel_filter = self.liststore.filter_new()
        self.sel_filter.set_visible_column(1)

        # create the 'selected' TreeView using filtered liststore
        self.sel_view = gtk.TreeView(self.sel_filter)

        # create a CellRenderer to render the data
        self.cell = gtk.CellRendererText()

        # create the TreeViewColumn to display the data
        self.tvcolumn = gtk.TreeViewColumn(header1, self.cell, text=0)

        # add column to treeview
        self.sel_view.append_column(self.tvcolumn)

        # place treeview in scrolled window
        sw_sel.add(self.sel_view)

        # add scrolled window to hbox
        self.pack_start(sw_sel)

        # Transfer-buttons
        bt_sel = gtk.Button()
        larrow = gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_OUT)
        bt_sel.add(larrow)
        bt_sel.connect("clicked", self.tosel)
        bt_unsel = gtk.Button()
        rarrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_OUT)
        bt_unsel.add(rarrow)
        bt_unsel.connect("clicked", self.tounsel)
        vbox = gtk.VBox(False, spacing=20)
        alignment = gtk.Alignment(yalign=0.5)
        alignment.add(vbox)
        self.pack_start(alignment, False, padding=5)
        vbox.pack_start(bt_sel, False)
        vbox.pack_start(bt_unsel, False)


        # 2nd list ('unsupported')
        sw_unsel = gtk.ScrolledWindow()
        sw_unsel.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw_unsel.set_shadow_type(gtk.SHADOW_IN)
        sw_unsel.set_size_request(columnwidth, -1)

        self.unsel_filter = self.liststore.filter_new()
        self.unsel_filter.set_visible_func(self.unselected)

        # create the 'selected' TreeView using filtered liststore
        self.unsel_view = gtk.TreeView(self.unsel_filter)

        # create the TreeViewColumn to display the data
        self.tvcolumn2 = gtk.TreeViewColumn(header2, self.cell, text=0)

        # add column to treeview
        self.unsel_view.append_column(self.tvcolumn2)

        # place treeview in scrolled window
        sw_unsel.add(self.unsel_view)

        # add scrolled window to hbox
        self.pack_start(sw_unsel)

        self.sel_selection = self.sel_view.get_selection()
        self.sel_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.unsel_selection = self.unsel_view.get_selection()
        self.unsel_selection.set_mode(gtk.SELECTION_MULTIPLE)

    def clear(self):
        self.liststore.clear()

    def additem(self, text, sel):
        self.liststore.append((text, sel))

    def unselected(self, model, iter, user_data=None):
        """A filter function, just negates the boolean column in the
        list model.
        """
        return not model.get_value(iter, 1)

    def selectedpaths(self, sel):
        model, pathlist = sel.get_selected_rows()
        return pathlist

    def getsupported(self):
        """Get the names of the locales in the 'supported' view.
        """
        return [r[0] for r in self.sel_filter]

    # These two functions move entries between lists. I collect iters to
    # all affected self.liststore entries before making any changes because
    # I expect a change will affect the paths in the filtered stores.
    def tosel(self, w, data=None):
        iters = []
        for path in self.selectedpaths(self.unsel_selection):
            iter = self.unsel_filter.get_iter(path)
            iters.append(self.unsel_filter.convert_iter_to_child_iter(iter))

        for i in iters:
            self.liststore.set_value(i, 1, True)

    def tounsel(self, w, data=None):
        iters = []
        for path in self.selectedpaths(self.sel_selection):
            iter = self.sel_filter.get_iter(path)
            iters.append(self.sel_filter.convert_iter_to_child_iter(iter))

        for i in iters:
            self.liststore.set_value(i, 1, False)


if __name__ == '__main__':
    if (len(sys.argv) == 1):
        rootdir = ''
    elif (len(sys.argv) == 2):
        rootdir = sys.argv[1]
    else:
        popupError(_("Usage:\n"
            "          localed.py [system root directory (default is '/')]\n"),
            _("Bad arguments"))
        quit()

    gui = MainWindow()
    gui.init(_("Locales"))
    gui.maintab.revert_cb()
    gui.mainLoop()
