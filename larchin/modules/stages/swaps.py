# swaps.py - formatting swap partitions (expert mode only)
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

class Swaps(Stage):
    def stageTitle(self):
        return _("Format swap partition(s)")

    def getHelp(self):
        return _("Swap partitions will be found on the drives and offered"
                 " for formatting. It is generally good to have a swap"
                 " partition, but it is not necessary, especially if you"
                 " have a lot of memory. 0.5 - 1.0 GB should be plenty"
                 " for most purposes.")

    def __init__(self):
        """
        """
        Stage.__init__(self)
        self.reinit()

    def reinit(self):
        # remove all widgets
        self.clear()

        self.swaps = {}
        inuse = install.getActiveSwaps()
        self.done = []
        if inuse:
            self.addLabel(_("The following swap partitions are currently"
                    " in use and will not be formatted (they shouldn't"
                    " need it!)."))
        for p, s in inuse:
            b = self.addCheckButton("%12s - %s %4.1f GB" % (p, _("size"), s))
            self.setCheck(b, True)
            self.done.append(p)
            self.swaps[p] = b

        all = install.getAllSwaps()
        fmt = []
        for p, s in all:
            if not (p in self.done):
                fmt.append((p, s))
        if fmt:
            self.addLabel(_("The following swap partitions will be formatted"
                    " if you select them for inclusion."))
        for p, s in fmt:
            b = self.addCheckButton("%12s - %s %4.1f GB" % (p, _("size"), s))
            self.setCheck(b, True)
            self.swaps[p] = b

        if not all:
            self.addLabel(_("There are no swap partitions available."))

    def forward(self):
        install.clearSwaps()
        for p, b in self.swaps.items():
            if self.getCheck(b):
                install.addSwap(p, (p not in self.done))

        if not popupWarning(_("The installation will now proceed. Then"
                " there is no way back ...\n\n"
                "Continue?")):
            self.reinit()
            return

        mainWindow.goto('install')


#################################################################

stages['swaps'] = Swaps

