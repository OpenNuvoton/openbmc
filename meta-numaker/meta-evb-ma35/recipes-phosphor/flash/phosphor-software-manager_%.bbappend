FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI:append:ma35 = " \
    file://obmc-flash-bmc \
    file://ma35-verify-version.sh \
    file://obmc-boot-verify.sh \
    file://obmc-boot-verify.service \
    file://bind-images.conf \
    file://bind-images.sh \
    file://bind-images.service \
    file://obmc-flash-bmc-ubiro-timeout.conf \
    file://0001-ubi-sanitize-systemd-unit-instance-names.patch \
"

SYSTEMD_SERVICE:${PN}-updater:append:ma35 = " \
    obmc-boot-verify.service \
"

SYSTEMD_SERVICE:${PN}-version:append:ma35 = " \
    bind-images.service \
"

do_install:append:ma35() {
    install -d ${D}${bindir}
    install -m 0755 ${UNPACKDIR}/obmc-flash-bmc ${D}${bindir}/obmc-flash-bmc
    install -m 0755 ${UNPACKDIR}/ma35-verify-version.sh ${D}${bindir}/ma35-verify-version.sh
    install -m 0755 ${UNPACKDIR}/obmc-boot-verify.sh ${D}${bindir}/obmc-boot-verify.sh
    install -m 0755 ${UNPACKDIR}/bind-images.sh ${D}${bindir}/bind-images.sh

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${UNPACKDIR}/obmc-boot-verify.service ${D}${systemd_system_unitdir}/obmc-boot-verify.service
    install -m 0644 ${UNPACKDIR}/bind-images.service ${D}${systemd_system_unitdir}/bind-images.service

    install -d ${D}/images
    install -d ${D}${systemd_system_unitdir}/xyz.openbmc_project.Software.Manager.service.d
    install -m 0644 ${UNPACKDIR}/bind-images.conf ${D}${systemd_system_unitdir}/xyz.openbmc_project.Software.Manager.service.d/bind-images.conf

    install -d ${D}${systemd_system_unitdir}/obmc-flash-bmc-ubiro@.service.d
    install -m 0644 ${UNPACKDIR}/obmc-flash-bmc-ubiro-timeout.conf ${D}${systemd_system_unitdir}/obmc-flash-bmc-ubiro@.service.d/timeout.conf
}

FILES:${PN}-updater:append:ma35 = " \
    ${bindir}/ma35-verify-version.sh \
    ${bindir}/obmc-boot-verify.sh \
    ${systemd_system_unitdir}/obmc-boot-verify.service \
    ${systemd_system_unitdir}/obmc-flash-bmc-ubiro@.service.d/timeout.conf \
"

FILES:${PN}-version:append:ma35 = " \
    /images \
    ${bindir}/bind-images.sh \
    ${systemd_system_unitdir}/bind-images.service \
    ${systemd_system_unitdir}/xyz.openbmc_project.Software.Manager.service.d/bind-images.conf \
"

