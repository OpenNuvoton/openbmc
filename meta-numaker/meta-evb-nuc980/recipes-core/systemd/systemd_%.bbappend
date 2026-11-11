PACKAGECONFIG:remove:nuc980 = "coredump"

# Fix warning: "Group render has never been defined"
# meta-phosphor removes udev from USERADD_PACKAGES (USERADD_PACKAGES:remove = "udev"),
# which negates any USERADD_PACKAGES:append = " udev" and skips render group creation.
# Add the render group to ${PN} (systemd) instead so groupadd is executed.
GROUPADD_PARAM:${PN} += "-r render;"

# Fix warning: "${rootlibexecdir}/systemd/systemd does not exist"
# meta-phosphor uses ${rootlibexecdir} (/usr/libexec in merged-usr), but
# systemd installs its binary to ${systemd_unitdir}/systemd (/usr/lib/systemd/systemd).
ALTERNATIVE_TARGET[init] = "${systemd_unitdir}/systemd"
