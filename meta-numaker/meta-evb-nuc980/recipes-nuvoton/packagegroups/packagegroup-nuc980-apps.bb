SUMMARY = "NUC980 Package Groups"
PR = "r1"

inherit packagegroup

PROVIDES = "${PACKAGES}"
PACKAGES = " \
    packagegroup-nuc980-apps \
"

RDEPENDS:packagegroup-nuc980-apps = " \
    avahi-daemon \
    bmcweb \
    entity-manager \
"
