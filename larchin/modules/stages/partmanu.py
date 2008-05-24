# partmanu.py - manual partitioning stage
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
# 2008.01.30



class ManuPart(Stage):
    def stageTitle(self):
        return _("Edit disk partitions manually")

    def getHelp(self):
        return _("Here you can choose a partitioning tool and/or disk(-like)"
                " device in order to prepare your system to receive an"
                " Arch Linux installation.\n\n"
                "'cfdisk' is a console based tool which should always be"
                " available. It must be started with the name of the"
                " device on which it is to be used.\n\n"
                "'gparted' is a fancy gui-tool which can do much more,"
                " including resizing partitions, but it  may not always"
                " be available. The device to be edited can be selected"
                " from within the program.")

    def __init__(self):
        Stage.__init__(self)

        dev = install.selectedDevice()

        # Offer gparted - if available
        if (install.gparted_available() == ""):
            gparted = self.addOption('gparted',
                    _("Use gparted (recommended)"), True)
        else:
            gparted = None

        # Offer cfdisk on each available disk device
        mounteds = 0
        for d, s, t in install.devices:
            if d.endswith('-'):
                d = d.rstrip('-')
                style = 'red'
                mounteds += 1
            else:
                style = None
            text = _("Use cfdisk on %s") % d
            b = self.addOption('cfdisk-%s' % d, text, style=style)
            if (d == dev) and not gparted:
                b.set_active(True)

        if mounteds:
            self.addLabel(_('WARNING: Editing partitions on a device with'
                    ' mounted partitions (those marked in red) is likely'
                    ' to cause a lot of trouble!\n'
                    'If possible, unmount them and then restart this'
                    ' program.'), style='red')

        # Offer 'use existing partitions/finished'
        self.done = self.addOption('done',
                _("Use existing partitions / finished editing partitions"))


    def forward(self):
        sel = self.getSelectedOption()
        if (sel == 'gparted'):
            install.gparted()
            self.reinit()

        elif (sel == 'done'):
            mainWindow.goto('partSelect')

        else:
            install.cfdisk(sel.split('-')[1])
            self.reinit()


#################################################################

stages['manualPart'] = ManuPart
