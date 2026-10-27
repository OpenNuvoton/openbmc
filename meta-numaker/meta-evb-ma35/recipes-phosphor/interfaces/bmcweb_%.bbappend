FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI:append = " \
    file://0001-stream-large-request-payloads-to-disk.patch \
"

PACKAGECONFIG:append = " redfish-allow-deprecated-power-thermal"

EXTRA_OEMESON:append:ma35 = " \
    -Dhttp-body-limit=256 \
"
