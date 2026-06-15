# Stub services for NUC980 power control are DISABLED.
# x86-power-control (GPIO-based) is now the active backend.
# See conf/machine/numaker-iot-nuc980g2.conf for VIRTUAL-RUNTIME settings.
#
# To revert to stub mode (no physical host hardware):
#   1. Comment out VIRTUAL-RUNTIME lines in machine conf
#   2. Restore the do_install:append below
#
# FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"
# SRC_URI:append:numaker-iot-nuc980g2 = " \
#     file://phosphor-reset-chassis-running@.service \
#     file://obmc-power-start@.service \
#     file://obmc-power-stop@.service \
#     file://phosphor-wait-power-off@.service \
#     "
# FILES:${PN}:append:numaker-iot-nuc980g2 = " \
#     ${systemd_system_unitdir}/phosphor-wait-power-off@.service \
#     "
# do_install:append:numaker-iot-nuc980g2() {
#     install -m 0644 ${UNPACKDIR}/phosphor-reset-chassis-running@.service \
#         ${D}${systemd_system_unitdir}/phosphor-reset-chassis-running@.service
#     install -m 0644 ${UNPACKDIR}/obmc-power-start@.service \
#         ${D}${systemd_system_unitdir}/obmc-power-start@.service
#     install -m 0644 ${UNPACKDIR}/obmc-power-stop@.service \
#         ${D}${systemd_system_unitdir}/obmc-power-stop@.service
#     install -m 0644 ${UNPACKDIR}/phosphor-wait-power-off@.service \
#         ${D}${systemd_system_unitdir}/phosphor-wait-power-off@.service
# }
