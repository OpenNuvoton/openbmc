FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

AVOID_OVERLAYFS:nuc980 = "1"

VOLATILE_BINDS:append:nuc980 = "\n    /var/volatile/configuration /var/configuration\n    /var/volatile/ssh /etc/ssh\n    /var/volatile/ssl/certs /etc/ssl/certs\n    /var/volatile/nslcd /etc/nslcd\n"

do_install:append:nuc980() {
    install -d ${D}${sysconfdir}/ssl/certs
    install -d ${D}${sysconfdir}/nslcd
}


