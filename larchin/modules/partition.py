# partition.py
#
# This module handles information about a single partition which is to
# be in some way relevant (!) to the new installation.
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
# 2008.02.11

class Partition:
    """The instances of this class manage the formatting/mount
    information for a single partition.
    """
    def __init__(self, p, s, fpre, m, f, fnew, mo, fo):
        self.partition = p
        self.size = s
        self.existing_format = fpre
        self.mountpoint = m
        self.mount_options = None
        self.newformat = fnew
        self.format = f
        if self.format:
            if not self.newformat:
                self.newformat = 'ext3'
            if (fo != None):
                self.format_options = fo
            else:
                self.format_options = self.default_flags(
                        self.format_flags(self.newformat))

            if self.mountpoint:
                if (mo != None):
                    self.mount_options = mo
                else:
                    self.mount_options = self.default_flags(
                            self.mount_flags(self.newformat or
                                    self.existing_format))

        else:
            self.newformat = None
            self.format_options = None
            self.mountpoint = None

    def format_flags(self, fstype):
        """Return a list of available format flags for the given
        file-system type.
        """
        # At the moment there is only an entry for 'ext3'
        return { 'ext3' : [
                (_("disable boot-time checks"), 'd', False,
                    _("Normally an ext3 file-system will be checked every"
                      " 30 mounts or so. With a large partition this can"
                      " take quite a while, and some people like to disable"
                      " this and just rely on the journalling.")),

                (_("directory indexing"), 'i', True,
                    _("This is supposed to speed up access.")),

                (_("full journal"), 'f', False,
                    _("This is supposed to increase data safety, at some"
                      " small cost in speed (and disk space?)"))
                ],
            }.get(fstype)

    def mount_flags(self, fstype):
        """Return a list of available mount (/etc/fstab) flags for the
        given file-system type.
        """
        # At the moment there are just these two flags
        if fstype:
            flg = [ (_("noatime"), 'T', True,
                    _("Disables recording atime (access time) to disk, thus"
                      " speeding up disk access. This is unlikely to cause"
                      " problems (famous last words ...). Important for"
                      " flash devices")),

                    (_("nodiratime"), 'D', True,
                    _("Disables recording directory access time to disk, thus"
                      " speeding up disk access. This is unlikely to cause"
                      " problems (famous last words ...). Important for"
                      " flash devices")),

                    (_("noauto"), 'A', False,
                    _("Don't mount this partition during system"
                      " initialization."))
                ]

            # And nothing file-system specific
            return flg
        else:
            return None

    def default_flags(self, flist):
        """Return the default set of flags for the given list of flags
        (output of mount_flags or format_flags).
        """
        flags = ''
        if flist:
            for f in flist:
                if f[2]:
                    flags += f[1]
        return flags

    def format_cb(self, table, on):
        self.format = on
        table.enable_fstype(self, on)
        table.enable_mountpoint(self, on)
        # Ensure changed signal emitted when real setting passed (later)
        table.set_fstype(self, None)
        if on:
            newfs = self.existing_format
            if not newfs:
                newfs = 'ext3'
            table.set_fstype(self, newfs)

        else:
            self.newformat = None
            if not self.mountpoint:
                self.mount_options = None

    def fstype_cb(self, table, fstype):
        if self.format:
            # if formatting
            on = True
            self.newformat = fstype
        else:
            on = False
            self.newformat = None
            table.set_mountpoint(self, None)

        table.enable_mountpoint(self, on)

        if fstype:
            self.format_options = self.default_flags(
                    self.format_flags(self.newformat))
            if self.mountpoint:
                # set default mount options
                self.mount_options = self.default_flags(self.mount_flags(
                        self.newformat or self.existing_format))
        else:
            self.format_options = None

    def get_format_options(self):
        fopts = []
        if self.format:
            # Options only available if format box is checked
            fl = self.format_flags(self.newformat)
            if fl:
                for name, flag, on, desc in fl:
                    fopts.append((name, flag, flag in self.format_options,
                            desc))
        return fopts

    def get_mount_options(self):
        mopts = []
        if self.mountpoint:
            # Options only available if mount-point is set and partition
            # has (or will have) a file-system
            fl = self.mount_flags(self.newformat or self.existing_format)
            if fl:
                for name, flag, on, desc in fl:
                    mopts.append((name, flag, flag in self.mount_options,
                            desc))
            elif (fl == None):
                return None
            return mopts
        return None

    def mountpoint_cb(self, m):
        if m.startswith('/'):
            # set default mount options
            self.mount_options = self.default_flags(self.mount_flags(
                    self.newformat or self.existing_format))
            self.mountpoint = m
        else:
            self.mountpoint = None
            self.mount_options = None

    def format_options_cb(self, opt, on):
        if on:
            if not opt in self.format_options:
                self.format_options += opt
        else:
            self.format_options = self.format_options.replace(opt, '')

    def mount_options_cb(self, opt, on):
        if on:
            if not opt in self.mount_options:
                self.mount_options += opt
        else:
            self.mount_options = self.mount_options.replace(opt, '')


