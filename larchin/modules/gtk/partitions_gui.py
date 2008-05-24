# partitions_gui.py - extra widgets for the partitions stage
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
# 2008.02.16

import gtk

class NtfsWidget(gtk.Frame):
    """This widget allows an existing operating system (Windows/NTFS)
    to be retained (optionally). It also provides for shrinking the
    partition used by that operating system. This function is just the
    constructor, the logic is handled by other functions.
    """
    def __init__(self, master):
        gtk.Frame.__init__(self)
        self.master = master

        self.keep1 = gtk.CheckButton(_("Retain existing operating system"
                " on first partition"))
        self.set_label_widget(self.keep1)

        adjlabel = gtk.Label(_("Set new size of NTFS partition (GB)"))
        adjlabel.set_alignment(0.9, 0.5)
        self.ntfsadj = gtk.Adjustment(step_incr=0.1, page_incr=1.0)
        hscale = gtk.HScale(self.ntfsadj)

        self.shrink = gtk.CheckButton(_("Shrink NTFS partition"))

        self.ntfsframe = gtk.Frame()
        self.ntfsframe.set_border_width(10)
        self.ntfsframe.set_label_widget(self.shrink)
        self.ntfsbox = gtk.VBox()
        self.ntfsbox.pack_start(adjlabel)
        self.ntfsbox.pack_start(hscale)
        self.ntfsframe.add(self.ntfsbox)

        self.add(self.ntfsframe)

        self.is_enabled = False
        self.keep1state = False
        self.shrinkstate = False
        self.size = 0.0

        self.ntfsadj.connect("value_changed", self.ntfs_size_cb)
        self.shrink.connect("toggled", self.shrink_check_cb)
        self.keep1.connect("toggled", self.keep1_check_cb)


    def enable(self, on):
        """Show (on=True) or hide (on=False) the ntfs shrinking widget.
        """
        if on:
            self.show()
        else:
            self.hide()
        self.is_enabled = on


    def set_keep1(self, on, update=True):
        """Set checkbutton 'keep 1st partition' on or off.
        """
        if (on != self.keep1state):
            self.keep1state = on
            self.master.keep1_cb(on)
        if update:
            self.keep1.set_active(on)

    def keep1_check_cb(self, widget, data=None):
        self.set_keep1(self.keep1.get_active(), False)


    def enable_shrink(self, on):
        if on:
            self.ntfsframe.show()
        else:
            self.ntfsframe.hide()

    def enable_shrinkswitch(self, on):
        self.shrink.set_sensitive(on)

    def set_shrink(self, on, update=True):
        """Set checkbutton 'shrink 1st partition' on or off.
        """
        if (on != self.shrinkstate):
            self.shrinkstate = on
            self.master.shrink_cb(on)
        if update:
            self.shrink.set_active(on)
        if on:
            self.ntfsbox.show()
        else:
            self.ntfsbox.hide()

    def shrink_check_cb(self, widget, data=None):
        self.set_shrink(self.shrink.get_active(), False)


    def set_shrinkadjust(self, lower = None, upper = None,
            value = None, update = True):
        """Set the size adjustment slider. Any of lower limit, upper limit
        and size can be set independently.
        """
        if (lower != None):
            self.ntfsadj.lower = lower
            if (self.size < lower):
                self.size = lower
                self.ntfsadj.value = lower
                self.master.ntfssize_cb(lower)
        if (upper != None):
            self.ntfsadj.upper = upper
            if (self.size > upper):
                self.size = upper
                self.ntfsadj.value = upper
                self.master.ntfssize_cb(upper)
        if ((value != None) and (value != self.size)
                and (value >= self.ntfsadj.lower)
                and (value <= self.ntfsadj.upper)):
            self.size = value
            self.master.ntfssize_cb(value)
            if update:
                self.ntfsadj.value = value

    def ntfs_size_cb(self, widget, data=None):
        self.set_shrinkadjust(value=self.ntfsadj.value, update=False)


class SwapWidget(gtk.Frame):
    """This widget allows a swap partition to be created.
    This function is just the constructor, the logic is handled by
    other functions.
    """
    def __init__(self, master):
        gtk.Frame.__init__(self)
        self.master = master
        adjlabel = gtk.Label(_("Set size of swap partition (GB)"))
        adjlabel.set_alignment(0.9, 0.5)
        self.swapadj = gtk.Adjustment(lower=0.2, step_incr=0.1, page_incr=1.0)
        hscale = gtk.HScale(self.swapadj)

        self.swapon = gtk.CheckButton(_("Create swap partition"))

        self.set_label_widget(self.swapon)
        self.swapbox = gtk.VBox()
        self.swapbox.pack_start(adjlabel)
        self.swapbox.pack_start(hscale)
        self.add(self.swapbox)

        self.is_enabled = False
        self.swapstate = False
        self.size = 0.0
        self.swapadj.connect("value_changed", self.swap_size_cb)
        self.swapon.connect("toggled", self.swap_check_cb)

    def enable(self, on):
        """Show (on=True) or hide (on=False) the swap partition widget.
        """
        if on:
            self.show()
            # Make having a swap partition the default
            self.set_swap(True)
        else:
            self.hide()
        self.is_enabled = on

    def swap_size_cb(self, widget, data=None):
        self.set_adjust(value=self.swapadj.value, update=False)

    def swap_check_cb(self, widget, data=None):
        self.set_swap(self.swapon.get_active(), False)

    def set_swap(self, on, update=True):
        if (on != self.swapstate):
            self.swapstate = on
            self.master.swapsize_cb()
        if on:
            self.swapbox.show()
        else:
            self.swapbox.hide()
        if update:
            self.swapon.set_active(on)

    def set_adjust(self, lower = None, upper = None,
            value = None, update = True):
        """Set the size adjustment slider. Any of lower limit, upper limit
        and size can be set independently.
        """
        osize = self.size
        if (lower != None):
            self.swapadj.lower = lower
            if (self.size < lower):
                self.size = lower
                self.swapadj.value = lower
        if (upper != None):
            self.swapadj.upper = upper
            if (self.size > upper):
                self.size = upper
                self.swapadj.value = upper
        if ((value != None) and (value != self.size)
                and (value >= self.swapadj.lower)
                and (value <= self.swapadj.upper)):
            self.size = value
            if update:
                self.swapadj.value = value

        if (osize != self.size):
            self.master.swapsize_cb()


class HomeWidget(gtk.Frame):
    """This widget allows a separate /home partition to be created.
    This function is just the constructor, the logic is handled by
    other functions.
    """
    def __init__(self, master):
        gtk.Frame.__init__(self)
        self.master = master
        adjlabel = gtk.Label(_("Set size of '/home' partition (GB)"))
        adjlabel.set_alignment(0.9, 0.5)
        self.homeadj = gtk.Adjustment(lower=0.1, step_incr=0.1, page_incr=1.0)
        hscale = gtk.HScale(self.homeadj)

        self.homeon = gtk.CheckButton(_("Create '/home' partition"))

        self.set_label_widget(self.homeon)
        self.homebox = gtk.VBox()
        self.homebox.pack_start(adjlabel)
        self.homebox.pack_start(hscale)
        self.add(self.homebox)

        self.is_enabled = False
        self.homestate = False
        self.size = 0.0
        self.homeadj.connect("value_changed", self.home_size_cb)
        self.homeon.connect("toggled", self.home_check_cb)

    def enable(self, on):
        """Show (on=True) or hide (on=False) the home partition widget.
        """
        if on:
            self.show()
            # Make having a home partition the default
            self.set_home(True)
        else:
            self.hide()
        self.is_enabled = on

    def home_size_cb(self, widget, data=None):
        self.set_adjust(value=self.homeadj.value, update=False)

    def home_check_cb(self, widget, data=None):
        self.set_home(self.homeon.get_active(), False)

    def set_home(self, on, update=True):
        if (on != self.homestate):
            self.homestate = on
            self.master.homesize_cb()
        if on:
            self.homebox.show()
        else:
            self.homebox.hide()
        if update:
            self.homeon.set_active(on)

    def set_adjust(self, lower = None, upper = None,
            value = None, update = True):
        """Set the size adjustment slider. Any of lower limit, upper limit
        and size can be set independently.
        """
        osize = self.size
        if (lower != None):
            self.homeadj.lower = lower
            if (self.size < lower):
                self.size = lower
                self.homeadj.value = lower
        if (upper != None):
            self.homeadj.upper = upper
            if (self.size > upper):
                self.size = upper
                self.homeadj.value = upper
        if ((value != None) and (value != self.size)
                and (value >= self.homeadj.lower)
                and (value <= self.homeadj.upper)):
            self.size = value
            if update:
                self.homeadj.value = value

        if (osize != self.size):
            self.master.homesize_cb()


class RootWidget(gtk.HBox):
    """A widget to display (only - it is not editable) the space
    available for the Linux root ('/') partition when using automatic
    partitioning. When using manual partitioning it shows the total
    amount of space available for Linux.
    """
    def __init__(self):
        gtk.HBox.__init__(self)
        rootlabel = gtk.Label(_("Space for Linux system (GB):  "))
        self.rootsizew = gtk.Entry(10)
        self.rootsizew.set_editable(False)
        self.pack_end(self.rootsizew, False)
        self.pack_end(rootlabel, False)

    def set_value(self, flval):
        self.rootsizew.set_text("%8.1f" % flval)

class TotalWidget(gtk.HBox):
    """A widget to display (only - it is not editable) the total size
    of the current disk drive.
    """
    def __init__(self):
        gtk.HBox.__init__(self)
        self.label = gtk.Label()
        self.sizew = gtk.Entry(10)
        self.sizew.set_editable(False)
        self.pack_end(self.sizew, False)
        self.pack_end(self.label, False)

    def set(self, drive, flval):
        self.label.set_text(_("Total capacity of drive %s (GB):  ") % drive)
        self.sizew.set_text("%8.1f" % flval)

