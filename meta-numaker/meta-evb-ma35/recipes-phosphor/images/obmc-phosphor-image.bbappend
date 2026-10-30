# OpenBMC image customization for MA35 series
# Both MA35D0 and MA35D05K share the same trimming policy:
# 256MB RAM, 512MB SPI-NAND — no iKVM, no LDAP, no telemetry

# SquashFS with XZ compression for rootfs
EXTRA_IMAGECMD:squashfs-xz:append:ma35d0 = " -b 262144 -Xbcj arm"
EXTRA_IMAGECMD:squashfs-xz:append:ma35d05k = " -b 262144 -Xbcj arm"
EXTRA_IMAGECMD:squashfs-xz:append:ma35d1 = " -b 262144 -Xbcj arm"

# Trim EXT4 overhead, reserved blocks, and oversized default inode table
IMAGE_OVERHEAD_FACTOR:ma35 = "1.02"
EXTRA_IMAGECMD:ext4:ma35 = "-i 16384 -m 0"

IMAGE_FEATURES:remove:ma35d0 = " \
    obmc-ikvm \
    obmc-user-mgmt-ldap \
    obmc-telemetry \
"

IMAGE_FEATURES:remove:ma35d05k = " \
    obmc-ikvm \
    obmc-user-mgmt-ldap \
    obmc-telemetry \
"

IMAGE_FEATURES:remove:ma35d1 = " \
    obmc-ikvm \
    obmc-user-mgmt-ldap \
    obmc-telemetry \
"

IMAGE_INSTALL:remove:ma35d0 = "rest-dbus"
IMAGE_INSTALL:remove:ma35d05k = "rest-dbus"
IMAGE_INSTALL:remove:ma35d1 = "rest-dbus"

# phosphor-user-manager unconditionally adds new Redfish/D-Bus accounts to the
# "ipmi" supplementary group for privilege mapping. That group is normally
# created by phosphor-ipmi-host (GROUPADD_PARAM), but obmc-host-ipmi/
# obmc-net-ipmi are trimmed from this image, so the group never gets created.
# Without it, useradd fails ("group 'ipmi' does not exist", exit code 6) and
# Redfish AccountService POST/PATCH calls fail with HTTP 500. Create the
# group directly so account management keeps working without pulling in the
# full IPMI host stack.
EXTRA_USERS_PARAMS:append:ma35d0 = " groupadd ipmi;"
EXTRA_USERS_PARAMS:append:ma35d05k = " groupadd ipmi;"
EXTRA_USERS_PARAMS:append:ma35d1 = " groupadd ipmi;"

# Complete Dual-Bank UBI layout for MA35 SPI-NAND (supports 256MB and 512MB Flash):
# - Volume 0: u-boot-env (256KiB) for persistent U-Boot environment
# - Volume 1: kernel-a   (16MiB)  for Bank A Kernel
# - Volume 2: dtb-a      (512KiB) for Bank A Device Tree
# - Volume 3: rofs-a     (70MiB)  for Bank A RootFS
# - Volume 4: kernel-b   (16MiB)  for Bank B Kernel (pre-allocated for OTA)
# - Volume 5: dtb-b      (512KiB) for Bank B Device Tree (pre-allocated for OTA)
# - Volume 6: rofs-b     (70MiB)  for Bank B RootFS (pre-allocated for OTA)
# - Volume 7: rwfs       (10MiB, autoresize) for writable persistence & staging (~65MB on 256MB, ~315MB on 512MB)
do_image_ubi[depends] += "virtual/kernel:do_deploy virtual/bootloader:do_deploy u-boot-tools-native:do_populate_sysroot"
do_image_wic[depends] += "virtual/kernel:do_deploy virtual/bootloader:do_deploy virtual/trusted-firmware-a:do_deploy"
IMAGE_TYPEDEP:ubi = "ubifs"
IMAGE_CMD:ubi:ma35 () {
	ENV_IMAGE_LINE=""
	if [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-spinand" ]; then
		mkenvimage -s 0x10000 -o ${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}.bin ${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-spinand
		ENV_IMAGE_LINE="image=${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}.bin"
	elif [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-spinand" ]; then
		mkenvimage -s 0x10000 -o ${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}.bin ${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-spinand
		ENV_IMAGE_LINE="image=${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}.bin"
	elif [ -f "${DEPLOY_DIR_IMAGE}/u-boot-initial-env" ]; then
		mkenvimage -s 0x10000 -o ${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}.bin ${DEPLOY_DIR_IMAGE}/u-boot-initial-env
		ENV_IMAGE_LINE="image=${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}.bin"
	fi

	UBIFS_IMAGE="${IMGDEPLOYDIR}/${IMAGE_NAME}.ubifs"
	if [ ! -f "${UBIFS_IMAGE}" ] && [ -f "${IMGDEPLOYDIR}/${IMAGE_LINK_NAME}.ubifs" ]; then
		UBIFS_IMAGE="${IMGDEPLOYDIR}/${IMAGE_LINK_NAME}.ubifs"
	fi

	cat <<EOF > ${IMGDEPLOYDIR}/ubinize-${IMAGE_NAME}.cfg
[uboot-env]
mode=ubi
${ENV_IMAGE_LINE}
vol_id=0
vol_type=dynamic
vol_name=u-boot-env
vol_size=256KiB

[kernel-a]
mode=ubi
image=${DEPLOY_DIR_IMAGE}/Image
vol_id=1
vol_type=dynamic
vol_name=kernel-a
vol_size=16MiB

[dtb-a]
mode=ubi
image=${DEPLOY_DIR_IMAGE}/Image.dtb
vol_id=2
vol_type=dynamic
vol_name=dtb-a
vol_size=512KiB

[rofs-a]
mode=ubi
image=${UBIFS_IMAGE}
vol_id=3
vol_type=dynamic
vol_name=rofs-a
vol_size=70MiB

[kernel-b]
mode=ubi
vol_id=4
vol_type=dynamic
vol_name=kernel-b
vol_size=16MiB

[dtb-b]
mode=ubi
vol_id=5
vol_type=dynamic
vol_name=dtb-b
vol_size=512KiB

[rofs-b]
mode=ubi
vol_id=6
vol_type=dynamic
vol_name=rofs-b
vol_size=70MiB

[rwfs]
mode=ubi
vol_id=7
vol_type=dynamic
vol_name=rwfs
vol_size=10MiB
vol_flags=autoresize
EOF

	ubinize -o ${IMGDEPLOYDIR}/${IMAGE_NAME}.ubi ${UBINIZE_ARGS} ${IMGDEPLOYDIR}/ubinize-${IMAGE_NAME}.cfg
	ln -sf ${IMAGE_NAME}.ubi ${IMGDEPLOYDIR}/obmc-phosphor-image-${MACHINE}-spinand.ubi
	ln -sf ${IMAGE_NAME}.ubi ${IMGDEPLOYDIR}/obmc-phosphor-image-spinand.ubi

	# Generate Raw NAND UBI image if NAND U-Boot initial env exists
	ENV_IMAGE_NAND=""
	if [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-nand" ]; then
		mkenvimage -s 0x10000 -o ${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}-nand.bin ${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-${MACHINE}-nand
		ENV_IMAGE_NAND="image=${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}-nand.bin"
	elif [ -f "${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-nand" ]; then
		mkenvimage -s 0x10000 -o ${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}-nand.bin ${DEPLOY_DIR_IMAGE}/u-boot-ma35-initial-env-nand
		ENV_IMAGE_NAND="image=${IMGDEPLOYDIR}/u-boot-env-${IMAGE_NAME}-nand.bin"
	fi

	if [ -n "${ENV_IMAGE_NAND}" ]; then
		sed "s|${ENV_IMAGE_LINE}|${ENV_IMAGE_NAND}|" ${IMGDEPLOYDIR}/ubinize-${IMAGE_NAME}.cfg > ${IMGDEPLOYDIR}/ubinize-${IMAGE_NAME}-nand.cfg
		ubinize -o ${IMGDEPLOYDIR}/${IMAGE_NAME}-nand.ubi ${UBINIZE_ARGS} ${IMGDEPLOYDIR}/ubinize-${IMAGE_NAME}-nand.cfg
		ln -sf ${IMAGE_NAME}-nand.ubi ${IMGDEPLOYDIR}/obmc-phosphor-image-${MACHINE}-nand.ubi
		ln -sf ${IMAGE_NAME}-nand.ubi ${IMGDEPLOYDIR}/obmc-phosphor-image-nand.ubi
	fi
}


