# selpart.py - select partitions manually
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
# 2008.02.05

class SelPart(Stage):
    def stageTitle(self):
        return _("Select installation partitions")

    def getHelp(self):
        return _("The device partitions used for the Arch Linux installation"
                " can be manually selected here.\n"
                "There must be at least an adequately large root ('/')"
                " partition, but the system can be split over a number of"
                " partitions, for example it is often desirable to have a"
                " separate '/home' partition to keep user data separate"
                " from system data and programs. This can be"
                " helpful when updating or changing the operating system.\n\n"
                "Also fairly common are separate partitions for one or more"
                " of '/boot', '/opt', '/usr', '/var', but it is advisable to"
                " inform yourself of the pros and cons before"
                " considering these.")

    def __init__(self):
        Stage.__init__(self)
        from selpart_gui import SelTable, SelDevice

        self.devselect = SelDevice(self, [d[0] for d in install.devices])
        self.addWidget(self.devselect, False)

        filesystems = ['ext3', 'reiserfs', 'ext2', 'jfs', 'xfs']
        # List of mount-point suggestions
        mountpoints = ['/', '/home', '/boot', '/var', '/opt', '/usr']

        self.table = SelTable(self, filesystems, mountpoints)
        self.addWidget(self.table)
        self.reinit()

    def reinit(self):
        self.mounts = install.getmounts()
        self.devselect.setdevice(install.selectedDevice())

    def setDevice(self, dev):
        self.device = dev
        install.getDeviceInfo(self.device)

        self.parts = []
        for p in install.getlinuxparts(self.device):
            if not self.ismounted(p):
                pa = install.getPartition(p)
                if not pa:
                    partno = int(re.sub("/dev/[a-z]+", "", p))
                    size, fstype = install.getPartInfo(partno)
                    pa = install.newPartition(p, size, fstype)
                self.parts.append(pa)

        self.table.renew(self.parts)

    def ismounted(self, part):
        return re.search(r'^%s ' % part, self.mounts, re.M)


    def forward(self):
        for p in install.parts.values():
            if (p.mountpoint == '/'):
                mainWindow.goto('swaps')
                return

        popupError(_("You must specify a root ('/') partition"))


#################################################################

stages['partSelect'] = SelPart
