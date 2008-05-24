# devices.py - select installation device stage
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
# 2008.01.23


class Devices(Stage):
    def stageTitle(self):
        return _("Select installation device")

    def getHelp(self):
        return _("Here you can choose to which of the disk(-like) devices"
                " you want to install Arch Linux.\n\n"
                "Select one of the devices"
                " and click on the 'Forward' button.\n\n"
                "To use partitions from more than one device, or to use a"
                " device on which partitions are currently mounted (such "
                " partitions are not shown here), you must select"
                " 'manual partitioning' and click on the 'Forward' button."
                " You will be taken to the manual partitioning menu.")

    def __init__(self):
        Stage.__init__(self)

        i = 0
        for d, s, n in install.devices:
            if d.endswith('-'):
                continue
            i += 1
            self.addOption(d, "%16s  (%10s : %s)" % (d, s, n), (i == 1))

        self.addOption('manual', _("Manual partitioning"))


    def forward(self):
        sel = self.getSelectedOption()
        if (sel == 'manual'):
            mainWindow.goto('manualPart')
        else:
            install.setDevice(sel)
            mainWindow.goto('partitions')


#################################################################

stages['devices'] = Devices
