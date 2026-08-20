FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# Update webui-vue to include upstream fix for empty sensors page (commit bfad598fc)
SRCREV = "eab5bcd07420f30d4199c1f7a13eac44e15446a7"

SRC_URI:append = " \
    file://0002-add-realtime-dynamic-sensor-chart.patch \
"
