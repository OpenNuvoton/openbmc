/*
 * MA35D16FJ87C.h
 *
 * DDR configuration header for NuMaker-IoT-MA35D16FJ87C
 * MA35D16FJ87C - 512MB DDR3L, single chip select
 *
 * Parameters sourced from Nuvoton MA35D1 TF-A / Buildroot BSP
 * (MA35D16FJ87C_LQFP-216_MCP_WinbondDDR3L_512M_1PCS configuration)
 */
#ifndef __CUSTOM_DDR_H__
#define __CUSTOM_DDR_H__

#include <ma35d1_ddr.h>

struct nvt_ddr_init_param custom_ddr = {
        0x00000001,   // 0  DBG1
        0x00000001,   // 1  PWRCTL
        0x01040001,   // 2  MSTR
        0x0000d010,   // 3  MRCTRL0
        0x00000000,   // 4  MRCTRL1
        0x00000000,   // 5  PWRCTL
        0x00400010,   // 6  PWRTMG
        0x000a0003,   // 7  HWLPCTL
        0x00210000,   // 8  RFSHCTL0
        0x003c003c,   // 9  RFSHCTL1
        0x00000000,   // 10 RFSHCTL3
        0x00170047,   // 11 RFSHTMG
        0x00000000,   // 12 CRCPARCTL0
        0x40020083,   // 13 INIT0
        0x00350002,   // 14 INIT1
        0x19400040,   // 15 INIT3
        0x00480000,   // 16 INIT4
        0x00090000,   // 17 INIT5
        0x00000000,   // 18 DIMMCTL
        0x0000032f,   // 19 RANKCTL
        0x0a0d050b,   // 20 DRAMTMG0
        0x0003030f,   // 21 DRAMTMG1
        0x00000508,   // 22 DRAMTMG2
        0x00003007,   // 23 DRAMTMG3
        0x05030305,   // 24 DRAMTMG4
        0x04040303,   // 25 DRAMTMG5
        0x00000904,   // 26 DRAMTMG8
        0x80000033,   // 27 DRAMTMG15
        0x00810021,   // 28 ZQCTL0
        0x00000100,   // 29 ZQCTL1
        0x04020101,   // 30 DFITMG0
        0x00060101,   // 31 DFITMG1
        0x0700b030,   // 32 DFILPCFG0
        0x00400005,   // 33 DFIUPD0
        0x00170066,   // 34 DFIUPD1
        0x80000000,   // 35 DFIUPD2
        0x00000011,   // 36 DFIMISC
        0x00000000,   // 37 DFIPHYMSTR
        0x0000001f,   // 38 ADDRMAP0
        0x00080808,   // 39 ADDRMAP1
        0x00000000,   // 40 ADDRMAP2
        0x00000000,   // 41 ADDRMAP3
        0x00001f1f,   // 42 ADDRMAP4
        0x070f0707,   // 43 ADDRMAP5
        0x0f070707,   // 44 ADDRMAP6
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
        0x00000000,   // 56 DBG1
        0x00000000,   // 57 DBGCMD
        0x00000001,   // 58 SWCTL
        0x00000000,   // 59 SWCTLSTATIC
        0x00110011,   // 60 POISONCFG
        0x00000001,   // 61 PCTRL_0
        0x00000000,   // 62 PCTRL_1
        0x00000000,   // 63 PCTRL_2
        0x00000000,   // 64 PCTRL_3
        0x00000000,   // 65 PCTRL_4
        0x00000001,   // 66 PCTRL_5
        0x00000001,   // 67 PCTRL_6
        0x00000000,   // 68 PCCFG
        0x0001500f,   // 69 PCFGR_0
        0x0001500f,   // 70 PCFGR_1
        0x0001500f,   // 71 PCFGR_2
        0x0001500f,   // 72 PCFGR_3
        0x0001500f,   // 73 PCFGR_4
        0x0001500f,   // 74 PCFGR_5
        0x0001500f,   // 75 PCFGR_6
        0x0000500f,   // 76 PCFGW_0
        0x0000500f,   // 77 PCFGW_1
        0x0000500f,   // 78 PCFGW_2
        0x0000500f,   // 79 PCFGW_3
        0x0000500f,   // 80 PCFGW_4
        0x0000500f,   // 81 PCFGW_5
        0x0000500f,   // 82 PCFGW_6
        0x00000008,   // 83 SARBASE0
        0x00000001,   // 84 SARSIZE0

        // DDR PHY
        0xf004649f,   // 85 DSGCR
        0x0300c461,   // 86 PGCR1
        0x00f00483,   // 87 PGCR2
        0x0b405a03,   // 88 PTR0
        0x2328032b,   // 89 PTR1
        0x00083def,   // 90 PTR2
        0x09241105,   // 91 PTR3
        0x0801a069,   // 92 PTR4
        0x00001940,   // 93 MR0_DDR3
        0x00000040,   // 94 MR1_DDR3
        0x00000048,   // 95 MR2_DDR3
        0x00000000,   // 96 MR3_DDR3
        0x71559955,   // 97 DTPR0
        0x1a946325,   // 98 DTPR1
        0x30023a01,   // 99 DTPR2
        0x0000101b,   // 100 ZQ0CR1
        0x0000040b,   // 101 DCR
        0x91003587,   // 102 DTCR
        0x0001c000,   // 103 PLLCR
        0x0000f583,   // 104 PIR
        0x00000000,   // 105 SWCTL
        0x0000000b,   // 106 PWRCTL
        0x00000001,   // 107 SWCTL
};

#endif /* __CUSTOM_DDR_H__ */
