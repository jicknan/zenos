#!/usr/bin/env python
#
# larchin - A hard-disk installer for Arch Linux and larch
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
# 2008.02.27

import os, sys

basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("%s/modules" % basedir)
sys.path.append("%s/modules/gtk" % basedir)

from install import installClass
from larchinmain import Larchin
from dialogs import popupError

def errorTrap(type, value, tb):
    etext = "".join(traceback.format_exception(type, value, tb))
    popupError(etext, _("This error could not be handled."))
    if initialized:
        try:
            install.tidyup()
        except:
            pass
    quit()


import __builtin__
def tr(s):
    return s
__builtin__._ = tr

import traceback
initialized = False

sys.excepthook = errorTrap

transfer = False
if (len(sys.argv) == 1):
    target = None
elif (len(sys.argv) == 2):
    target = sys.argv[1]
else:
    popupError(_("Usage:\n"
        "          larchin.py \t\t\t\t # local installation\n"
        "          larchin.py target-address \t # remote installation\n"),
        _("Bad arguments"))
    quit()

__builtin__.basePath = basedir
__builtin__.stages = {}
__builtin__.mainWindow = Larchin()
__builtin__.install = installClass(target)
initialized = True
mainWindow.goto('welcome')
mainWindow.mainLoop()
