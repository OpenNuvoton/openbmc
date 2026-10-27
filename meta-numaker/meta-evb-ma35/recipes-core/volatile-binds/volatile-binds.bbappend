FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

AVOID_OVERLAYFS:ma35 = "1"

VOLATILE_BINDS:append:ma35 = "\n    /var/volatile/configuration /var/configuration\n    /var/volatile/ssh /etc/ssh\n    /var/volatile/ssl/certs /etc/ssl/certs\n    /var/volatile/nslcd /etc/nslcd\n"

do_install:append:ma35() {
    install -d ${D}${sysconfdir}/ssl/certs
    install -d ${D}${sysconfdir}/nslcd
}
