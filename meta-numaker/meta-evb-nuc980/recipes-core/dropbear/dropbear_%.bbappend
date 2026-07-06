# NUC980: Override dropbearkey.service to skip RSA key generation
# (RSA keygen takes minutes on ARM926 ~300MHz, blocking SSH availability)
# Also override dropbear@.service to remove hardcoded RSA key path
FILESEXTRAPATHS:prepend:nuc980 := "${THISDIR}/${PN}:"

SRC_URI:append:nuc980 = " \
    file://dropbear@.service \
"

do_install:append:nuc980() {
    install -m 0644 ${UNPACKDIR}/dropbear@.service ${D}${systemd_system_unitdir}/dropbear@.service
}
