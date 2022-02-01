#!/usr/bin/env python

__name__ = "rfkill"
__license__ = "GPLv3"
__version__ = "0.0.1"
__date__ = "June 2016"
__author__ = "Dale Patterson"
__maintainer__ = "Dale Patterson"
__email__ = "wraith.wireless@yandex.com"
__status__ = "Production"

import os
import struct
import fcntl
import pyric
import errno
import pyric.net.wireless.rfkill_h as rfkh
import sys

_PY3_ = sys.version_info.major == 3

RFKILL_STATE = [False, True]  # Unblocked = 0, Blocked = 1
dpath = "/dev/rfkill"
spath = "/sys/class/rfkill"
ipath = "/sys/class/ieee80211"  # directory of physical indexes


def rfkill_list():
    rfks = {}
    fin = open(dpath, "r")  # this will raise an IOError if rfkill is not supported
    flags = fcntl.fcntl(fin.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(fin.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
    while True:
        try:
            stream = fin.read(rfkh.RFKILLEVENTLEN)
            if _PY3_:
                # noinspection PyArgumentList
                stream = bytes(stream, "ascii")
                if len(stream) < rfkh.RFKILLEVENTLEN:
                    raise IOError("python 3")
            idx, t, op, s, h = struct.unpack(rfkh.rfk_rfkill_event, stream)
            # print(idx)
            files = os.listdir(spath)
            idx = [index for index, value in enumerate(files)]
            for idx in idx:
                if op == rfkh.RFKILL_OP_ADD:
                    rfks[getname(idx)] = {
                        "idx": idx,
                        "type": rfkh.RFKILL_TYPES[t],
                        "soft": RFKILL_STATE[s],
                        "hard": RFKILL_STATE[h],
                    }
        except IOError:
            break
    fin.close()
    return rfks


def rfkill_block(idx):
    """
    blocks the device at index
    :param idx: rkill index
    """
    if not os.path.exists(os.path.join(spath, "rfkill{0}".format(idx))):
        raise pyric.error(errno.ENODEV, "No device at {0}".format(idx))
    fout = None
    try:
        rfke = rfkh.rfkill_event(idx, rfkh.RFKILL_TYPE_ALL, rfkh.RFKILL_OP_CHANGE, 1, 0)
        if _PY3_:
            rfke = rfke.decode("ascii")
        fout = open(dpath, "wb")
        fout.write(rfke)
    except struct.error as e:
        raise pyric.error(pyric.EUNDEF, "Error packing rfkill event {0}".format(e))
    except IOError as e:
        raise pyric.error(e.errno, e.message)
    finally:
        if fout:
            fout.close()


def rfkill_blockby(rtype):
    """
    blocks the device of type
    :param rtype: rfkill type one of {'all'|'wlan'|'bluetooth'|'uwb'|'wimax'
     |'wwan'|'gps'|'fm'|'nfc'}
    """
    rfks = rfkill_list()
    for name in rfks:
        if rfks[name]["type"] == rtype:
            rfkill_block(rfks[name]["idx"])


def rfkill_unblock(idx):
    """
    unblocks the device at index
    :param idx: rkill index
    """
    if not os.path.exists(os.path.join(spath, "rfkill{0}".format(idx))):
        raise pyric.error(errno.ENODEV, "No device at {0}".format(idx))
    fout = None
    try:
        rfke = rfkh.rfkill_event(idx, rfkh.RFKILL_TYPE_ALL, rfkh.RFKILL_OP_CHANGE, 0, 0)
        rfke = b"rfke".decode()
        fout = open("dpath", "w")
        fout.write(rfke)
    except struct.error as e:
        raise pyric.error(pyric.EUNDEF, "Error packing rfkill event {0}".format(e))
    except IOError as e:
        raise pyric.error(e.errno, e.message)
    finally:
        if fout:
            fout.close()


def rfkill_unblockby(rtype):
    """
    unblocks the device of type
    :param rtype: rfkill type one of {'all'|'wlan'|'bluetooth'|'uwb'|'wimax'
     |'wwan'|'gps'|'fm'|'nfc'}
    """
    if rtype not in rfkh.RFKILL_TYPES:
        raise pyric.error(errno.EINVAL, "Type {0} is not valid".format(rtype))
    rfks = rfkill_list()
    for name in rfks:
        if rfks[name]["type"] == rtype:
            rfkill_unblock(rfks[name]["idx"])


def soft_blocked(idx):
    """
    determines soft block state of device
    :param idx: rkill index
    :returns: True if device at idx is soft blocked, False otherwise
    """
    # print(os.path.join(spath, "rfkill{0}".format(idx)))
    if not os.path.exists(os.path.join(spath, "rfkill{0}".format(idx))):
        raise pyric.error(errno.ENODEV, "No device at {0}".format(idx))
    fin = None
    try:
        fin = open(os.path.join(spath, "rfkill{0}".format(idx), "soft"), "r")
        return int(fin.read().strip()) == 1
    except IOError:
        raise pyric.error(errno.ENODEV, "No device at {0}".format(idx))
    except ValueError:
        raise pyric.error(pyric.EUNDEF, "Unexpected error")
    finally:
        if fin:
            fin.close()


def hard_blocked(idx):
    """
    determines hard block state of device
    :param idx: rkill index
    :returns: True if device at idx is hard blocked, False otherwise
    """
    if not os.path.exists(os.path.join(spath, "rfkill{0}".format(idx))):
        raise pyric.error(errno.ENODEV, "No device at {0}".format(idx))
    fin = None
    try:
        fin = open(os.path.join(spath, "rfkill{0}".format(idx), "hard"), "r")
        return int(fin.read().strip()) == 1
    except IOError:
        raise pyric.error(errno.ENODEV, "No device at {0}".format(idx))
    except ValueError:
        raise pyric.error(pyric.EUNDEF, "Unexpected error")
    finally:
        if fin:
            fin.close()


def getidx(phy):
    """
    returns the rfkill index associated with the physical index
    :param phy: phyiscal index
    :returns: the rfkill index
    """
    rfks = rfkill_list()
    try:
        return rfks["phy{0}".format(phy)]["idx"]
    except KeyError:
        return None


def getname(idx):
    """
    returns the phyical name of the device
    :param idx: rfkill index
    :returns: the name of the device
    """
    fin = None
    try:
        fin = open(os.path.join(spath, "rfkill{0}".format(idx), "name"), "r")
        return fin.read().strip()
    except IOError:
        raise pyric.error(errno.EINVAL, "No device at {0}".format(idx))
    finally:
        if fin:
            fin.close()


def gettype(idx):
    """
    returns the type of the device
    :param idx: rfkill index
    :returns: the type of the device
    """
    fin = None
    try:
        fin = open(os.path.join(spath, "rfkill{0}".format(idx), "type"), "r")
        return fin.read().strip()
    except IOError:
        raise pyric.error(errno.ENODEV, "No device at {0}".format(idx))
    finally:
        if fin:
            fin.close()
