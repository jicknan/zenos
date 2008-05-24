# doinstall.py - formatting and installation stage
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

class DoInstall(Stage):
    def stageTitle(self):
        return _("Perform Installation")

    def getHelp(self):
        return _("Here the chosen partitions will be formatted and mounted."
                " Then the running system will be copied onto them.\n\n"
                "This latter can take a while, so an estimate of progress (not"
                " terribly accurate) is shown.")

    def labelL(self):
        return ""

    def __init__(self):
        """
        """
        Stage.__init__(self)
        from doinstall_gui import Report, Progress
        self.output = Report()
        self.addWidget(self.output)

        self.progress = Progress()
        self.addWidget(self.progress, False)
        self.request_soon(self.run)

    def run(self):
        # need to disable forward button
        mainWindow.enable_forward(False)
        mainWindow.busy_on(False)

        self.ok = False
        if self.format():
            mountlist = install.mount()
            if mountlist:
                for m, p in mountlist:
                    self.output.report(_("Mounted partition %s at %s")
                            % (p, m))

                if (self.install() and install.unmount()):
                    self.output.report(_("Unmounted installation"
                            " partitions."))
                    self.output.report(_("\nInstallation completed"
                            " successfully."))
                    self.output.report(_("\nPress 'Forward' to continue"))
                    self.ok = True
                else:
                    self.output.report(_("\nInstallation failed"))
            else:
                self.output.report(_("Couldn't mount installation"
                        " partition(s)"))
        # need to reenable forward button
        mainWindow.busy_off(False)
        mainWindow.enable_forward(True)
        return self.stop_callback()

    def reinit(self):
        self.output.report(_("The installation has already been completed."
                " No further action is possible."))

    def format(self):


#        print "NOT FORMATTING"
#        return True

        # Swaps
        for p in install.format_swaps:
            self.output.report(_("Formatting partition %s as swap ...") % p)
            result = install.swapFormat(p)
            if result:
                self.output.report(result)
                return False

        # Installation partitions
        for p in install.parts.values():
            if p.format:
                self.output.report(_("Formatting partition %s as %s ...")
                        % (p.partition, p.newformat))
                result = install.partFormat(p)
                if result:
                    self.output.report(result)
                    return False
        return True

    def install(self):

#        print "NOT INSTALLING"
#        return True


        self.progress_count = 0
        self.progress_ratio = 1.0
        totalsize = 0
        self.output.report(_("Estimating installation size ..."))
        self.basesize = install.get_size()
        dlist = ["/bin", "/boot", "/etc", "/root", "/sbin", "/srv", "/lib",
                "/opt", "/home"]
        dlist += ["/usr/" + d for d in install.lsdir("/usr")]
        dlist.append("/var")

        self.system_size = 0
        partsizes = {}
        for d in dlist:
            gs = install.guess_size(d)
            partsizes[d] = gs
            self.system_size += gs

        self.output.report(_("Starting actual installation ...") + "\n---")
        self.progress.start()
        isize = self.basesize
        for d in dlist:
            #self.output.backline()
            self.output.report(_("--- Copying %s") % d)
            #print "cp", d, self.progress_ratio, totalsize, isize-self.basesize
            install.copyover(d, self.progress_cb)
            totalsize += partsizes[d]
            isize = install.get_size()
            self.progress_ratio = float(totalsize) / (isize - self.basesize)

        install.install_tidy()

        self.progress.ended()
        self.output.report(_("Copying of system completed."))
        self.output.report(_("Generating initramfs (this could take a while ...)"))
        install.mkinitcpio()
        if not install.frugal:
            self.output.report(_("Generating /etc/fstab"))
            install.fstab()
        return True

    def progress_cb(self):
        self.progress_count += 1
        if self.progress_count < 10:
            return
        self.progress_count = 0
        installed_size = install.get_size()
        frac = ((installed_size  - self.basesize) * self.progress_ratio
                / self.system_size)
        if (frac > 1.0):
            frac = 1.0
        self.progress.set(installed_size - self.basesize, frac)

    def forward(self):
        if self.ok:
            mainWindow.goto('grub')
        else:
            mainWindow.goto('error')


#################################################################

stages['install'] = DoInstall

