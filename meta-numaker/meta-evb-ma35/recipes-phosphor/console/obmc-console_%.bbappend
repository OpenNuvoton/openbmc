# Enable Serial-Over-LAN (SOL) for NuMaker MA35 platforms.
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# NuMaker MA35 machines select "ssh-server-openssh" as the BMC's main login
# shell (see numaker-iot-ma35d05ki1.conf), and OE-core's dropbear package
# RCONFLICTS with openssh (they cannot both be installed in the same rootfs -
# do_rootfs fails with "package dropbear ... conflicts with openssh"). So the
# upstream port-2200/dropbear forwarding path is not usable here; drop the
# "ssh" PACKAGECONFIG for this machine.
PACKAGECONFIG:remove:numaker-iot-ma35d05ki1 = "ssh"

SRC_URI:append:numaker-iot-ma35d05ki1 = " file://server.ttyS4.conf "

# numaker-iot-ma35d05ki1 wires the host SOL link to uart4 (ttyS4, per its
# "port-number" property), enabled in ma35d05k-iot-ma35d05ki1-v1-256m.dts.
OBMC_CONSOLE_HOST_TTY:numaker-iot-ma35d05ki1 = "ttyS4"
OBMC_CONSOLE_TTYS:numaker-iot-ma35d05ki1 = "ttyS4"

do_install:append:numaker-iot-ma35d05ki1() {
    install -d ${D}${systemd_system_unitdir}/multi-user.target.wants
    ln -sf ../obmc-console@.service ${D}${systemd_system_unitdir}/multi-user.target.wants/obmc-console@ttyS4.service
}
