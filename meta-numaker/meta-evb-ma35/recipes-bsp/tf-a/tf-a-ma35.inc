# Common TF-A recipe logic for MA35 series
LICENSE = "BSD-3-Clause"
LIC_FILES_CHKSUM = "file://license.rst;md5=1dd070c98a281d18d9eefd938729b031"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = "git://github.com/OpenNuvoton/MA35D1_arm-trusted-firmware-v2.3.git;branch=master;protocol=https \
           file://0001-plat-nuvoton-override-por-from-sram-when-usb-boot.patch \
          "
SRC_URI += "file://${TFA_DDR_HEADER}"

SECTION = "bootloaders"
SRCREV = "${TFA_SRCREV}"
TFA_SRCREV ?= "${AUTOREV}"

PV = "${TF_VERSION}+git${SRCPV}"
TF_VERSION = "2.3"

PACKAGE_ARCH = "${MACHINE_ARCH}"

inherit deploy

PROVIDES += "virtual/trusted-firmware-a"
DEPENDS += "dtc-native"

# Let the Makefile handle setting up the CFLAGS and LDFLAGS as it
# is a standalone application
LDFLAGS[unexport] = "1"
CFLAGS[unexport] = "1"
LD[unexport] = "1"
AS[unexport] = "1"

PLATFORM = "${TFA_PLATFORM}"
export CROSS_COMPILE = "${TARGET_PREFIX}"
export ARCH = "arm64"

BOOT_TOOLS = ""

do_compile:prepend() {
    if echo ${TFA_DTB} | grep -q "custom"; then
        cp ${UNPACKDIR}/${TFA_DDR_HEADER} ${S}/plat/nuvoton/${PLATFORM}/include/custom_ddr.h
    fi
    python3 - "${S}" << 'EOF'
import glob, os, sys
s_dir = sys.argv[1]
target = """\t/* Set clock : initial clock 200KHz */
\t/* SDH_CLOCK_CONTROL */
\tsdh_set_clock(mmc, 200000);

\t/* reset SD bus */
\tcmd.cmdidx = MMC_CMD_GO_IDLE_STATE;
\tcmd.cmdarg = 0;
\tcmd.resp_type = MMC_RSP_NONE;
\tsdh_send_command(mmc, &cmd, 0);

\t/* timer delay */
\tudelay(0x1000);

\tmmc->rca = 0;
\t// initial SDHC
\t/* Test for SD version 2 */
\tcmd.cmdidx = SD_CMD_SEND_IF_COND;
\t/* We set the bit if the host supports voltages between 2.7 and 3.6 V */
\tcmd.cmdarg = 0x100 | 0xaa;
\tcmd.resp_type = MMC_RSP_R7;
\tsdh_send_command(mmc, &cmd, 0);"""

replacement = """\t/* Set clock : initial clock 200KHz */
\t/* SDH_CLOCK_CONTROL */
\tsdh_set_clock(mmc, 200000);
\tudelay(0x1000);

\tfor (int retry = 0; retry < 3; retry++) {
\t\t/* reset SD bus */
\t\tmemset(&cmd, 0, sizeof(cmd));
\t\tcmd.cmdidx = MMC_CMD_GO_IDLE_STATE;
\t\tcmd.cmdarg = 0;
\t\tcmd.resp_type = MMC_RSP_NONE;
\t\tsdh_send_command(mmc, &cmd, 0);
\t\tudelay(0x1000);
\t\tsdh_send_command(mmc, &cmd, 0);
\t\tudelay(0x1000);

\t\tmmc->rca = 0;
\t\t/* Test for SD version 2 */
\t\tmemset(&cmd, 0, sizeof(cmd));
\t\tcmd.cmdidx = SD_CMD_SEND_IF_COND;
\t\tcmd.cmdarg = 0x100 | 0xaa;
\t\tcmd.resp_type = MMC_RSP_R7;
\t\tsdh_send_command(mmc, &cmd, 0);
\t\tif ((cmd.response[0] & 0xff) == 0xaa)
\t\t\tbreak;
\t}"""

for path in glob.glob(os.path.join(s_dir, "drivers/nuvoton/sdhc/ma35*_sdhc.c")):
    with open(path, "r") as f:
        c = f.read()
    if target in c:
        with open(path, "w") as f:
            f.write(c.replace(target, replacement))
EOF
}

do_compile() {
    TFA_OPT="NEED_BL31=yes NEED_BL33=yes MA35D0_PMIC=${TFA_PMIC}"

    oe_runmake PLAT=${PLATFORM} ${TFA_OPT} -C ${S} realclean
    oe_runmake PLAT=${PLATFORM} ${TFA_OPT} LDFLAGS="--no-warn-rwx-segments" -C ${S} all
    oe_runmake PLAT=${PLATFORM} ${TFA_OPT} -C ${S} fiptool
}

do_deploy() {
    install -d ${DEPLOYDIR}
    install -Dm 0644 ${S}/build/${PLATFORM}/release/bl2.bin ${DEPLOYDIR}/bl2-${PLATFORM}.bin
    install -Dm 0644 ${S}/build/${PLATFORM}/release/fdts/${TFA_DTB}.dtb ${DEPLOYDIR}/bl2-${PLATFORM}.dtb
    install -Dm 0644 ${S}/build/${PLATFORM}/release/bl31.bin ${DEPLOYDIR}/bl31-${PLATFORM}.bin
    install -Dm 0755 ${S}/tools/fiptool/fiptool ${DEPLOYDIR}/fiptool
}

addtask deploy after do_compile
