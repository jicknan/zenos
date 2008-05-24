# partitions.py - select automatic or manual partitioning stage
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

# I think the logic of this stage is probably too complicated ...

class Partitions(Stage):
    def stageTitle(self):
        return _("Choose partitioning scheme")

    def getHelp(self):
        return _("Here you can choose which part(s) of the disk(-like)"
                " device to use for the Arch Linux installation.\n\n"
                "WARNING: If you have an operating system already installed"
                " on this drive which you wish to keep, you must choose"
                " 'expert' partitioning, unless the existing operating"
                " system is on the first partition ONLY, and uses the NTFS"
                " file-system (Windows).\n\n"
                "If the first partition (alone) is occupied by a Windows"
                " operating system, you have here the option of shrinking it"
                " to create enough space for Arch Linux.")

    def __init__(self):
        """Things could have changed if we return to this stage, so
        all the setting up of the data is done in 'reinit'.
        """
        Stage.__init__(self)
        from partitions_gui import NtfsWidget, SwapWidget, HomeWidget
        from partitions_gui import TotalWidget, RootWidget

        # Info: total drive size
        self.totalsize = self.addWidget(TotalWidget())

        # NTFS resizing
        self.ntfs = self.addWidget(NtfsWidget(self))

        # swap size
        self.swap = self.addWidget(SwapWidget(self))

        # home size
        self.home = self.addWidget(HomeWidget(self))

        # root size
        self.root = self.addWidget(RootWidget())

        # Manual partitioning
        self.expert = self.addCheckButton(_("'Expert' (manual) partitioning"),
            self.expert_cb)

        self.reinit()

    def reinit(self):
        self.ntfsFlag = False   # Used for flagging update requests

        install.clearParts()    # Clear list of assigned partitions

        self.dev = install.selectedDevice()
        # Info on drive and partitions (dev="/dev/sda", etc.):
        install.getDeviceInfo(self.dev)
        self.dsize = float(install.dsize) / 1000
        self.totalsize.set(self.dev, self.dsize)

        self.request_update(self.start)

    def start(self):
        self.ntfs.enable(self.keep1init(self.dev))

        self.swap.enable(True)
        self.setCheck(self.expert, False)
        self.ntfs_changed()
        return self.stop_callback()


    def keep1init(self, dev):
        """Only offer to keep first partition if:
            (a) part1 is NTFS, and (b) potential free space > MINLINUXSIZE
        Return True if the option is to be offered.
        """
        self.noshrink = False
        self.forceshrink = False
        self.p1end = 0.0

        MINLINUXSIZE = 5.0      # GB
        if not install.p1end:
            return False        # part1 not NTFS

        self.p1end = float(install.p1end) / 1000

        # Get lowest possible new end point for partition
        ntfsmin = float(install.getNTFSmin(dev+"1") + install.p1start) / 1000
        valmin = ntfsmin + 0.2
        space = ((self.dsize - valmin) >= MINLINUXSIZE)
                # enough (potential) free space?

        valmax = self.p1end - 0.1
        self.forceshrink = ((self.dsize - self.p1end) < MINLINUXSIZE)
        if self.forceshrink:
            # keeping only possible by shrinking
            valmax = self.dsize - MINLINUXSIZE

        self.noshrink = (valmax < valmin)
                # No shrinking possible, partition too full?
        if self.noshrink or not space:
            popupMessage(_("The option to reduce the size of the existing"
                    " operating system is not available because its"
                    " partition is too full."))
            return space

        # slider values
        val = self.dsize / 2
        if (valmax < val):
            val = valmax
        elif (valmin > val):
            val = valmin
        self.ntfs.set_shrinkadjust(lower=valmin, upper=valmax, value=val)

        # Activate shrinking by default if self.forceshrink is set or
        # less than half the drive is free
        self.ntfs.set_shrink(self.forceshrink or (self.p1end > (self.dsize/2)))

        # Enable retention of the first partition by default
        self.ntfs.set_keep1(True)
        return True

    def keep1_cb(self, on):
        enshrink = (on and not self.noshrink)
        self.ntfs.enable_shrink(enshrink)
        if enshrink and self.ntfs.shrinkstate:
            self.ntfs.enable_shrinkswitch(not self.forceshrink)
        self.ntfs_changed()

    def shrink_cb(self, on):
        self.ntfs_changed()

    def ntfssize_cb(self, size):
        self.ntfs_changed()

    def ntfs_changed(self):
        """Signal a change in ntfssize.
        """
        if not self.ntfsFlag:
            self.ntfsFlag = True
            self.request_update(self.recalculate)

    def swapsize_cb(self):
        self.adjustroot()

    def swap_cb(self, on):
        self.adjustroot()

    def homesize_cb(self):
        self.adjustroot()

    def home_cb(self, on):
        self.adjustroot()

    def expert_cb(self, on):
        self.home.enable((not on) and self.home_on)
        self.swap.enable(not on)
        self.adjustroot()

    def adjustroot(self):
        self.rootsize = self.dsize
        if (self.ntfs.is_enabled and self.ntfs.keep1state):
            if self.ntfs.shrinkstate:
                self.rootsize -= self.ntfs.size
            else:
                self.rootsize -= self.p1end

        if (self.swap.is_enabled and self.swap.swapstate):
            self.swap_mb = int(self.swap.size * 1000)
            self.rootsize -= self.swap.size
        else:
            self.swap_mb = 0
        if (self.home.is_enabled and self.home.homestate):
            self.home_mb = int(self.home.size * 1000)
            self.rootsize -= self.home.size
        else:
            self.home_mb = 0
        self.root.set_value(self.rootsize)

    def recalculate(self):
        """Something about the ntfs partition has changed.
        Reevaluate the other partitions. This is an idle callback.
        """
        self.ntfsFlag = False

        MINSPLITSIZE = 20.0    # GB
        SWAPSIZE = 5           # % of total
        SWAPMAX  = 2.0         # GB
        SWAPMAXSIZE = 10       # % of total
        SWAPDEF = 1.0          # GB
        freesize = self.dsize
        if (self.ntfs.is_enabled and self.ntfs.keep1state):
            if self.ntfs.shrinkstate:
                freesize -= self.ntfs.size
            else:
                freesize -= self.p1end

        self.home_on = (freesize >= MINSPLITSIZE)
        home_upper = freesize - SWAPMAX - 5.0
        home_value = home_upper - 2.0
        self.home.set_adjust(upper=home_upper, value=home_value)
        self.home.enable(self.home_on and (not self.getCheck(self.expert)))

        swap_upper = freesize * SWAPMAXSIZE / 100
        if (swap_upper > SWAPMAX):
            swap_upper = SWAPMAX
        swap_value = freesize * SWAPSIZE / 100
        if (swap_value > SWAPDEF):
            swap_value = SWAPDEF
        self.swap.set_adjust(upper=swap_upper, value=swap_value)

        return self.stop_callback()


    def ntfsresize(self):
        """Shrink NTFS filesystem on first partition.
        """
        # convert size to MB
        newsize = int(self.ntfs.size * 1000)
        message = install.doNTFSshrink(newsize)
        if message:
            # resize failed
            popupMessage(_("Sorry, resizing failed. Here is the"
                    " error report:\n\n") + message)
            self.reinit()
            return False
        return True

    def forward(self):
        if (self.ntfs.is_enabled and self.ntfs.keep1state
                and self.ntfs.shrinkstate):
            if not popupWarning(_("You are about to shrink the"
                    " first partition. Make sure you have backed up"
                    " any important data.\n\nContinue?")):
                return
            if not self.ntfsresize():
                self.reinit()
                return

        if self.getCheck(self.expert):
            mainWindow.goto('manualPart')
            return

        # Set up the installation partitions automatically.
        if (self.ntfs.is_enabled and self.ntfs.keep1state):
            text = _(" * Wipe everything except the first partition")
            # allocate partitions from 2nd
            startmark = install.p1end       # altered by ntfsresize
            partno = 2
        else:
            text = _(" * Completely wipe the drive")
            startmark = 0
            partno = 1

        dev = install.selectedDevice()
        if not popupWarning(_("You are about to perform a destructive"
                " operation on the data on your disk drive (%s):\n%s\n\n"
                "This is a risky business, so don't proceed if"
                " you have not backed up your important data.\n\n"
                "Continue?") % (dev, text)):
            self.reinit()
            return

        endmark = install.dsize #-1?

        # Tricky logic here! The first partition should be root, then swap then
        # home, but swap and/or home may be absent. The last partition should take
        # its endpoint from 'endmark', root's start from startmark. The actual
        # partitioning should be done, but the formatting can be handled - given
        # the appropriate information - by the installation stage.

        # Remove all existing partitions (except optionally the first)
        install.rmparts(dev, partno)

        if (self.home_mb == 0) and (self.swap_mb == 0):
            em = endmark
        else:
            em = startmark + int(self.rootsize * 1000)
        install.mkpart(dev, startmark, em)
        startmark = em
        install.newPartition("%s%d" % (dev, partno), m='/', f=True)

        install.clearSwaps()
        if (self.swap_mb != 0):
            partno += 1
            if (self.home_mb == 0):
                em = endmark
            else:
                em = startmark + self.swap_mb
            install.mkpart(dev, startmark, em, 'linux-swap')
            startmark = em
            part = "%s%d" % (dev, partno)
            install.addSwap(part, True)

        if self.home_mb:
            partno += 1
            install.mkpart(dev, startmark, endmark)
            install.newPartition("%s%d" % (dev, partno), m='/home', f=True)

        mainWindow.goto('install')


#################################################################

stages['partitions'] = Partitions

