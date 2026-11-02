# Disable IPv6 and AAAA record publishing in avahi-daemon

do_install:append:ma35() {
    if [ -f ${D}${sysconfdir}/avahi/avahi-daemon.conf ]; then
        sed -i -e 's/^#*use-ipv6=.*/use-ipv6=no/' \
               -e 's/^#*publish-aaaa-on-ipv4=.*/publish-aaaa-on-ipv4=no/' \
               -e 's/^#*publish-a-on-ipv6=.*/publish-a-on-ipv6=no/' \
               ${D}${sysconfdir}/avahi/avahi-daemon.conf
    fi
}

