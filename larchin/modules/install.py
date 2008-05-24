# install.py
#
# This module handles communication with the system on which Arch is to
# be installed, which can be different to the one on which larchin is
# running.
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
# 2008.04.18

from subprocess import Popen, PIPE, STDOUT
import os, shutil, signal
import re
import crypt, random

from partition import Partition
from dialogs import PopupInfo, popupWarning, popupError

class installClass:
    def __init__(self, host=None):
        self.host = host

        self.processes = []
        assert (self.xcall("init") == ""), (
                "Couldn't initialize installation system")

        # Create a directory for temporary files
        shutil.rmtree("/tmp/larchin", True)
        os.mkdir("/tmp/larchin")

        # Allow possibility of offering 'frugal' installation (may never be
        # implemented as it should perhaps be handled completely separately).
        self.frugal = False

    def tidyup(self):
        for p in self.processes:
            os.kill(p.pid, signal.SIGKILL)
            p.wait()
        tu = self.xcall("tidyup")
        if tu:
            popupError(tu, _("Tidying up failed,"
                    " there may still be devices mounted"))
        shutil.rmtree("/tmp/larchin", True)

    def xsendfile(self, path, dest):
        """Copy the given file (path) to dest on the target.
        """
        if self.host:
            Popen("scp -q %s root@%s:%s" %
                    (path, self.host, dest), shell=True,
                    stdout=PIPE).communicate()[0]
        else:
            shutil.copyfile(path, dest)

    def xcall_local(self, cmd):
        """Call a function on the same machine.
        """
        xcmd = ("%s/syscalls/%s" % (basePath, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT)

    def xcall_net(self, cmd, opt=""):
        """Call a function on another machine.
        Public key authentication must be already set up so that no passsword
        is required.
        """
        xcmd = ("ssh %s root@%s /opt/larchin/syscalls/%s" %
                (opt, self.host, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT)

    def terminal(self, cmd):
        """Run a command in a terminal. The environment variable 'XTERM' is
        recognized, otherwise one will be chosen from a list.
        """
        term = os.environ.get("XTERM", "")
        if (os.system("which %s &>/dev/null" % term) != 0):
            for term in ("terminal", "konsole", "xterm", "rxvt", "urxvt"):
                if (os.system("which %s &>/dev/null" % term) != 0):
                    term = None
                else:
                    break

            assert term, "No terminal emulator found"
            if (term == "terminal"):
                term += " -x "
            else:
                term += " -e "

            process = Popen(term + cmd, shell=True)
            self.processes.append(process)
            while (process.poll() == None):
                mainWindow.eventloop(0.5)
            del(self.processes[-1])

    def xcall(self, cmd, opt="", callback=None):
        if self.host:
            process = self.xcall_net(cmd, opt)
        else:
            process = self.xcall_local(cmd)
        self.processes.append(process)

        while (process.poll() == None):
            if callback:
                callback()
            mainWindow.eventloop(0.5)

        op = process.stdout.read()
        del(self.processes[-1])
        if op.endswith("^OK^"):
            self.okop = op
            return ""
        else:
            return op

    def listDevices(self):
        """Return a list of device descriptions.
        Each device description is a list of strings:
            [device (/dev/sda, etc.),
             size (including unit),
             device type/name]
        """
        devices = []
        op = self.xcall("get-devices")
        for line in op.splitlines():
            devices.append(line.rstrip(';').split(':'))
        return devices

    def getmounts(self):
        return self.xcall("get-mounts")

    def setDevices(self, devs):
        """Set the self.devices list.
        """
        self.devices = devs

    def larchdev(self):
        """If the running system is larch, return the device from which
        it booted. Otherwise ''.
        """
        return self.xcall("larchbootdev").strip()

    def setDevice(self, device):
        """Set device selection for automatic partitioning.
        The value is the name of the drive ('/dev/sda', etc.).
        None is also a possibility ...
        """
        self.autodevice = device

    def selectedDevice(self):
        return self.autodevice or self.devices[0][0]

    def setPart(self, start):
        """Used by the autopartitioner to determine where the free space
        begins. The value can be:
                None       - manual partitioning
                0          - use whole drive
                1          - start after first partition
        """
        self.autoPartStart = start

    def getDeviceInfo(self, dev):
        # Info on drive and partitions (dev="/dev/sda", etc.):
        self.dinfo = self.xcall("get-partitions %s" % dev)
        # get the drive size in MB
        dsm = re.search(r"^/dev.*:([0-9\.]+)MB:.*;$", self.dinfo, re.M)
        self.dsize = int(dsm.group(1).split('.')[0])
        # get the info for the first partition, but only if it is NTFS
        p1m = re.search(r"^1:([0-9\.]+)MB:([0-9\.]+)MB:"
                "([0-9\.]+)MB:ntfs:.*;$", self.dinfo, re.M)
        if p1m:
            self.p1size = int(p1m.group(3).split('.')[0])
            self.p1start = int(p1m.group(1).split('.')[0])
            self.p1end = int(p1m.group(2).split('.')[0])
        else:
            self.p1size = 0
            self.p1start = 0
            self.p1end = 0
        # Also get the size of a cylinder, convert to MB
        c, m = self.xcall("get-cylsize %s" % dev).split()
        self.cylinders = int(c)
        self.cylinderMB = float(m) / 1000

    def getPartInfo(self, partno):
        """Get size and fstype for the given partition number using the
        data from the last call of getDeviceInfo.
        """
        rc = re.compile(r"^%d:([0-9\.]+)MB:([0-9\.]+)MB:"
                "([0-9\.]+)MB:([^:]*):.*;$" % partno)
        for l in self.dinfo.splitlines():
            rm = rc.search(l)
            if (rm and (rm.group(4) != 'free')):
                size = int(rm.group(3))
                fstype = rm.group(4)
                return (size, fstype)
        # This shouldn't happen
        assert False, "I wasn't expecting the Spanish Inquisition"

    def getNTFSinfo(self, part):
        """Return information about the given partition as a tuple:
                (cluster size (unit for resizing?),
                 current volume size,
                 current device size,
                 suggested resize point (minimum))
        All sizes are in bytes.
        When resizing, I suppose it makes sense to select a multiple of
        the cluster size - but this doesn't seem to be necessary. For
        other reasons - it seems to be standard - I have decided to make
        partitions start on (even?) cylinder boundaries.

        If the call fails for some reason, None is returned.
        """
        op = self.xcall("get-ntfsinfo %s" % part)
        rx = re.compile(r"^[^0-9]* ([0-9]+) ")
        lines = op.splitlines()
        try:
            self.ntfs_cluster_size = int(rx.search(lines[0]).group(1))
            cvs = int(rx.search(lines[0]).group(1))
            cds = int(rx.search(lines[0]).group(1))
            srp = int(rx.search(lines[0]).group(1))
        except:
            print "get-ntfsinfo failed"
            return None
        return (self.ntfs_cluster_size, cvs, cds, srp)

    def getNTFSmin(self, part):
        """Get the minimum size in MB for shrinking the given NTFS partition.
        """
        cs, cvs, cds, srp = self.getNTFSinfo(part)
        return srp / 1000000

    def doNTFSshrink(self, s):
        """Shrink selected NTFS partition. First the file-system is shrunk,
        then the partition containing it. The given size is in MB.
        """
        # This rounding to whole clusters may well not be necessary
        clus = int(s * 1e6) / self.ntfs_cluster_size
        newsize = clus * self.ntfs_cluster_size

        dev = self.selectedDevice()

        # First a test run
        info = PopupInfo(_("Test run ..."), _("Shrink NTFS partition"))
        res = self.xcall("ntfs-testrun %s1 %s" % (dev, newsize))
        info.drop()
        if res:
            return res

        # Now the real thing, resize the file-system
        info = PopupInfo(_("This is for real, shrinking file-system ..."),
                _("Shrink NTFS partition"))
        res = self.xcall("ntfs-resize %s1 %s" % (dev, newsize))
        info.drop()
        if res:
            return res

        # Now resize the actual partition

        # Get new start of following partition - even cylinder boundary,
        # doing quite a safe rounding up.
        newcyl = (int((newsize / 1e6) / self.cylinderMB + 2) / 2) * 2

        info = PopupInfo(_("Resizing partition ..."),
                _("Shrink NTFS partition"))
        res = self.xcall("part1-resize %s %d" % (dev, newcyl))
        info.drop()
        if res:
            return res

        # And finally expand the ntfs file-system into the new partition
        info = PopupInfo(_("Fitting file-system to new partition ..."),
                _("Shrink NTFS partition"))
        res = self.xcall("ntfs-growfit %s1" % dev)
        info.drop()
        self.getDeviceInfo(dev)
        return res

    def gparted_available(self):
        """Return '' if gparted is available.
        """
        return self.xcall("gparted-available", "-Y")

    def gparted(self):
        return self.xcall("gparted-run", "-Y")

    def cfdisk(self, dev):
        if self.host:
            cmd = "ssh -t root@%s cfdisk %s" % (self.host, dev)
        else:
            cmd = "cfdisk %s" % dev
        self.terminal(cmd)


    def rmparts(self, dev, partno):
        """Remove all partitions on the given device starting from the
        given partition number.
        """
        parts = self.xcall("listparts %s" % dev).splitlines()
        i = len(parts)
        while (i > 0):
            i -= 1
            p = int(parts[i])
            if (p >= partno):
                op = self.xcall("rmpart %s %d" % (dev, p))
                if op: return op
        return ""

    def mkpart(self, dev, startMB, endMB, ptype='ext2', pl='primary'):
        """Make a partition on the given device with the given start and
        end points. The default type is linux (called 'ext2' but no
        formatting is done). pl can be 'primary', 'extended' or 'logical'.
        """
        # Partitions are aligned to even cylinder boundaries
        startcyl = (int(startMB / self.cylinderMB + 1) / 2) * 2
        endcyl = (int(endMB / self.cylinderMB + 1) / 2) * 2
        if (endcyl > self.cylinders):
            endcyl = self.cylinders

        return self.xcall("newpart %s %d %d %s %s" % (dev,
                startcyl, endcyl, ptype, pl))

    def getlinuxparts(self, dev):
        """Return a list of partitions on the given device with linux
        partition code (83).
        """
        return self.xcall("linuxparts %s" % dev).split()

    def clearParts(self):
        """Keep a record of partitions which have been marked for use,
        initially empty.
        """
        self.parts = {}

    def newPartition(self, p, s="?", fpre=None, m=None, f=False, fnew=None,
            mo=None, fo=None):
        """Add a partition to the list of those marked for use.
        """
        pa = Partition(p, s, fpre, m, f, fnew, mo, fo)
        self.parts[p] = pa
        return pa

    def getPartition(self, part):
        return self.parts.get(part)

    def getActiveSwaps(self):
        """Discover active swap partitions. Return list
        of pairs: (device, size(GB)).
        """
        output = self.xcall("get-active-swaps")
        swaps = []
        for l in output.splitlines():
            ls = l.split()
            swaps.append((ls[0], float(ls[1]) * 1024 / 1e9))
        return swaps

    def getAllSwaps(self):
        """Discover swap partitions, whether active or not. Return list
        of pairs: (device, size(GB)).
        """
        # I might want to add support for LVM/RAID?
        output = self.xcall("get-all-swaps")
        swaps = []
        for l in output.splitlines():
            ls = l.split()
            swaps.append((ls[0], float(ls[1]) * 1024 / 1e9))
        return swaps

    def clearSwaps(self):
        self.swaps = []
        self.format_swaps = []

    def addSwap(self, p, format):
        # include in /etc/fstab
        self.swaps.append(p)
        if format:
            self.format_swaps.append(p)

    def swapFormat(self, p):
        return self.xcall("swap-format %s" % p)

    def partFormat(self, p):
        fo = p.format_options
        if (fo == None):
            fo = ""
        return self.xcall("part-format %s %s %s" % (p.partition,
                p.newformat, fo))

    def checkEmpty(self, mp):
        if self.xcall("check-mount %s" % mp):
            return popupWarning(_("The partition mounted at %s is not"
                    " empty. This could have bad consequences if you"
                    " attempt to install to it. Please reconsider.\n\n"
                    " Do you still want to install to it?") % mp)
        return True

    def guess_size(self, d='/'):
        """Get some estimate of the size of the given directory d, in MiB.
        """
        return int(self.xcall("guess-size %s" % d))

    def lsdir(self, d):
        """Get a list of items in the given directory ('ls').
        """
        return self.xcall("lsdir %s" % d).split()

    def copyover(self, dir, cb):
        self.xcall("copydir %s" % dir, callback=cb)

    def install_tidy(self):
        """Complete the copy part of the installation, creating missing
        items, etc.
        """
        self.xcall("larch-tidy")

    def get_size(self):
        """Get some estimate of the current size of the system being
        installed.
        Returns a value in MiB.
        """
        return int(self.xcall("installed-size"))

    def mount(self):
        """The order is important in some cases, so when building the list
        care must be taken that inner mounts (e.g. '/home') are placed
        after their containing mounts (e.g. '/') in the list.
        """
        self.mplist = []
        for p in self.parts.values():
            # Only mount partitions which will be formatted, which have
            # a mount-point and which are to be mounted at boot.
            if (p.mountpoint and p.format and ('A' not in p.mount_options)):
                i = 0
                for p0 in self.mplist:
                    if (p.mountpoint < p0[0]):
                        break
                    i += 1
                self.mplist.insert(i, (p.mountpoint, p.partition))
        return self.remount(True)

    def remount(self, check=False):
        """This mounts the partitions used by the new system using the
        list prepared by 'mount'.
        """
        for m, d in self.mplist:
            result = self.xcall("do-mount %s %s" % (d, m))
            if result:
                return None
            # Check that there are no files on this partition. The warning
            # can be ignored however.
            if check and not self.checkEmpty(m):
                return None
        return self.mplist

    def unmount(self):
        """To unmount the partitions mounted by the installer.
        """
        mlist = list(self.mplist)
        mlist.reverse()
        for m, d in mlist:
            # the 'list()' is needed because of the 'remove' below
            result = self.xcall("do-unmount %s" % m)
            if result:
                return False
        return True

    def mkinitcpio(self):
        self.xcall("do-mkinitcpio")

    def fstab(self):
        """Build a suitable /etc/fstab for the newly installed system.
        """
        fstab = ("# fstab generated by larchin\n"
                "#<file system>   <dir>       <type>      <options>"
                        "    <dump> <pass>\n")

        mainmounts = []
        mmounts = []
        xmounts = []
        # System partitions from self.parts
        for p in install.parts.values():
            if p.mountpoint:
                mainmounts.append(p.partition)
                opt = 'defaults'
                if (p.mountpoint == '/'):
                    pas = '1'
                else:
                    pas = '2'
                sysm = True
                if ('T' in p.mount_options):
                    opt += ',noatime'
                if ('D' in p.mount_options):
                    opt += ',nodiratime'
                if ('A' in p.mount_options):
                    opt += ',noauto'
                    pas = '0'
                    sysm = False

                s = "%-15s %-12s %-8s %s 0     %s\n" % (p.partition,
                        p.mountpoint, p.newformat or "auto", opt, pas)
                if sysm:
                    mmounts.append((p.mountpoint, s))
                else:
                    xmounts.append((p.mountpoint, s))

        mmounts.sort()
        for m, s in mmounts:
            fstab += s

        fstab += ("\nnone            /dev/pts    devpts      defaults"
                        "        0     0\n"
                "none            /dev/shm    tmpfs       defaults"
                        "        0     0\n\n")

        fstab += "# Swaps\n"
        for p in self.swaps:
            fstab += ("%-12s swap       swap   defaults        0     0\n"
                    % p)

        if xmounts:
            fstab += "#\n Other partitions\n"
            xmounts.sort()
            for m, s in xmounts:
                fstab += s

        fstab += "\n#Optical drives\n"
        for p in self.xcall("get-cd").splitlines():
            fstab += ("#/dev/%-6s /mnt/cd_%-4s auto"
                    "   user,noauto,exec,unhide 0     0\n" % (p, p))

        # Add other partitions to /mnt if not already catered for
        # One shouldn't assume the existing device info is up to date.
        dl = []
        for devi in self.xcall("get-usableparts").splitlines():
            devi = devi.split()
            dev = "/dev/" + devi[0]
            if (dev not in mainmounts):
                dl.append(devi)
        if dl:
            fstab += "\n#Additional partitions\n"
            for devi in dl:
                if (devi[1] == '+'):
                    # removable
                    rmv = '_'
                else:
                    rmv = ''
                fstype = devi[2].strip('"') or "auto"
                fstab += ("#/dev/%-7s /mnt/%-7s %s    user,noauto,noatime"
                        " 0     0\n" % (devi[0], devi[0]+rmv, fstype))

        dl = []
        for dev in self.xcall("get-lvm").splitlines():
            devm = "/dev/mapper/" + dev
            if (devm not in mainmounts):
                dl.append(dev)
        if dl:
            fstab += "\n#LVM partitions\n"
            for p in dl:
                fstab += ("#/dev/mapper/%-6s /mnt/lvm_%-4s auto"
                    "   user,noauto,noatime 0     0\n" % (p, p))

        fw = open("/tmp/larchin/fstab", "w")
        fw.write(fstab)
        fw.close()
        self.xsendfile("/tmp/larchin/fstab", "/tmp/install/etc/fstab")

    def set_devicemap(self):
        """Generate a (temporary) device.map file on the target and read
        its contents to a list of pairs in self.device_map.
        It also scans all partitions for menu.lst files, which are
        then stored as (device, path) pairs.
        """
        if self.remount():
            # Filter out new system '/' and '/boot'
            bar = []
            for p in self.parts.values():
                if (p.mountpoint == '/') or (p.mountpoint == '/boot'):
                    bar.append(p.partition)

            self.device_map = []
            self.menulst = []
            for line in self.xcall("mkdevicemap").splitlines():
                spl = line.split()
                if (spl[0].startswith('(')):
                    self.device_map.append(spl)
                elif (spl[0] == '+++'):
                    d = self.grubdevice(spl[2])
                    if d not in bar:
                        self.menulst.append((d, spl[1]))
            ok = self.unmount() and (self.device_map != [])
            return ok
        return False

    def grubdevice(self, device):
        """Convert from a grub drive name to a linux drive name, or vice
        versa. Uses the information previously gathered by set_devicemap().
        This works for drives and partitions in both directions.
        """
        if device.startswith('('):
            d = device.split(',')
            if (len(d) == 1):
                part = ''
            else:
                part = str(int(d[1].rstrip(')')) + 1)
                d = d[0] + ')'
            for a, b in self.device_map:
                if (a == d):
                    return (b + part)
        else:
            d  = device.rstrip('0123456789')
            if (d == device):
                part = ')'
            else:
                part = ',%d)' % (int(device[len(d):]) - 1)
            for a, b in self.device_map:
                if (b == d):
                    return a.replace(')', part)
        return None

    def getbootinfo(self):
        """Retrieves kernel file name and a list of initramfs files from
        the boot directory of the newly installed system.
        """
        self.remount()
        kernel = None
        inits = []
        for line in self.xcall("get-bootinfo").splitlines():
            if line.startswith('+++'):
                kernel = line.split()[1]
            else:
                inits.append(line)
        self.unmount()
        if not kernel:
            popupError(inits[0], _("GRUB problem"))
            return None
        if not inits:
            popupError(_("No initramfs found"), _("GRUB problem"))
            return None
        return (kernel, inits)

    def readmenulst(self, dev, path):
        return self.xcall("readmenulst %s %s" % (dev, path))

    def setup_grub(self, dev, path, text):
        fh = open("/tmp/larchin/menulst", "w")
        fh.write(text)
        fh.close()
        if dev:
            self.remount()
            self.xcall("grubinstall %s" % dev)
            self.xsendfile("/tmp/larchin/menulst",
                    "/tmp/install/boot/grub/menu.lst")
            self.unmount()

        else:
            # Just replace the appropriate menu.lst
            d, p = path.split(':')
            self.xcall("mount1 %s" % d)
            self.xsendfile("/tmp/larchin/menulst", "/tmp/mnt%s" % p)
            self.xcall("unmount1")


    def set_rootpw(self, pw):
        if (pw == ''):
            # Passwordless login
            pwcrypt = ''
        else:
            # Normal MD5 password
            salt = '$1$'
            for i in range(8):
                salt += random.choice("./0123456789abcdefghijklmnopqrstuvwxyz"
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            pwcrypt = crypt.crypt(pw, salt)

        self.remount()
        op = self.xcall("setpw root '%s'" % pwcrypt)
        self.unmount()
        if op:
            popupError(op, _("Couldn't set root password:"))
            return False
        return True
