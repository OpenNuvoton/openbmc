#!/bin/sh
#
# Mounts persistent/staging storage for firmware updates and sets up fw_env.config
# Supports both SPI-NAND (UBI) and eMMC/SD (EXT4 rwfs)
#
mount -o remount,rw / 2>/dev/null || true
mkdir -p /images /tmp/images /var/persist

if [ -e /dev/ubi0 ] && ubinfo /dev/ubi0 -N rwfs >/dev/null 2>&1; then
    mount -t ubifs ubi0:rwfs /images 2>/dev/null || true
else
    RWFS_DEV=$(blkid 2>/dev/null | grep 'LABEL="rwfs"' | cut -d':' -f1 || true)
    if [ -n "${RWFS_DEV}" ] && [ -b "${RWFS_DEV}" ]; then
        mount -t ext4 "${RWFS_DEV}" /images 2>/dev/null || true
    fi
fi

mkdir -p /images/staging /images/persist
rm -rf /images/staging/* 2>/dev/null || true

if ! mountpoint -q /tmp/images; then
    mount --bind /images/staging /tmp/images 2>/dev/null || mount --bind /images /tmp/images
fi

if ! mountpoint -q /var/persist; then
    mount --bind /images/persist /var/persist
fi

mount -o remount,rw /tmp/images 2>/dev/null || true
mount -o remount,rw /var/persist 2>/dev/null || true

# Auto-configure /etc/fw_env.config for active MMC device
ROOT_DEV=$(findmnt -n -o SOURCE / 2>/dev/null || grep -o 'root=[^ ]*' /proc/cmdline | cut -d'=' -f2)
MMC_BASE=$(echo "${ROOT_DEV}" | grep -o 'mmcblk[0-9]' || true)
if [ -n "${MMC_BASE}" ]; then
    if [ ! -f /etc/fw_env.config ] || grep -q 'ubi' /etc/fw_env.config 2>/dev/null; then
        echo "/dev/${MMC_BASE} 0x50000 0x10000" > /etc/fw_env.config
    elif [ ! -e /dev/mmcblk0 ] && [ -e "/dev/${MMC_BASE}" ]; then
        sed -i "s|/dev/mmcblk0|/dev/${MMC_BASE}|g" /etc/fw_env.config
    fi

    # Ensure mmcboot uses correct rofspart (p5 for Bank B, p3 for Bank A) in MBR layout
    CURRENT_MMCBOOT=$(fw_printenv mmcboot 2>/dev/null | cut -d'=' -f2- || true)
    if echo "${CURRENT_MMCBOOT}" | grep -q 'rofspart 4'; then
        NEW_MMCBOOT=$(echo "${CURRENT_MMCBOOT}" | sed 's/if test -e mmc \${mmcdev}:5 \/; then setenv rofspart 5; else setenv rofspart 4; fi;/setenv rofspart 5;/g; s/setenv rofspart 4;/setenv rofspart 5;/g')
        fw_setenv mmcboot "${NEW_MMCBOOT}" 2>/dev/null || true
    fi
fi

