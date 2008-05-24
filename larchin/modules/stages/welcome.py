# welcome.py - first - 'welcome' - stage
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
# 2008.02.15

class Welcome(Stage):
    def stageTitle(self):
        return ('<i>larchin</i>: %s' % _("Install Arch Linux"))

    def __init__(self):
        Stage.__init__(self)
        self.addLabel(_('Welcome to <i>larchin</i>. This will install'
                ' Arch Linux on your computer. This program was written'
                ' for the <i>larch</i> project:\n'
                '       http://larch.berlios.de\n'
                '\nIt is free software,'
                ' released under the GNU General Public License.\n\n') +
                'Copyright (c) 2008   Michael Towers')

    def getHelp(self):
        return _("Click on the 'Forward' button to start.")

    def labelL(self):
        return ""

    def forward(self):
        larchdev = install.larchdev().rstrip('0123456789')
        larchcount = 0
        devs = []
        ld = install.listDevices()
        # Note that if one of these has mounted partitions it will not be
        # available for automatic partitioning, and should thus not be
        # included in the list used for automatic installation
        mounts = install.getmounts().splitlines()
        count = 0
        if ld:
            for d, s, n in ld:
                count += 1
                # Mark devices which have mounted partitions
                for m in mounts:
                    if m.startswith(d):
                        if (d == larchdev):
                            larchcount = 1
                        d += "-"
                        count -= 1
                        break
                devs.append([d, s, n])
            install.setDevices(devs)

        if not devs:
            popupError(_("No disk(-like) devices were found,"
                    " so Arch Linux can not be installed on this machine"))
            install.tidyup()
        nds = len(devs)         # Total number of devices
        mds = nds - count       # Number of devices with mounted partitions
        mds2 = mds - larchcount # Number excluding the larch boot device

        if mds2:
            popupMessage(_("%d devices were found with mounted partitions."
                    " These devices are not available for automatic"
                    " partitioning, you must partition them manually.")
                    % mds)

        install.setDevice(None)
        if (count == 1):
            for d, s, n in devs:
                if not d.endswith('-'):
                    install.setDevice(d)
                    break
            mainWindow.goto('partitions')
        elif (count == 0):
            mainWindow.goto('manualPart')
        else:
            mainWindow.goto('devices')


#################################################################

stages['welcome'] = Welcome
