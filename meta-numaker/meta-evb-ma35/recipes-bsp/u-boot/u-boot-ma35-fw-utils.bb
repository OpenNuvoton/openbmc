SUMMARY = "U-Boot Environment Configuration for Nuvoton MA35"
DESCRIPTION = "Provides /etc/fw_env.config for U-Boot environment access based on storage architecture"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://fw_env_spinand.config \
    file://fw_env_mmc.config \
"

S = "${UNPACKDIR}"

RDEPENDS:${PN} = "libubootenv-bin"

do_install[depends] += "virtual/bootloader:do_deploy"

do_install() {
    install -d ${D}${sysconfdir}
    if [ "${MA35_STORAGE_TYPE}" = "mmc" ]; then
        install -m 0644 ${UNPACKDIR}/fw_env_mmc.config ${D}${sysconfdir}/fw_env.config
        if [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-sd" ]; then
            install -m 0644 "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-sd" ${D}${sysconfdir}/u-boot-initial-env
        elif [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-sd" ]; then
            install -m 0644 "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-sd" ${D}${sysconfdir}/u-boot-initial-env
        fi
    else
        install -m 0644 ${UNPACKDIR}/fw_env_spinand.config ${D}${sysconfdir}/fw_env.config
        if [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-spinand" ]; then
            install -m 0644 "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-spinand" ${D}${sysconfdir}/u-boot-initial-env
        elif [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-spinand" ]; then
            install -m 0644 "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-spinand" ${D}${sysconfdir}/u-boot-initial-env
        elif [ -f "${DEPLOY_DIR_IMAGE}/u-boot-initial-env" ]; then
            install -m 0644 "${DEPLOY_DIR_IMAGE}/u-boot-initial-env" ${D}${sysconfdir}/u-boot-initial-env
        fi
    fi

    # Fallback if initial-env file was not found in deploy directory
    if [ ! -f "${D}${sysconfdir}/u-boot-initial-env" ]; then
        cat <<'EOF' > ${D}${sysconfdir}/u-boot-initial-env
bootcmd=run distro_bootcmd
bootdelay=3
baudrate=115200
ethprime=eth0
bootfile=Image
kernel_addr_r=0x80080000
fdt_addr_r=0x85000000
loadaddr=0x81000000
scriptaddr=0x85010000
bootubipart=rootfs
bootubivol=rofs-a
kernelname=kernel-a
dtbname=dtb-a
bootlimit=3
bootcount=0
upgrade_available=0
altbootcmd=echo [FAILSAFE] Bootlimit exceeded! Switching active bank...; if test ${bootubivol} = rofs-b; then setenv bootubivol rofs-a; setenv kernelname kernel-a; setenv dtbname dtb-a; else setenv bootubivol rofs-b; setenv kernelname kernel-b; setenv dtbname dtb-b; fi; setenv upgrade_available 0; setenv bootcount 0; saveenv; if test ${mtdids} = 'nand0=nand0'; then run nandboot; else run spinandboot; fi;
kernelmem=256M swiotlb=1
mmc_block=mmcblk1p1
spinand_ubiblock=spinand-rootfs
nand_ubiblock=nand-rootfs
mtdids=spi-nand0=spi-nand0
nandboot=if test ${mtdids} = 'nand0=nand0' ; then if test -z "${bootubivol}"; then setenv bootubivol rofs-a; fi; if test -z "${kernelname}"; then setenv kernelname kernel-a; fi; if test -z "${dtbname}"; then setenv dtbname dtb-a; fi; if test -z "${bootubipart}"; then setenv bootubipart rootfs; fi; echo "Booting from nand (${kernelname}, ${dtbname}, ${bootubivol}) ..."; setenv bootargs noinitrd ubi.mtd=${nand_ubiblock} root=ubi0:${bootubivol} rootfstype=ubifs rw rootwait=1 console=ttyS0,115200n8 init=/sbin/init mem=${kernelmem}; if ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then echo "Booting kernel from UBI volume..."; elif ubi part ${bootubipart} && ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then echo "Booting kernel from UBI volume..."; else echo "UBI read kernel/dtb failed!"; fi; booti ${kernel_addr_r} - ${fdt_addr_r}; fi
spinandboot=if test ${mtdids} = 'spi-nand0=spi-nand0' ; then if test -z "${bootubivol}"; then setenv bootubivol rofs-a; fi; if test -z "${kernelname}"; then setenv kernelname kernel-a; fi; if test -z "${dtbname}"; then setenv dtbname dtb-a; fi; if test -z "${bootubipart}"; then setenv bootubipart rootfs; fi; echo "Booting from spinand (${kernelname}, ${dtbname}, ${bootubivol}) ..."; setenv bootargs noinitrd ubi.mtd=${spinand_ubiblock} root=ubi0:${bootubivol} rootfstype=ubifs rw rootwait=1 console=ttyS0,115200n8 init=/sbin/init mem=${kernelmem}; if ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then echo "Booting kernel from UBI volume..."; elif ubi part ${bootubipart} && ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then echo "Booting kernel from UBI volume..."; else echo "UBI read kernel/dtb failed!"; fi; booti ${kernel_addr_r} - ${fdt_addr_r}; fi
boot_targets=mmc0 mmc1 legacy_mmc0 mtd0 spinor0
bootcmd_mtd0=run spinandboot
distro_bootcmd=for target in ${boot_targets}; do run bootcmd_${target}; done
EOF
    fi
}

FILES:${PN} = "${sysconfdir}/fw_env.config ${sysconfdir}/u-boot-initial-env"
