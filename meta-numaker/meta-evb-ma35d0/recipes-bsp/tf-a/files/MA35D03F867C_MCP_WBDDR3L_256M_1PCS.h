/*
 * MA35D03F867C_MCP_WBDDR3L_256M_1PCS.h
 *
 * DDR configuration header for NuMaker-IoT-MA35D06F80
 * MA35D03F867C - 256MB WB DDR3L, single chip select
 *
 * Parameters sourced from Nuvoton MA35D0 TF-A BSP
 * (ma35d0_wb_ddr3_256mb configuration)
 */
#ifndef __CUSTOM_DDR_H__
#define __CUSTOM_DDR_H__

#include <ma35d0_ddr.h>

struct nvt_ddr_init_param custom_ddr = {
        0x00000001,   // 0  DBG1_1
        0x00000001,   // 1  PWRCTL_1
        0x01040001,   // 2  MSTR
        0x0000d010,   // 3  MRCTRL0
        0x00000000,   // 4  MRCTRL1
        0x00000000,   // 5  PWRCTL_2
        0x00400010,   // 6  PWRTMG
        0x000a0003,   // 7  HWLPCTL
        0x00210000,   // 8  RFSHCTL0
        0x003c003c,   // 9  RFSHCTL1
        0x00000000,   // 10 RFSHCTL3
        0x0010002b,   // 11 RFSHTMG
        0x00000000,   // 12 CRCPARCTL0
        0x40020083,   // 13 INIT0
        0x00350002,   // 14 INIT1
        0x1b400006,   // 15 INIT3
        0x00480000,   // 16 INIT4
        0x00090000,   // 17 INIT5
        0x00000000,   // 18 DIMMCTL
        0x0000032f,   // 19 RANKCTL
        0x090d040a,   // 20 DRAMTMG0
        0x0003020e,   // 21 DRAMTMG1
        0x00000408,   // 22 DRAMTMG2
        0x00003007,   // 23 DRAMTMG3
        0x04020205,   // 24 DRAMTMG4
        0x03030202,   // 25 DRAMTMG5
        0x00000a02,   // 26 DRAMTMG8
        0x80000032,   // 27 DRAMTMG15
        0x00800020,   // 28 ZQCTL0
        0x00000100,   // 29 ZQCTL1
        0x04020101,   // 30 DFITMG0
        0x00060101,   // 31 DFITMG1
        0x0700b030,   // 32 DFILPCFG0
        0x00400005,   // 33 DFIUPD0
        0x00170066,   // 34 DFIUPD1
        0x80000000,   // 35 DFIUPD2
        0x00000011,   // 36 DFIMISC
        0x00000000,   // 37 DFIPHYMSTR
        0x00000015,   // 38 ADDRMAP0
        0x00080808,   // 39 ADDRMAP1
        0x00000000,   // 40 ADDRMAP2
        0x00000000,   // 41 ADDRMAP3
        0x00001f1f,   // 42 ADDRMAP4
        0x070f0707,   // 43 ADDRMAP5
        0x0f0f0707,   // 44 ADDRMAP6
        0x07070707,   // 45 ADDRMAP9
        0x07070707,   // 46 ADDRMAP10
        0x00000007,   // 47 ADDRMAP11
        0x06000608,   // 48 ODTCFG
        0x00000101,   // 49 ODTMAP
        0x00f51f00,   // 50 SCHED
        0x00000000,   // 51 SCHED1
        0x0f000001,   // 52 PERFHPR1
        0x0f00007f,   // 53 PERFLPR1
        0x0f00007f,   // 54 PERFWR1
        0x00000000,   // 55 DBG0
        0x00000000,   // 56 DBG1_2
        0x00000000,   // 57 DBGCMD
        0x00000001,   // 58 SWCTL
        0x00000000,   // 59 SWCTLSTATIC
        0x00110011,   // 60 POISONCFG
        0x00000001,   // 61 PCTRL_0
        0x00000000,   // 62 PCTRL_1
        0x00000000,   // 63 PCTRL_2
        0x00000000,   // 64 PCTRL_3
        0x00000000,   // 65 PCTRL_4
        0x00000000,   // 66 PCTRL_5
        0x00000001,   // 67 PCCFG
        0x00000000,   // 68 reserved
        0x0001500f,   // 69 PCFGR_0
        0x0001500f,   // 70 PCFGW_0
        0x0001500f,   // 71 PCFGR_1
        0x0001500f,   // 72 PCFGW_1
        0x0001500f,   // 73 PCFGR_2
        0x0001500f,   // 74 PCFGW_2
        0x0000500f,   // 75 PCFGR_3
        0x0000500f,   // 76 PCFGW_3
        0x0000500f,   // 77 PCFGR_4
        0x0000500f,   // 78 PCFGW_4
        0x0000500f,   // 79 PCFGR_5
        0x0000500f,   // 80 PCFGW_5
        0x0000500f,   // 81 SARBASE0
        0x0000500f,   // 82 SARSIZE0
        0x00000008,   // 83 DFI_CTRL
        0x00000000,   // 84 reserved

        // DDR PHY
        0xf004649f,   // 85
        0x0300c461,   // 86
        0x00f0027f,   // 87
        0x0c806403,   // 88
        0x27100385,   // 89
        0x00083def,   // 90
        0x05b4111d,   // 91
        0x0801a072,   // 92
        0x00001b40,   // 93
        0x00000006,   // 94
        0x00000048,   // 95
        0x00000000,   // 96
        0x71568855,   // 97
        0x2282b32a,   // 98
        0x30023e00,   // 99
        0x0000105d,   // 100
        0x0000040b,   // 101
        0x91003587,   // 102
        0x0001c000,   // 103
        0x0000ff81,   // 104

        0x0000000b,   // 105
        0x00000000,   // 106
        0x00000001,   // 107
};

#endif /* __CUSTOM_DDR_H__ */
