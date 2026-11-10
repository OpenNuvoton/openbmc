# NOTE: This script is test under Python 3.x

__copyright__ = "Copyright (C) 2020~2021 Nuvoton Technology Corp. All rights reserved"

import sys
import usb.core
import usb.util
import json
import typing

XFER_LEN_CMD = 0x0012
GET_INFO_CMD = 0x0005


class XUsbCom:

    def __init__(self, _dev):
        self.dev = _dev
        self.write_addr = 0x1
        self.read_addr = 0x81
        self.attach = False
        self.id = 0
        self.info = b''
        
        self.bus = 0
        self.address = 0

    def write(self, data) -> None:
        try:
            # Vendor command set transfer length
            self.dev.ctrl_transfer(0x40, 0xA0, wValue=XFER_LEN_CMD, wIndex=len(data), data_or_wLength='')
            # Actual data
            self.dev.write(self.write_addr, data, timeout=1000)
        except usb.core.USBError as err:
            sys.exit(err)

    def read(self, size) -> bytes:
        try:
            buf = self.dev.read(self.read_addr, size, timeout=1000)
        except usb.core.USBError as err:
            sys.exit(err)
        return buf

    def set_media(self, media) -> None:
        try:
            # Vendor command set type
            self.dev.ctrl_transfer(0x40, 0xB0, wValue=media, wIndex=0, data_or_wLength='')
        except usb.core.USBError as err:
            sys.exit(err)
        return

    def get_info(self, data) -> bytes:
        try:
            self.dev.ctrl_transfer(0x40, 0xB0, wValue=GET_INFO_CMD, wIndex=0, data_or_wLength='')
            self.dev.ctrl_transfer(0x40, 0xA0, wValue=XFER_LEN_CMD, wIndex=84, data_or_wLength='')
            self.dev.write(0x01, data, timeout=1000)
            self.info = self.dev.read(0x81, 84, timeout=1000)
            # not used
            self.dev.read(0x81, 4, timeout=5000)

        except usb.core.USBError as err:
            sys.exit(err)
        return self.info

    def set_id(self, i) -> None:
        self.id = i

    def get_id(self) -> int:
        return self.id
        
    def set_bus(self, i) -> None:
        self.bus = i

    def get_bus(self) -> int:
        return self.bus
    
    def set_address(self, i) -> None:
        self.address = i

    def get_address(self) -> int:
        return self.address

    @staticmethod
    def set_align(nand, spinand, npage, nblock, nbcnt, noob, snpage, snblock, snbcnt, snoob, emmc_blk, sd_blk) -> None:
        # See if we need to overwrite existing json file.
        overwrite = False
        try:
            with open(".config", "r") as json_file:
                cfg = json.load(json_file)
            for key in cfg.keys():
                if key == 'nand_align':
                    if nand != int(cfg['nand_align']):
                        overwrite = True
                elif key == 'spinand_align':
                    if spinand != int(cfg['spinand_align']):
                        overwrite = True
                elif key == 'nand_page':
                    if npage != int(cfg['nand_page']):
                        overwrite = True
                elif key == 'nand_block':
                    if nblock != int(cfg['nand_block']):
                        overwrite = True
                elif key == 'nand_block_cnt':
                    if nbcnt != int(cfg['nand_block_cnt']):
                        overwrite = True
                elif key == 'nand_oob':
                    if noob != int(cfg['nand_oob']):
                        overwrite = True
                elif key == 'spinand_page':
                    if snpage != int(cfg['spinand_page']):
                        overwrite = True
                elif key == 'spinand_block':
                    if snblock != int(cfg['spinand_block']):
                        overwrite = True
                elif key == 'spinand_block_cnt':
                    if snbcnt != int(cfg['spinand_block_cnt']):
                        overwrite = True
                elif key == 'spinand_oob':
                    if snoob != int(cfg['spinand_oob']):
                        overwrite = True
                elif key == 'emmc_block':
                    if emmc_blk != int(cfg['emmc_block']):
                        overwrite = True
        except (IOError, OSError, json.decoder.JSONDecodeError) as err:
            overwrite = True

        if overwrite is True:
            try:
                with open(".config", "w+") as json_file:
                    new_key = {'nand_align': nand, 'spinand_align': spinand, \
                        'nand_page': npage, 'nand_block': nblock, 'nand_block_cnt': nbcnt, 'nand_oob': noob,\
                        'spinand_page': snpage, 'spinand_block': snblock, 'spinand_block_cnt': snbcnt,\
                        'spinand_oob': snoob, 'emmc_block': emmc_blk, 'sd_block': sd_blk}
                    json.dump(new_key, json_file, indent = 4)
            except (IOError, OSError) as err:
                print("Write .config failed. Please re-attach")
                sys.exit(err)

    @staticmethod
    def get_align() -> typing.Tuple[int, int, int, int, int, int, int, int, int, int, int]:
        try:
            with open(".config", "r") as json_file:
                cfg = json.load(json_file)
        except (IOError, OSError, json.decoder.JSONDecodeError) as err:
            print("Open/parsing .config failed. Please re-attach")
            sys.exit(err)
        nand_align = spinand_align = npage = nblock = nbcnt = noob = snpage = snblock = snbcnt = snoob = emmc_blk = sd_blk = 0
        for key in cfg.keys():
            if key == 'nand_align':
                nand_align = int(cfg['nand_align'])
            elif key == 'spinand_align':
                spinand_align = int(cfg['spinand_align'])
            elif key == 'nand_page':
                npage = int(cfg['nand_page'])
            elif key == 'nand_block':
                nblock = int(cfg['nand_block'])
            elif key == 'nand_block_cnt':
                nbcnt = int(cfg['nand_block_cnt'])
            elif key == 'nand_oob':
                noob = int(cfg['nand_oob'])
            elif key == 'spinand_page':
                snpage = int(cfg['spinand_page'])
            elif key == 'spinand_block':
                snblock = int(cfg['spinand_block'])
            elif key == 'spinand_block_cnt':
                snbcnt = int(cfg['spinand_block_cnt'])
            elif key == 'spinand_oob':
                snoob = int(cfg['spinand_oob'])
            elif key == 'emmc_block':
                emmc_blk = int(cfg['emmc_block'])
            elif key == 'sd_block':
                sd_blk = int(cfg['sd_block'])
        return nand_align, spinand_align, npage, nblock, nbcnt, noob, snpage, snblock, snbcnt, snoob, emmc_blk, sd_blk


class XUsbComList:

    def __init__(self, attach_all=False):
        vid = 0x0416
        pid = 0x5963
        try:
            self.devices = list(usb.core.find(idVendor=vid, idProduct=pid,
                                              find_all=True if attach_all is True else False))
        except TypeError:
            # list will raise exception if there's no device
            self.devices = []
            return
        except usb.core.NoBackendError as err:
            sys.exit(err)

        if len(self.devices) != 0 and attach_all is False:
            # Object type return on attach_all == False is different
            self.devices[0] = self.devices[0].device

        for dev in self.devices:
            try:
                dev.set_configuration()
            except (usb.core.USBError, NotImplementedError) as err:
                sys.exit(err)

        for i in range(0, len(self.devices)):
            dev = self.devices[i]
            bus = dev.bus
            address = dev.address
            self.devices[i] = XUsbCom(self.devices[i])
            self.devices[i].set_id(i)
            self.devices[i].set_bus(bus)
            self.devices[i].set_address(address)

    def __del__(self):
        if len(self.devices) != 0:
            for dev in self.devices:
                try:
                    usb.util.dispose_resources(dev.dev)
                    # dev.dev.reset()
                    dev = None
                #except (usb.core.USBError, NotImplementedError) as err:
                except usb.core.USBError as err:
                    sys.exit(err)

        self.devices = None

    def get_dev(self):
        return self.devices
