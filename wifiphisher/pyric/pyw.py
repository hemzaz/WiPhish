#!/usr/bin/env python
import os
import re
import socket
import struct
from dataclasses import dataclass
from errno import (
    EADDRNOTAVAIL,
    EAFNOSUPPORT,
    EBUSY,
    EINVAL,
    ENODEV,
    ENOENT,
    ENONET,
    ENOTDIR,
    ENOTUNIQ,
    EPROTONOSUPPORT,
)
from os import strerror
from typing import Any, Dict, List, Optional, Tuple, Union

from .lib.libio import io_socket_free, io_transfer, io_socket_alloc
from .lib.libnl import (
    NLSocket,
    nl_recvmsg,
    nl_sendmsg,
    nl_socket_alloc,
    nl_socket_free,
    nla_find,
    nla_parse_nested,
    nla_put_string,
    nla_put_u8,
    nla_put_u32,
    nla_put_unspec,
    nlmsg_new,
)
from .net.genetlink_h import (
    CTRL_ATTR_FAMILY_ID,
    CTRL_ATTR_FAMILY_NAME,
    CTRL_CMD_GETFAMILY,
    GENL_ID_CTRL,
)
from .net.if_h import (
    AF_INET,
    AF_UNSPEC,
    ARPHRD_ETHER,
    ARPHRD_IEEE80211_RADIOTAP,
    IFF_UP,
    IFNAMELEN,
    ifr_flags,
    ifr_ifindex,
    ifr_iwtxpwr,
    ifreq,
    sa_addr,
)
from .net.netlink_h import (
    NLA_ERROR,
    NLE_SUCCESS,
    NLM_F_ACK,
    NLM_F_MATCH,
    NLM_F_REQUEST,
    NLM_F_ROOT,
)
from .net.sockios_h import (
    SIOCGIFADDR,
    SIOCGIFBRDADDR,
    SIOCGIFFLAGS,
    SIOCGIFHWADDR,
    SIOCGIFINDEX,
    SIOCGIFNETMASK,
    SIOCGIWNAME,
    SIOCGIWTXPOW,
    SIOCSIFADDR,
    SIOCSIFBRDADDR,
    SIOCSIFFLAGS,
    SIOCSIFHWADDR,
    SIOCSIFNETMASK,
)
from .net.wireless.nl80211_h import (
    NL80211_ATTR_BSS,
    NL80211_ATTR_CENTER_FREQ1,
    NL80211_ATTR_CHANNEL_WIDTH,
    NL80211_ATTR_CIPHER_SUITES,
    NL80211_ATTR_GENERATION,
    NL80211_ATTR_IFINDEX,
    NL80211_ATTR_IFNAME,
    NL80211_ATTR_IFTYPE,
    NL80211_ATTR_MAC,
    NL80211_ATTR_MAX_NUM_SCAN_SSIDS,
    NL80211_ATTR_MNTR_FLAGS,
    NL80211_ATTR_PS_STATE,
    NL80211_ATTR_REG_ALPHA2,
    NL80211_ATTR_SOFTWARE_IFTYPES,
    NL80211_ATTR_SSID,
    NL80211_ATTR_STA_INFO,
    NL80211_ATTR_SUPPORTED_COMMANDS,
    NL80211_ATTR_SUPPORTED_IFTYPES,
    NL80211_ATTR_WDEV,
    NL80211_ATTR_WIPHY,
    NL80211_ATTR_WIPHY_BANDS,
    NL80211_ATTR_WIPHY_CHANNEL_TYPE,
    NL80211_ATTR_WIPHY_COVERAGE_CLASS,
    NL80211_ATTR_WIPHY_FRAG_THRESHOLD,
    NL80211_ATTR_WIPHY_FREQ,
    NL80211_ATTR_WIPHY_RETRY_LONG,
    NL80211_ATTR_WIPHY_RETRY_SHORT,
    NL80211_ATTR_WIPHY_RTS_THRESHOLD,
    NL80211_ATTR_WIPHY_TX_POWER_LEVEL,
    NL80211_ATTR_WIPHY_TX_POWER_SETTING,
    NL80211_BAND_ATTR_FREQS,
    NL80211_BAND_ATTR_HT_AMPDU_DENSITY,
    NL80211_BAND_ATTR_HT_AMPDU_FACTOR,
    NL80211_BAND_ATTR_HT_CAPA,
    NL80211_BAND_ATTR_HT_MCS_SET,
    NL80211_BAND_ATTR_RATES,
    NL80211_BAND_ATTR_VHT_CAPA,
    NL80211_BAND_ATTR_VHT_MCS_SET,
    NL80211_BANDS,
    NL80211_BITRATE_ATTR_RATE,
    NL80211_BSS_BEACON_INTERVAL,
    NL80211_BSS_BSSID,
    NL80211_BSS_CHAN_WIDTH,
    NL80211_BSS_CHAN_WIDTHS,
    NL80211_BSS_FREQUENCY,
    NL80211_BSS_INFORMATION_ELEMENTS,
    NL80211_BSS_SIGNAL_MBM,
    NL80211_BSS_STATUS,
    NL80211_BSS_STATUSES,
    NL80211_CMD_CONNECT,
    NL80211_CMD_DEL_INTERFACE,
    NL80211_CMD_DISCONNECT,
    NL80211_CMD_GET_INTERFACE,
    NL80211_CMD_GET_POWER_SAVE,
    NL80211_CMD_GET_REG,
    NL80211_CMD_GET_SCAN,
    NL80211_CMD_GET_STATION,
    NL80211_CMD_NEW_INTERFACE,
    NL80211_CMD_REQ_SET_REG,
    NL80211_CMD_SET_CHANNEL,
    NL80211_CMD_SET_INTERFACE,
    NL80211_CMD_SET_POWER_SAVE,
    NL80211_CMD_SET_WIPHY,
    NL80211_FREQUENCY_ATTR_DISABLED,
    NL80211_FREQUENCY_ATTR_FREQ,
    NL80211_FREQUENCY_ATTR_INDOOR_ONLY,
    NL80211_FREQUENCY_ATTR_MAX_TX_POWER,
    NL80211_FREQUENCY_ATTR_NO_10MHZ,
    NL80211_FREQUENCY_ATTR_NO_20MHZ,
    NL80211_FREQUENCY_ATTR_NO_80MHZ,
    NL80211_FREQUENCY_ATTR_NO_160MHZ,
    NL80211_FREQUENCY_ATTR_NO_HT40_MINUS,
    NL80211_FREQUENCY_ATTR_NO_HT40_PLUS,
    NL80211_GENL_NAME,
    NL80211_IFTYPES,
    NL80211_MNTR_FLAGS,
    NL80211_RATE_INFO_40_MHZ_WIDTH,
    NL80211_RATE_INFO_BITRATE,
    NL80211_RATE_INFO_BITRATE32,
    NL80211_RATE_INFO_MCS,
    NL80211_RATE_INFO_SHORT_GI,
    NL80211_STA_INFO_RX_BITRATE,
    NL80211_STA_INFO_RX_BYTES,
    NL80211_STA_INFO_RX_PACKETS,
    NL80211_STA_INFO_TX_BITRATE,
    NL80211_STA_INFO_TX_BYTES,
    NL80211_STA_INFO_TX_FAILED,
    NL80211_STA_INFO_TX_PACKETS,
    NL80211_STA_INFO_TX_RETRIES,
    NL80211_TX_POWER_AUTOMATIC,
    NL80211_TX_POWER_SETTINGS,
    NL80211_CMD_GET_WIPHY,
)
from .net.wireless.wlan import (
    COV_CLASS_MAX,
    COV_CLASS_MIN,
    FRAG_THRESH_MAX,
    FRAG_THRESH_MIN,
    FRAG_THRESH_OFF,
    RETRY_MAX,
    RETRY_MIN,
    RTS_THRESH_MAX,
    RTS_THRESH_MIN,
    RTS_THRESH_OFF,
    WLAN_CIPHER_SUITE_SELECTORS,
)
from .nlhelp.nlsearch import cmdbynum
from .utils.channels import CHTYPES, ch2rf, channels, freqs, rf2ch
from .utils.hardware import dpath, ifcard, manufacturer
from .utils.ouifetch import load
from .utils.rfkill import *

EUNDEF = -1  # undefined error
_FAM80211ID_ = None

# redefine some nl80211 enum lists for ease of use
IFTYPES = NL80211_IFTYPES
MNTRFLAGS = NL80211_MNTR_FLAGS
TXPWRSETTINGS = NL80211_TX_POWER_SETTINGS

################################################################################
#### WIRELESS CORE                                                          ####
################################################################################


def interfaces() -> List[str]:
    """Return all connected network interfaces.

    Find all the connected interfaces by parsing the /proc/net/dev file.

    :returns: a list of all the connected interfaces.
    :raises OSError: when the file is not found.
    """
    all_interfaces: List[str] = []

    with open(dpath) as dev_file:
        for line in dev_file:
            # the file format is an interface_name followed by a colon
            colon = line.find(":")
            wl = line.find("wl")
            if colon > 0 and wl > 0:
                # left strip is needed because some of the interface names
                # are not always at the start of the line
                interface = line[:colon].lstrip()
                all_interfaces.append(interface)

    return all_interfaces


def isinterface(dev: str) -> bool:
    """Return whether device is a network card.

    Find if dev is in the /proc/net/dev file which is the list of
    connected interfaces.

    :raises OSError: when the file is not found.
    """
    with open(dpath) as dev_file:
        for line in dev_file:
            if dev in line:
                return True
        return False


def winterfaces(iosock: Optional[socket.socket] = None) -> List[str]:
    """Return all wireless interfaces."""
    if iosock is None:
        return _iostub_(winterfaces)

    wifaces = []
    for dev in interfaces():
        if iswireless(dev, iosock):
            wifaces.append(dev)
    return wifaces


def iswireless(dev: str, iosock: Optional[socket.socket] = None) -> bool:
    """Return whether device is wireless or not."""
    if iosock is None:
        return _iostub_(iswireless, dev)

    try:
        # if the call succeeds, dev is found to be wireless
        _ = io_transfer(iosock, SIOCGIWNAME, ifreq(dev))
        return True
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except EnvironmentError:
        return False


def phylist() -> List[Tuple[int, str]]:
    """Retrun all phys of wireless devices using rfkill.

    :returns: a list of tuples t(physical index, physical name)
    """
    # these are stroed in /sys/class/ieee80211 but we let rfkill do it (just in
    # case the above path differs across distros or in future upgrades). However,
    # in some cases like OpenWRT which does not support rfkill we have to walk the
    # directory
    phys = []
    try:
        rfdevs = rfkill_list()
        for rfk in rfdevs:
            if rfdevs[rfk]["type"] == "wlan":
                phys.append((int(rfk.split("phy")[1]), rfk))
    except IOError as e:
        # catch 'No such file or directory' errors when rfkill is not supported
        if e.errno == ENOENT:
            try:
                rfdevs = os.listdir(ipath)
            except OSError:
                emsg = "{} is not a directory & rfkill is not supported".format(ipath)
                raise EnvironmentError(ENOTDIR, emsg)
            else:
                for rfk in rfdevs:
                    phys.append((int(rfk.split("phy")[1]), rfk))
        else:
            raise EnvironmentError(
                EUNDEF, f"PHY listing failed: {e.errno}-{e.strerror}"
            )
    return phys


def regget(nlsock: Optional[NLSocket] = None) -> str:
    """Return the current regulatory domain.

    :returns: the two charactor regulatory domain.
    """
    if nlsock is None:
        return _nlstub_(regget)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_GET_REG,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)
    return nla_find(rmsg, NL80211_ATTR_REG_ALPHA2)


def regset(rd: str, nlsock: Optional[NLSocket] = None):
    """Set the current regulatory domain.

    :param rd: regulatory domain code
    :param nlsock: netlink socket
    .. warning:: Requires root privileges
    """
    if len(rd) != 2:
        raise EnvironmentError(EINVAL, "Invalid reg. domain")
    if nlsock is None:
        return _nlstub_(regset, rd)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_REQ_SET_REG,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_string(msg, rd.upper(), NL80211_ATTR_REG_ALPHA2)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


################################################################################
#### CARD RELATED ####
################################################################################


@dataclass(frozen=True)
class Card:
    """A wireless network interface controller.

    Exposes the following properties: (callable by '.'):
        phy: physical index
        dev: device name
        idx: interface index (ifindex)
    """

    phy: int
    dev: str
    idx: int


def getcard(dev: str, nlsock: Optional[NLSocket] = None) -> Card:
    """Return the Card object using device name."""
    # print(type(dev))
    if nlsock is None:
        return _nlstub_(getcard, dev)
    return devinfo(dev, nlsock)["card"]


def validcard(card: Card, nlsock: Optional[NLSocket] = None) -> bool:
    """Return the card validity."""
    if nlsock is None:
        return _nlstub_(validcard, card)

    try:
        return card == devinfo(card.dev, nlsock)["card"]
    except EnvironmentError as e:
        if e.errno == ENODEV:
            return False
        else:
            raise


################################################################################
#### ADDRESS RELATED                                                        ####
################################################################################


def macget(card: Card, iosock: Optional[socket.socket] = None) -> str:
    """Return the interface's hw address."""
    if iosock is None:
        return _iostub_(macget, card)

    try:
        flag = SIOCGIFHWADDR
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam in [ARPHRD_ETHER, AF_UNSPEC, ARPHRD_IEEE80211_RADIOTAP]:
            return _hex2mac_(ret[18:24])
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return hwaddr family")
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def macset(card: Card, mac: str, iosock: Optional[socket.socket] = None) -> bool:
    """Set nic's hwaddr.

    .. warning:: Requires root privileges
    """
    if not _validmac_(mac):
        raise EnvironmentError(EINVAL, "Invalid mac address")
    if iosock is None:
        return _iostub_(macset, card, mac)

    try:
        flag = SIOCSIFHWADDR
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag, [mac]))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam in [ARPHRD_ETHER, AF_UNSPEC, ARPHRD_IEEE80211_RADIOTAP]:
            return _hex2mac_(ret[18:24]) == mac
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return hwaddr family")
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def ifaddrget(
    card: Card, iosock: Optional[socket.socket] = None
) -> Tuple[Any, Any, Any]:
    """Return nic's ip, netmask and broadcast addresses

    :returns: the tuple t = (inet,mask,bcast)
    """
    if iosock is None:
        return _iostub_(ifaddrget, card)

    try:
        # ip
        flag = SIOCGIFADDR
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam == AF_INET:
            inet = _hex2ip4_(ret[20:24])
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return ip family")

        # netmask
        flag = SIOCGIFNETMASK
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam == AF_INET:
            mask = _hex2ip4_(ret[20:24])
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return netmask family")

        # broadcast
        flag = SIOCGIFBRDADDR
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam == AF_INET:
            bcast = _hex2ip4_(ret[20:24])
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return broadcast family")
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        # catch address not available, which means the card currently does not
        # have any addresses set - raise others
        if e.errno == EADDRNOTAVAIL:
            return None, None, None
        raise EnvironmentError(e.errno, e.strerror)

    return inet, mask, bcast


def ifaddrset(
    card: Card,
    inet: Optional[str] = None,
    mask: Optional[str] = None,
    bcast: Optional[str] = None,
    iosock: Optional[socket.socket] = None,
) -> bool:
    """Set nic's ip4 addr, netmask and/or broadcast.

    It can set ipaddr,netmask and/or broadcast to None but one or more of ipaddr,
    netmask, broadcast must be set

    .. note:
        1) throws error if setting netmask or broadcast and card does not have
            an ip assigned
        2) if setting only the ip address, netmask and broadcast will be set
            accordingly by the kernel.
        3) If setting multiple or setting the netmask and/or broadcast after the ip
            is assigned, one can set them to erroneous values i.e. ip = 192.168.1.2
            and broadcast = 10.0.0.31.
    .. warning:: Requires root privileges
    """
    # ensure one of params is set & that all set params are valid ip address
    if not inet and not mask and not bcast:
        raise EnvironmentError(EINVAL, "No parameters specified")
    if inet and not _validip4_(inet):
        raise EnvironmentError(EINVAL, "Invalid IP address")
    if mask and not _validip4_(mask):
        raise EnvironmentError(EINVAL, "Invalid netmask")
    if bcast and not _validip4_(bcast):
        raise EnvironmentError(EINVAL, "Invalid broadcast")
    if iosock is None:
        return _iostub_(ifaddrset, card, inet, mask, bcast)

    try:
        success = True
        # we have to do one at a time
        if inet:
            success &= inetset(card, inet, iosock)
        if mask:
            success &= maskset(card, mask, iosock)
        if bcast:
            success &= bcastset(card, bcast, iosock)
        return success
    except EnvironmentError as e:
        # an ambiguous error is thrown if attempting to set netmask or broadcast
        # without an ip address already set on the card
        if e.errno == EADDRNOTAVAIL and inet is None:
            raise EnvironmentError(EINVAL, "Set ip4 addr first")
        else:
            raise
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")


def inetset(card: Card, inet, iosock: Optional[socket.socket] = None) -> bool:
    """Set nic's ip4 addrress.

    .. note: setting the ip will set netmask and broadcast accordingly
    .. warning:: Requires root privileges
    """
    if not _validip4_(inet):
        raise EnvironmentError(EINVAL, "Invalid IP")
    if iosock is None:
        return _iostub_(inetset, card, inet)

    try:
        flag = SIOCSIFADDR
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag, [inet]))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam == AF_INET:
            return _hex2ip4_(ret[20:24]) == inet
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return ip family")
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def maskset(card: Card, mask: str, iosock: Optional[socket.socket] = None) -> bool:
    """Set nic's ip4 netmask.

    .. note:
        throws error if netmask is set and card does not have an ip assigned
    .. warning:: Requires root privileges
    """
    if not _validip4_(mask):
        raise EnvironmentError(EINVAL, "Invalid netmask")
    if iosock is None:
        return _iostub_(maskset, card, mask)
    try:
        flag = SIOCSIFNETMASK
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag, [mask]))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam == AF_INET:
            return _hex2ip4_(ret[20:24]) == mask
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return netmask family")
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        # an ambiguous error is thrown if attempting to set netmask or broadcast
        # without an ip address already set on the card
        if e.errno == EADDRNOTAVAIL:
            raise EnvironmentError(EINVAL, "Cannot set netmask. Set ip first")
        else:
            raise EnvironmentError(e, e.strerror)


def bcastset(card: Card, bcast: str, iosock: Optional[socket.socket] = None) -> bool:
    """Set nic's ip4 netmask.

    .. note:
        1) throws error if netmask is set and card does not have an ip assigned
        2) can set broadcast to erroneous values i.e. ipaddr = 192.168.1.2 and
            broadcast = 10.0.0.31.
    .. warning:: Requires root privileges
    """
    if not _validip4_(bcast):
        raise EnvironmentError(EINVAL, "Invalid bcast")
    if iosock is None:
        return _iostub_(bcastset, card, bcast)

    # we have to do one at a time
    try:
        flag = SIOCSIFBRDADDR
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag, [bcast]))
        fam = struct.unpack_from(sa_addr, ret, IFNAMELEN)[0]
        if fam == AF_INET:
            return _hex2ip4_(ret[20:24]) == bcast
        else:
            raise EnvironmentError(EAFNOSUPPORT, "Invalid return broadcast family")
    except EnvironmentError as e:
        # an ambiguous error is thrown if attempting to set netmask or broadcast
        # without an ip address already set on the card
        if e.errno == EADDRNOTAVAIL:
            raise EnvironmentError(EINVAL, "Cannot set broadcast. Set ip first")
        else:
            raise
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        # an ambiguous error is thrown if attempting to set netmask or broadcast
        # without an ip address already set on the card
        if e.errno == EADDRNOTAVAIL:
            raise EnvironmentError(EINVAL, "Cannot set broadcast. Set ip first")
        else:
            raise EnvironmentError(e, e.strerror)


################################################################################
#### HARDWARE ON/OFF                                                        ####
################################################################################


def isup(card: Card, iosock: Optional[socket.socket] = None) -> bool:
    """Return whether the card is up or not."""
    if iosock is None:
        return _iostub_(isup, card)

    try:
        return _issetf_(_flagsget_(card.dev, iosock), IFF_UP)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")


def up(card: Card, iosock: Optional[socket.socket] = None) -> None:
    """Turn device on.

    .. warning:: Requires root privileges
    """
    if iosock is None:
        return _iostub_(up, card)

    try:
        flags = _flagsget_(card.dev, iosock)
        if not _issetf_(flags, IFF_UP):
            _flagsset_(card.dev, _setf_(flags, IFF_UP), iosock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")


def down(card: Card, iosock: Optional[socket.socket] = None) -> None:
    """Turn device off.

    .. warning:: Requires root privileges
    """
    if iosock is None:
        return _iostub_(down, card)

    try:
        flags = _flagsget_(card.dev, iosock)
        if _issetf_(flags, IFF_UP):
            _flagsset_(card.dev, _unsetf_(flags, IFF_UP), iosock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")


def isblocked(card: Card) -> Tuple[bool, bool]:
    """Return whether the device is blocked or not.

    :returns: tuple (Soft={True if soft blocked|False otherwise},
                     Hard={True if hard blocked|False otherwise})
    """
    try:
        # print(card.phy)
        idx = getidx(card.phy)
        return soft_blocked(idx), hard_blocked(idx)
    except AttributeError:
        raise EnvironmentError(ENODEV, "Card is no longer registered")


def block(card: Card) -> None:
    """Soft block the card."""
    try:
        idx = getidx(card.phy)
        rfkill_block(idx)
    except AttributeError:
        raise EnvironmentError(ENODEV, "Card is no longer registered")


def unblock(card: Card) -> None:
    """Turn off soft block."""
    try:
        idx = getidx(card.phy)
        rfkill_unblock(idx)
    except AttributeError:
        raise EnvironmentError(ENODEV, "Card is no longer registered")


################################################################################
#### RADIO PROPERTIES                                                       ####
################################################################################


def pwrsaveget(card: Card, nlsock: Optional[NLSocket] = None) -> bool:
    """Return whether card's power save state is on or not."""
    if nlsock is None:
        return _nlstub_(pwrsaveget, card)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_GET_POWER_SAVE,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)

    return nla_find(rmsg, NL80211_ATTR_PS_STATE) == 1


def pwrsaveset(card: Card, on: bool, nlsock: Optional[NLSocket] = None):
    """Set card's power save state.

    .. warning:: Requires root privileges
    """
    if nlsock is None:
        return _nlstub_(pwrsaveset, card, on)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_POWER_SAVE,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nla_put_u32(msg, int(on), NL80211_ATTR_PS_STATE)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except ValueError:
        raise EnvironmentError(EINVAL, f"Invalid parameter {on} for on")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def covclassget(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the card's coverage class value."""
    if nlsock is None:
        return _nlstub_(covclassget, card)
    return phyinfo(card, nlsock)["cov_class"]


def covclassset(card: Card, cc: int, nlsock: Optional[NLSocket] = None) -> None:
    """Set the card's coverage class.

    The coverage class IAW IEEE Std 802.11-2012 is
    defined as the Air propagation time & together with max tx power control
    the BSS diamter

    :param cc: coverage class 0 to 31 IAW IEEE Std 802.11-2012 Table 8-56
    .. warning:: Requires root privileges. Also this might not work on all
        systems.
    """
    if cc < COV_CLASS_MIN or cc > COV_CLASS_MAX:
        # this can work 'incorrectly' on non-int values but these will
        # be caught later during conversion
        emsg = "Cov class must be integer {0}-{1}".format(COV_CLASS_MIN, COV_CLASS_MAX)
        raise EnvironmentError(EINVAL, emsg)
    if nlsock is None:
        return _nlstub_(covclassset, card, cc)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nla_put_u8(msg, int(cc), NL80211_ATTR_WIPHY_COVERAGE_CLASS)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except ValueError:
        raise EnvironmentError(EINVAL, f"Invalid value {cc} for Cov. Class")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def retryshortget(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the card's short retry limit."""
    if nlsock is None:
        return _nlstub_(retryshortget, card)
    return phyinfo(card, nlsock)["retry_short"]


def retryshortset(card: Card, lim: int, nlsock: Optional[NLSocket] = None):
    """Sets the short retry limit.

    :param lim: max # of short retries 1 - 255
    .. note: with kernel 4, the kernel does not allow setting up to the max
    .. warning:: Requires root privileges
    """
    if lim < RETRY_MIN or lim > RETRY_MAX:
        # this can work 'incorrectly' on non-int values but these will
        # be caught later during conversion
        emsg = "Retry short must be integer {0}-{1}".format(RETRY_MIN, RETRY_MAX)
        raise EnvironmentError(EINVAL, emsg)
    if nlsock is None:
        return _nlstub_(retryshortset, card, lim)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nla_put_u8(msg, int(lim), NL80211_ATTR_WIPHY_RETRY_SHORT)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except ValueError:
        raise EnvironmentError(EINVAL, f"Invalid value {lim} for lim")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def retrylongget(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the card's long retry limit."""
    if nlsock is None:
        return _nlstub_(retrylongget, card)
    return phyinfo(card, nlsock)["retry_long"]


def retrylongset(card: Card, lim: int, nlsock: Optional[NLSocket] = None):
    """Set the card's long retry limit.

    :param lim: max # of short retries 1 - 255
    .. note: after moving to kernel 4, the kernel does not allow setting up to
        the max
    .. warning:: Requires root privileges
    """
    if lim < RETRY_MIN or lim > RETRY_MAX:
        # this can work 'incorrectly' on non-int values but these will
        # be caught later during conversion
        emsg = "Retry long must be integer {0}-{1}".format(RETRY_MIN, RETRY_MAX)
        raise EnvironmentError(EINVAL, emsg)
    if nlsock is None:
        return _nlstub_(retrylongset, card, lim)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nla_put_u8(msg, int(lim), NL80211_ATTR_WIPHY_RETRY_LONG)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except ValueError:
        raise EnvironmentError(EINVAL, f"Invalid value {lim} for lim")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def rtsthreshget(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the card's RTS Threshold.

    :returns: RTS threshold
    """
    if nlsock is None:
        return _nlstub_(rtsthreshget, card)
    return phyinfo(card, nlsock)["rts_thresh"]


def rtsthreshset(card: Card, thresh: int, nlsock: Optional[NLSocket] = None):
    """Set the card's RTS threshold.

    If off, RTS is disabled. If an integer, sets the
    smallest packet for which card will send an RTS prior to each transmission

    .. warning:: Requires root privileges
    """
    if thresh == "off":
        thresh = RTS_THRESH_OFF
    elif thresh == RTS_THRESH_OFF:
        pass
    elif thresh < RTS_THRESH_MIN or thresh > RTS_THRESH_MAX:
        emsg = "Thresh must be 'off' or integer {0}-{1}".format(
            RTS_THRESH_MIN, RTS_THRESH_MAX
        )
        raise EnvironmentError(EINVAL, emsg)
    if nlsock is None:
        return _nlstub_(rtsthreshset, card, thresh)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nla_put_u32(msg, thresh, NL80211_ATTR_WIPHY_RTS_THRESHOLD)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except ValueError:
        raise EnvironmentError(EINVAL, f"Invalid value {thresh} for thresh")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def fragthreshget(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the card's Fragmentation Threshold.

    :returns: RTS threshold
    """
    if nlsock is None:
        return _nlstub_(fragthreshget, card)
    return phyinfo(card, nlsock)["frag_thresh"]


def fragthreshset(card: Card, thresh, nlsock: Optional[NLSocket] = None):
    """Set the card's Fragmentation threshold.

    If off, fragmentation is disabled. If an integer,
    sets the largest packet before the card will enable fragmentation

    :param thresh: frag threshold limit in octets
    .. warning:: Requires root privileges
    """
    if thresh == "off":
        thresh = FRAG_THRESH_OFF
    elif thresh == FRAG_THRESH_OFF:
        pass
    elif thresh < FRAG_THRESH_MIN or thresh > FRAG_THRESH_MAX:
        emsg = "Thresh must be 'off' or integer {0}-{1}".format(
            FRAG_THRESH_MIN, FRAG_THRESH_MAX
        )
        raise EnvironmentError(EINVAL, emsg)
    if nlsock is None:
        return _nlstub_(fragthreshset, card, thresh)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nla_put_u32(msg, thresh, NL80211_ATTR_WIPHY_FRAG_THRESHOLD)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


################################################################################
#### INFO RELATED                                                           ####
################################################################################


def devfreqs(card: Card, nlsock: Optional[NLSocket] = None) -> List[str]:
    """Return card's supported frequencies.

    :returns: list of supported frequencies
    """
    if nlsock is None:
        return _nlstub_(devfreqs, card)

    rfs: Any = []
    pinfo = phyinfo(card, nlsock)
    for band in pinfo["bands"]:
        rfs.extend(pinfo["bands"][band]["rfs"])
    rfs = sorted(rfs)
    return rfs


def devchs(card: Card, nlsock: Optional[NLSocket] = None) -> List:
    """Return the card's supported channels.

    :returns: list of supported channels
    """
    if nlsock is None:
        return _nlstub_(devchs, card)
    return [rf2ch(rf) for rf in devfreqs(card, nlsock)]


def devstds(card: Card, nlsock: Optional[NLSocket] = None) -> List[str]:
    """Return the card's wireless standards.

    :returns: list of standards (letter designators)
    """
    if nlsock is None:
        return _nlstub_(devstds, card)

    stds = []
    bands = phyinfo(card, nlsock)["bands"]
    if "5GHz" in bands:
        stds.append("a")
    if "2GHz" in bands:
        stds.extend(["b", "g"])  # assume backward compat with b
    HT = VHT = True
    for band in bands:
        HT &= bands[band]["HT"]
        VHT &= bands[band]["VHT"]
    if HT:
        stds.append("n")
    if VHT:
        stds.append("ac")
    return stds


def devmodes(card: Card, nlsock: Optional[NLSocket] = None) -> List:
    """Return the card's supported modes.

    :returns: list of card's supported modes
    """
    if nlsock is None:
        return _nlstub_(devmodes, card)
    return phyinfo(card, nlsock)["modes"]


def devcmds(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the card's supported commands.

    :returns: supported commands
    """
    if nlsock is None:
        return _nlstub_(devcmds, card)
    return phyinfo(card, nlsock)["commands"]


def ifinfo(card: Card, iosock: Optional[socket.socket] = None) -> Dict[str, Any]:
    """Return info for interface.

    :returns: dict with the following key:value pairs
        driver -> card's driver
        chipset -> card's chipset
        manufacturer -> card's manufacturer
        hwaddr -> card's mac address
        inet -> card's inet address
        bcast -> card's broadcast address
        mask -> card's netmask address
    """
    if iosock is None:
        return _iostub_(ifinfo, card)

    # get oui dict
    ouis: Dict[str, str] = {}
    try:
        ouis = load()
    except EnvironmentError:
        pass

    try:
        drvr, chips = ifcard(card.dev)
        mac = macget(card, iosock)
        ip4, nmask, bcast = ifaddrget(card, iosock)
        info = {
            "driver": drvr,
            "chipset": chips,
            "hwaddr": mac,
            "manufacturer": manufacturer(ouis, mac),
            "inet": ip4,
            "bcast": bcast,
            "mask": nmask,
        }
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")

    return info


def devinfo(card: Union[Card, str], nlsock: Optional[NLSocket] = None):
    """Return info for device.

    :returns: dict with the following key:value pairs
        card -> Card(phy,dev,ifindex)
        mode -> i.e. monitor or managed
        wdev -> wireless device id
        mac -> hw address
        RF (if associated) -> frequency
        CF (if assoicate) -> center frequency
        CHW -> channel width i.e. NOHT,HT40- etc
    """
    if nlsock is None:
        return _nlstub_(devinfo, card)

    dev = None  # appease pycharm
    try:
        # if we have a Card, pull out ifindex. otherwise get ifindex from dev
        try:
            dev = card.dev
            idx = card.idx
        except AttributeError:
            dev = card
            idx = _ifindex_(dev)

        # using the ifindex, get the phy and details about the Card
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_GET_INTERFACE,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, idx, NL80211_ATTR_IFINDEX)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)
    except EnvironmentError as e:
        # if we get a errno -19, it means ifindex failed & there is no device dev
        raise EnvironmentError(e.errno, e.strerror)
    except EnvironmentError as e:
        # if we get a errno -19, it is mostly likely because the card does
        # not support nl80211. However check to ensure the card hasn't been
        # unplugged.
        if e.errno == ENODEV:
            try:
                _ = _ifindex_(dev)
            except EnvironmentError as e:
                raise EnvironmentError(e.errno, f"{e.strerror}. Check Card")
            raise EnvironmentError(EPROTONOSUPPORT, "Device does not support nl80211")
        raise EnvironmentError(e.errno, e.strerror)

    # pull out attributes
    info = {
        "card": Card(nla_find(rmsg, NL80211_ATTR_WIPHY), dev, idx),
        "mode": IFTYPES[nla_find(rmsg, NL80211_ATTR_IFTYPE)],
        "wdev": nla_find(rmsg, NL80211_ATTR_WDEV),
        "mac": _hex2mac_(nla_find(rmsg, NL80211_ATTR_MAC)),
        "RF": nla_find(rmsg, NL80211_ATTR_WIPHY_FREQ),
        "CF": nla_find(rmsg, NL80211_ATTR_CENTER_FREQ1),
        "CHW": nla_find(rmsg, NL80211_ATTR_CHANNEL_WIDTH),
    }

    # convert CHW to string version
    try:
        info["CHW"] = CHTYPES[info["CHW"]]
    except (IndexError, TypeError):  # invalid index and NoneType
        info["CHW"] = None
    return info


def phyinfo(card: Card, nlsock: Optional[NLSocket] = None) -> Dict[str, Any]:
    """Return info for phy.

    :returns: dict with the following key:value pairs
        generation -> wiphy generation
        modes -> list of supported modes
        bands -> dict of supported bands of the form
        bandid -> {'rates': list of supported rates,
                  'rfs': list of supported freqs,
                  'rd-data': list of data corresponding to rfs,
                  'HT': 802.11n HT supported,
                  'VHT': 802.11ac VHT supported}
        scan_ssids -> max number of scan SSIDS
        retry_short -> retry short limit
        retry_long -> retry long limit
        frag_thresh -> frag threshold
        rts_thresh -> rts threshold
        cov_class -> coverage class
        swmodes -> supported software modes
        commands -> supported commands
        ciphers -> supported ciphers
    """
    if nlsock is None:
        return _nlstub_(phyinfo, card)

    # iw sends @NL80211_ATTR_SPLIT_WIPHY_DUMP, we don't & get full return at once
    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_GET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)

    # pull out attributes
    info = {
        "generation": nla_find(rmsg, NL80211_ATTR_GENERATION),
        "retry_short": nla_find(rmsg, NL80211_ATTR_WIPHY_RETRY_SHORT),
        "retry_long": nla_find(rmsg, NL80211_ATTR_WIPHY_RETRY_LONG),
        "frag_thresh": nla_find(rmsg, NL80211_ATTR_WIPHY_FRAG_THRESHOLD),
        "rts_thresh": nla_find(rmsg, NL80211_ATTR_WIPHY_RTS_THRESHOLD),
        "cov_class": nla_find(rmsg, NL80211_ATTR_WIPHY_COVERAGE_CLASS),
        "scan_ssids": nla_find(rmsg, NL80211_ATTR_MAX_NUM_SCAN_SSIDS),
        "bands": [],
        "modes": [],
        "swmodes": [],
        "commands": [],
        "ciphers": [],
    }

    # modify frag_thresh and rts_thresh as necessary
    if info["frag_thresh"] >= FRAG_THRESH_MAX:
        info["frag_thresh"] = "off"
    if info["rts_thresh"] >= RTS_THRESH_MAX:
        info["rts_thresh"] = "off"

    # complex attributes
    # NOTE: after correcting my understanding of how to parsed nested attributes
    # they should no longer result in a NLA_ERROR but just in case...
    _, bs, d = nla_find(rmsg, NL80211_ATTR_WIPHY_BANDS, False)
    if d != NLA_ERROR:
        info["bands"] = _bands_(bs)

    _, cs, d = nla_find(rmsg, NL80211_ATTR_CIPHER_SUITES, False)
    if d != NLA_ERROR:
        info["ciphers"] = _ciphers_(cs)

    # supported iftypes, sw iftypes are IAW nl80211.h flags (no attribute data)
    _, ms, d = nla_find(rmsg, NL80211_ATTR_SUPPORTED_IFTYPES, False)
    if d != NLA_ERROR:
        info["modes"] = [_iftypes_(iftype) for iftype, _ in ms]

    _, ms, d = nla_find(rmsg, NL80211_ATTR_SOFTWARE_IFTYPES, False)
    if d != NLA_ERROR:
        info["swmodes"] = [_iftypes_(iftype) for iftype, _ in ms]

    # get supported commands
    _, cs, d = nla_find(rmsg, NL80211_ATTR_SUPPORTED_COMMANDS, False)
    if d != NLA_ERROR:
        info["commands"] = _commands_(cs)

    return info


################################################################################
#### TX/RX RELATED ####
################################################################################


def txset(card: Card, setting, lvl: str, nlsock: Optional[NLSocket] = None) -> bool:
    """Set the card's tx power.

    :param setting: power level setting oneof {'auto' = automatically determine
        transmit power|'limit' = limit power by <pwr>|'fixed' = set to <pwr>}
    :param lvl: desired tx power in dBm or None. NOTE: ignored if lvl is 'auto'
    .. note: this does not work on my card(s) (nor does the corresponding iw
        command)
    .. warning:: Requires root privileges
    """
    # sanity check on power setting and power level
    if not setting in TXPWRSETTINGS:
        raise EnvironmentError(EINVAL, f"Invalid power setting {setting}")
    if setting != "auto" and lvl is None:
        raise EnvironmentError(EINVAL, "Power level must be specified")
    if nlsock is None:
        return _nlstub_(txset, card, setting, lvl)

    try:
        setting = TXPWRSETTINGS.index(setting)
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        # neither sending the phy or ifindex works
        # nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nla_put_u32(msg, setting, NL80211_ATTR_WIPHY_TX_POWER_SETTING)
        if setting != NL80211_TX_POWER_AUTOMATIC:
            nla_put_u32(msg, 100 * lvl, NL80211_ATTR_WIPHY_TX_POWER_LEVEL)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except ValueError:
        # converting to mBm
        raise EnvironmentError(EINVAL, f"Invalid value {lvl} for txpwr")
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def txget(card: Card, iosock: Optional[socket.socket] = None):
    """Return the card's transmission power.

    :returns: transmission power in dBm
    .. note: info can be found by cat /sys/kernel/debug/ieee80211/phy<#>/power but
        how valid is it?
    """
    if iosock is None:
        return _iostub_(txget, card)

    try:
        flag = SIOCGIWTXPOW
        ret = io_transfer(iosock, flag, ifreq(card.dev, flag))
        return struct.unpack_from(ifr_iwtxpwr, ret, IFNAMELEN)[0]
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except IndexError:
        return None
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def chget(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the current channel for device.

    .. note: will only work if dev is associated w/ AP or device is in monitor mode
        and has had chset previously
    """
    if nlsock is None:
        return _nlstub_(chget, card)
    return rf2ch(devinfo(card, nlsock)["RF"])


def chset(
    card: Card, ch: int, chw: Optional[str] = None, nlsock: Optional[NLSocket] = None
):
    """Set the current channel for device.

    :param ch: channel number
    :param chw: channel width oneof {None|'HT20'|'HT40-'|'HT40+'}
    .. note:
      Can throw a device busy for several reason. 1) Card is down, 2) Another
      device is sharing the phy and wpa_supplicant/Network Manage is using it
    .. warning:: Requires root privileges
    """
    if nlsock is None:
        return _nlstub_(chset, card, ch, chw)
    return freqset(card, ch2rf(ch), chw, nlsock)


def freqget(card: Card, nlsock: Optional[NLSocket] = None):
    """Return the current frequency for device.

    .. note: will only work if dev is associated w/ AP or device is in monitor mode
        and has had [ch|freq] set previously
    """
    if nlsock is None:
        return _nlstub_(chget, card)
    return devinfo(card, nlsock)["RF"]


def freqset(
    card: Card, rf, chw: Optional[str] = None, nlsock: Optional[NLSocket] = None
):
    """Set the card's frequency and width

    :param rf: frequency
    :param chw: channel width oneof {[None|'HT20'|'HT40-'|'HT40+'}
    .. note:
        Can throw a device busy for several reason. 1) Card is down, 2) Another
        device is sharing the phy and wpa_supplicant/Network Manage is using it
    .. warning:: Requires root privileges
    """
    if nlsock is None:
        return _nlstub_(freqset, card, rf, chw)

    try:
        chw = CHTYPES.index(chw)
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_WIPHY,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.phy, NL80211_ATTR_WIPHY)
        nla_put_u32(msg, rf, NL80211_ATTR_WIPHY_FREQ)
        nla_put_u32(msg, chw, NL80211_ATTR_WIPHY_CHANNEL_TYPE)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except ValueError:
        raise EnvironmentError(EINVAL, "Invalid channel width")
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        if e.errno == EBUSY:
            raise EnvironmentError(e.errno, strerror(e.errno))
        raise EnvironmentError(e.errno, e.strerror)


#### INTERFACE & MODE RELATED ####


def modeget(card: Card, nlsock: Optional[NLSocket] = None) -> str:
    """Return the card's current mode."""
    if nlsock is None:
        return _nlstub_(modeget, card)
    return devinfo(card, nlsock)["mode"]


def modeset(
    card: Card, mode: Optional[str], flags=None, nlsock: Optional[NLSocket] = None
):
    """Set the card's mode.

    (APX iw dev <card.dev> set type <mode> [flags])

    :param mode: 'name' of mode to operate in (must be one of in {'unspecified'|
        'ibss'|'managed'|'AP'|'AP VLAN'|'wds'|'monitor'|'mesh'|'p2p'}
    :param flags: list of monitor flags (can only be used if card is being set
        to monitor mode) neof {'invalid'|'fcsfail'|'plcpfail'|'control'|'other bss'
                             |'cook'|'active'}
    .. note: as far
    """
    if mode not in IFTYPES:
        raise EnvironmentError(EINVAL, "Invalid mode")
    if flags and mode != "monitor":
        raise EnvironmentError(EINVAL, "Can only set flags in monitor mode")
    if flags:
        for flag in flags:
            if flag not in MNTRFLAGS:
                raise EnvironmentError(EINVAL, f"Invalid flag: {flag}")
    else:
        flags = []
    if nlsock is None:
        return _nlstub_(modeset, card, mode, flags)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_INTERFACE,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nla_put_u32(msg, IFTYPES.index(mode), NL80211_ATTR_IFTYPE)
        for flag in flags:
            nla_put_u32(msg, MNTRFLAGS.index(flag), NL80211_ATTR_MNTR_FLAGS)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def ifaces(card: Card, nlsock: Optional[NLSocket] = None) -> List[Tuple[Card, str]]:
    """Return all interfaces sharing the same phy as card.

    (APX iw dev | grep phy#)

    :returns: a list of tuples t = (Card, mode) for each device having the same
        phyiscal index as that of card
    """
    if nlsock is None:
        return _nlstub_(ifaces, card)

    ifs = []
    for dev in winterfaces():
        info = devinfo(dev, nlsock)
        try:
            if info["card"].phy == card.phy:
                ifs.append((info["card"], info["mode"]))
        except AttributeError:
            raise EnvironmentError(EINVAL, "Invalid Card")
        except EnvironmentError as e:
            raise EnvironmentError(e.errno, e.strerror)
    return ifs


def devset(card: Card, ndev, nlsock: Optional[NLSocket] = None) -> Card:
    """Change the card's device name.


    :param ndev: new dev name
    :returns: the new card object
    .. note:
        - via netlink one can set a new physical name but we want the ability to
            set a new dev.
        - this is not a true set name: it adds a new card with ndev as the dev then
            deletes the current card, returning the new card
        - in effect, it will appear as if the card has a new name but, it will also
            have a new ifindex
    .. warning: Requires root privileges
    """
    if nlsock is None:
        return _nlstub_(devset, card, ndev)

    new = None  # appease PyCharm
    try:
        mode = modeget(card, nlsock)
        phy = card.phy
        devdel(card, nlsock)
        new = phyadd(phy, ndev, mode, None, nlsock)
    except EnvironmentError:
        # try and restore the system i.e. delete new if possible
        if new:
            try:
                devdel(new, nlsock)
            except EnvironmentError:
                pass
        if not validcard(card):
            try:
                pass
            except EnvironmentError:
                pass
        raise
    return new


def devadd(
    card: Card, vdev: str, mode: str, flags=None, nlsock: Optional[NLSocket] = None
) -> Card:
    """Add a virtual interface on device having type mode.

    iw dev <card.dev> interface add <vnic> type <mode>

    :param vdev: device name of new interface
    :param mode: 'name' of mode to operate in (must be one of in {'unspecified'|
        'ibss'|'managed'|'AP'|'AP VLAN'|'wds'|'monitor'|'mesh'|'p2p'}
    :param flags: list of monitor flags (can only be used if creating monitor
        mode) oneof {'invalid'|'fcsfail'|'plcpfail'|'control'|'other bss'
                    |'cook'|'active'}
    .. note: the new Card will be 'down'
    .. warning: Requires root privileges
    """
    if iswireless(vdev):
        raise EnvironmentError(ENOTUNIQ, f"{vdev} already exists")
    if mode not in IFTYPES:
        raise EnvironmentError(EINVAL, "Invalid mode")
    if flags and mode != "monitor":
        raise EnvironmentError(EINVAL, "Can only set flags in monitor mode")
    if flags:
        for flag in flags:
            if flag not in MNTRFLAGS:
                raise EnvironmentError(EINVAL, f"Invalid flag: {flag}")
    else:
        flags = []
    if nlsock is None:
        return _nlstub_(devadd, card, vdev, mode, flags)

    # if we have a Card, pull out ifindex
    try:
        idx = card.idx
    except AttributeError:
        idx = card

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_NEW_INTERFACE,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, idx, NL80211_ATTR_IFINDEX)
        nla_put_string(msg, vdev, NL80211_ATTR_IFNAME)
        nla_put_u32(msg, IFTYPES.index(mode), NL80211_ATTR_IFTYPE)
        for flag in flags:
            nla_put_u32(msg, MNTRFLAGS.index(flag), NL80211_ATTR_MNTR_FLAGS)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)  # success returns new device attributes
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)

    # return the new Card with info from the results msg
    return Card(
        nla_find(rmsg, NL80211_ATTR_WIPHY),
        nla_find(rmsg, NL80211_ATTR_IFNAME),
        nla_find(rmsg, NL80211_ATTR_IFINDEX),
    )


def devdel(card: Card, nlsock: Optional[NLSocket] = None) -> None:
    """delete the device.

    .. note: the original card is no longer valid (i.e. the phy will still be present
     but the device name and ifindex are no longer 'present' in the system
    .. warning: Requires root privileges.
    """
    if nlsock is None:
        return _nlstub_(devdel, card)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_DEL_INTERFACE,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def phyadd(
    card: Card, vdev: str, mode: str, flags=None, nlsock: Optional[NLSocket] = None
) -> Card:
    """Add a virtual interface on device having type mode.

    iw phy <card.phy> interface add <vnic> type <mode>

    :param vdev: device name of new interface
    :param mode: 'name' of mode to operate in (must be one of in {'unspecified'|
    'ibss'|'managed'|'AP'|'AP VLAN'|'wds'|'monitor'|'mesh'|'p2p'}
    :param flags: list of monitor flags (can only be used if creating monitor
    mode) oneof {'invalid'|'fcsfail'|'plcpfail'|'control'|'other bss'
                 |'cook'|'active'}
    .. note: the new Card will be 'down'
    .. warning: Requires root privileges.
    """
    if mode not in IFTYPES:
        raise EnvironmentError(EINVAL, "Invalid mode")
    if flags:
        if mode != "monitor":
            raise EnvironmentError(EINVAL, "Can only set flags in monitor mode")
        for flag in flags:
            if flag not in MNTRFLAGS:
                raise EnvironmentError(EINVAL, f"Invalid flag: {flag}")
    else:
        flags = []
    if nlsock is None:
        return _nlstub_(phyadd, card, vdev, mode, flags)

    # if we have a Card, pull out phy
    try:
        phy = card.phy
    except AttributeError:
        phy = card

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_NEW_INTERFACE,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, phy, NL80211_ATTR_WIPHY)
        nla_put_string(msg, vdev, NL80211_ATTR_IFNAME)
        nla_put_u32(msg, IFTYPES.index(mode), NL80211_ATTR_IFTYPE)
        for flag in flags:
            nla_put_u32(msg, MNTRFLAGS.index(flag), NL80211_ATTR_MNTR_FLAGS)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)  # success returns new device attributes
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)

    # get card & determine if we got a card with the specified name
    return Card(
        nla_find(rmsg, NL80211_ATTR_WIPHY),
        nla_find(rmsg, NL80211_ATTR_IFNAME),
        nla_find(rmsg, NL80211_ATTR_IFINDEX),
    )


################################################################################
#### STA FUNCTIONS                                                          ####
################################################################################


def isconnected(card: Card, nlsock: Optional[NLSocket] = None) -> bool:
    """Return whether card is connected to an access point."""
    if nlsock is None:
        return _nlstub_(isconnected, card)
    return devinfo(card, nlsock)["RF"] is not None


def connect(
    card: Card,
    ssid: str,
    bssid: Optional[str] = None,
    rf=None,
    nlsock: Optional[NLSocket] = None,
) -> bool:
    """Connect card to an open access point.

     :param ssid: the SSID, network name
     :param bssid: the AP's BSSID
     :param rf:  the frequency of the AP
    .. note: Although connected, traffic will not be routed, card will not have
      an IP assigned
    .. warning: Requires root privileges and WPA_SUPPLICANT must be disabled.
    """
    if nlsock is None:
        return _nlstub_(connect, card, ssid, bssid, rf)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_CONNECT,  # step 1
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nla_put_unspec(msg, ssid, NL80211_ATTR_SSID)
        nla_put_unspec(msg, _mac2hex_(bssid), NL80211_ATTR_MAC)
        nl_sendmsg(nlsock, msg)
        if not nl_recvmsg(nlsock) == NLE_SUCCESS:
            return False
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)
    return True


def disconnect(card: Card, nlsock: Optional[NLSocket] = None) -> None:
    """Disconnect the card from the access point.

    .. note: does not return error if card is not connected. May not work if
     wpa_supplicant is running.
    .. warning: Requires root privileges.
    """
    if nlsock is None:
        return _nlstub_(disconnect, card)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_DISCONNECT,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def link(card: Card, nlsock: Optional[NLSocket] = None) -> Dict[str, Any]:
    """Return information about link.

    (iw dev card.<dev> link)

    :returns: link info as dict  with the following key:value pairs
      bssid -> AP mac/ net BSSID
      ssid -> the ssid (Experimental)
      freq -> BSSID frequency in MHz
      chw -> width of the BSS control channel
      rss -> Received signal strength in dBm
      int -> beacon interval (ms)
      stat -> status w.r.t of card to BSS one of {'authenticated','associated','ibss'}
      tx -> tx metrics dict of the form
       pkts -> total sent packets to connected STA (AP)
       bytes -> total sent in bytes to connected STA (AP)
       retries -> total # of retries
       failed -> total # of failed
       bitrate -> dict of form
         rate -> tx rate in Mbits
         width -> channel width oneof {None|20|40}
         mcs-index -> mcs index (0..32) or None
         gaurd -> guard interval oneof {None|0=short|1=long}
         Note: width, mcs-index, guard will be None unless 802.11n is being used
      rx -> rx metrics dict (see tx for format exluces retries and fails)
     or None if the card is not connected
    .. note: if the nested attribute was not parsed correctly will attempt to pull
     out as much as possible
    """
    if nlsock is None:
        return _nlstub_(link, card)

    # if we're not connected GET_SCAN will dump scan results, we don't want that
    if not isconnected(card, nlsock):
        return None

    try:
        # we need to set additional flags or the kernel will return ERRNO 95
        flags = NLM_F_REQUEST | NLM_F_ACK | NLM_F_ROOT | NLM_F_MATCH
        msg = nlmsg_new(
            nltype=_familyid_(nlsock), cmd=NL80211_CMD_GET_SCAN, flags=flags
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)

    # link returns multiple attributes but we are only concerned w/ @NL80211_ATTR_BSS
    # some cards (my integrated intel) do not parse correctly
    info = {
        "bssid": None,
        "ssid": None,
        "freq": None,
        "rss": None,
        "int": None,
        "chw": None,
        "stat": None,
        "tx": {},
        "rx": {},
    }

    _, bs, d = nla_find(rmsg, NL80211_ATTR_BSS, False)
    if d == NLA_ERROR:
        return info
    for idx, attr in bs:
        # any errors attempting to parse -> leave as default None, empty
        try:
            if idx == NL80211_BSS_BSSID:
                info["bssid"] = _hex2mac_(attr)
            if idx == NL80211_BSS_FREQUENCY:
                info["freq"] = struct.unpack_from("I", attr, 0)[0]
            if idx == NL80211_BSS_SIGNAL_MBM:
                info["rss"] = struct.unpack_from("i", attr, 0)[0] / 100
            if idx == NL80211_BSS_INFORMATION_ELEMENTS:
                """
                hack the proprietary info element attribute: (it should
                be a nested attribute itself, but I have currently no way of
                knowing what the individual indexes would mean
                 \x06\x00\x00<l>SSID.....
                '\x06\x00' is the ie index & the ssid is the first element
                (from what I've seen). This is not nested. Not sure if the
                length is the first two bytes or just the second  Get the length
                of the ssid which is the 3rd,4th byte, then unpack the string
                starting at the fifth byte up to the specified length
                """
                try:
                    l = struct.unpack_from(">H", attr, 0)[
                        0
                    ]  # have to change the format
                    info["ssid"] = struct.unpack_from("{0}s".format(l), attr, 2)[0]
                except struct.error:
                    pass
            if idx == NL80211_BSS_BEACON_INTERVAL:
                info["int"] = struct.unpack_from("H", attr, 0)[0]
            if idx == NL80211_BSS_CHAN_WIDTH:
                j = struct.unpack_from("I", attr, 0)[0]
                info["chw"] = NL80211_BSS_CHAN_WIDTHS[j]
            if idx == NL80211_BSS_STATUS:
                j = struct.unpack_from("I", attr, 0)[0]
                info["stat"] = NL80211_BSS_STATUSES[j]
        except struct.error:
            pass

    # process stainfo of AP
    try:
        sinfo = stainfo(card, info["bssid"], nlsock)
        info["tx"] = {
            "bytes": sinfo["tx-bytes"],
            "pkts": sinfo["tx-pkts"],
            "failed": sinfo["tx-failed"],
            "retries": sinfo["tx-retries"],
            "bitrate": {"rate": sinfo["tx-bitrate"]["rate"]},
        }
        if sinfo["tx-bitrate"].has_key("mcs-index"):
            info["tx"]["bitrate"]["mcs-index"] = sinfo["tx-bitrate"]["mcs-index"]
            info["tx"]["bitrate"]["gi"] = sinfo["tx-bitrate"]["gi"]
            info["tx"]["bitrate"]["width"] = sinfo["tx-bitrate"]["width"]

        info["rx"] = {
            "bytes": sinfo["rx-bytes"],
            "pkts": sinfo["rx-pkts"],
            "bitrate": {"rate": sinfo["rx-bitrate"]["rate"]},
        }
        if sinfo["rx-bitrate"].has_key("mcs-index"):
            info["rx"]["bitrate"]["mcs-index"] = sinfo["rx-bitrate"]["mcs-index"]
            info["rx"]["bitrate"]["gi"] = sinfo["rx-bitrate"]["gi"]
            info["rx"]["bitrate"]["width"] = sinfo["rx-bitrate"]["width"]
    except (KeyError, TypeError, AttributeError):
        # ignore for now, returning what we got
        pass

    return info


def stainfo(card: Card, mac: str, nlsock: Optional[NLSocket] = None) -> Dict[str, Any]:
    """Return info about sta (AP) the card is associated with.

    (iw dev card.<dev> link)

    :param mac: mac address of STA
    :returns: sta info as dict  with the following key:value pairs
     rx-bytes: total received bytes (from STA)
     tx-bytes: total sent bytes (to STA)
     rx-pkts: total received packets (from STA)
     tx-pkts: total sent packets (to STA)
     tx-bitrate: dict of the form
      rate: bitrate in 100kbits/s
      legacy: fallback bitrate in 100kbits/s (only present if rate is not determined)
      mcs-index: mcs index (0..32) (only present if 802.11n)
      gi: guard interval oneof {0=short|1=long} (only present if 802.11n)
      width: channel width oneof {20|40}
     rx-bitrate: see tx-bitrate
    .. note:
     - if the nested attribute was not parsed correctly will attempt to pull
      out as much as possible
     - given msc index, guard interval and channel width, one can calculate the
      802.11n rate (see wraith->standards->mcs)
    """
    if nlsock is None:
        return _nlstub_(stainfo, card, mac)

    # if we're not connected GET_SCAN will dump scan results, we don't want that
    if not isconnected(card, nlsock):
        return None

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_GET_STATION,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nla_put_unspec(msg, _mac2hex_(mac), NL80211_ATTR_MAC)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)

    # we are only concerned w/ @NL80211_ATTR_STA_INFO
    info = {
        "rx-bytes": None,
        "tx-bytes": None,
        "rx-pkts": None,
        "tx-pkts": None,
        "tx-bitrate": {},
        "rx-bitrate": {},
    }

    _, bs, d = nla_find(rmsg, NL80211_ATTR_STA_INFO, False)
    if d == NLA_ERROR:
        return info
    for sidx, sattr in bs:  # sidx indexes the enum nl80211_sta_info
        try:
            if sidx == NL80211_STA_INFO_RX_BYTES:
                info["rx-bytes"] = struct.unpack_from("I", sattr, 0)[0]
            elif sidx == NL80211_STA_INFO_TX_BYTES:
                info["tx-bytes"] = struct.unpack_from("I", sattr, 0)[0]
            elif sidx == NL80211_STA_INFO_RX_PACKETS:
                info["rx-pkts"] = struct.unpack_from("I", sattr, 0)[0]
            elif sidx == NL80211_STA_INFO_TX_PACKETS:
                info["tx-pkts"] = struct.unpack_from("I", sattr, 0)[0]
            elif sidx == NL80211_STA_INFO_TX_RETRIES:
                info["tx-retries"] = struct.unpack_from("I", sattr, 0)[0]
            elif sidx == NL80211_STA_INFO_TX_FAILED:
                info["tx-failed"] = struct.unpack_from("I", sattr, 0)[0]
            elif sidx == NL80211_STA_INFO_TX_BITRATE:
                info["tx-bitrate"] = _rateinfo_(sattr)
            elif sidx == NL80211_STA_INFO_RX_BITRATE:
                info["rx-bitrate"] = _rateinfo_(sattr)
        except struct.error:
            # ignore this and hope other elements still work
            pass

    return info


################################################################################
#### FILE PRIVATE                                                           ####
################################################################################

IPADDR = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")  # re for ip addr
MACADDR = re.compile(r"^([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2})$")  # re for mac addr


def _hex2ip4_(v):
    """
    :param v: packed by string
    :returns: a '.' separated ip4 address from byte stream v
    """
    try:
        return ".".join([str(ord(c)) for c in v])
    except TypeError:
        # python 3 c is already numeric
        return ".".join([str(c) for c in v])


def _hex2mac_(v):
    """
    :param v: packed bytestream of form \xd8\xc7\xc8\x00\x11\x22
    :returns: a ':' separated mac address from byte stream v
    """
    try:
        return ":".join(["{0:02x}".format(ord(c)) for c in v])
    except TypeError:
        # it appears that in Python 3.5 c is already numeric
        return ":".join(["{0:02x}".format(c) for c in v])


def _mac2hex_(v: str):
    """
    converts mac address to hex string
    :param v: mac address of form xx:yy:zz:00:11:22
    :returns: mac address as hex string
    """
    try:
        return struct.pack("6B", *[int(x, 16) for x in v.split(":")])
    except AttributeError:
        raise EnvironmentError(EINVAL, "Mac address is not valid")
    except struct.error:
        raise EnvironmentError(EINVAL, "Mac address is not 6 octets")


def _validip4_(addr):
    """
    determines validity of ip4 address
    :param addr: ip addr to check
    :returns: True if addr is valid ip, False otherwise
    """
    try:
        if re.match(IPADDR, addr):
            return True
    except TypeError:
        return False
    return False


def _validmac_(addr):
    """
    determines validity of hw addr
    :param addr: address to check
    :returns: True if addr is valid hw address, False otherwise
    """
    try:
        if re.match(MACADDR, addr):
            return True
    except TypeError:
        return False
    return False


def _issetf_(flags, flag):
    """
    determines if flag is set
    :param flags: current flag value
    :param flag: flag to check
    :return: True if flag is set
    """
    return (flags & flag) == flag


def _setf_(flags, flag):
    """
    sets flag, adding to flags
    :param flags: current flag value
    :param flag: flag to set
    :return: new flag value
    """
    return flags | flag


def _unsetf_(flags, flag):
    """
    unsets flag, adding to flags
    :param flags: current flag value
    :param flag: flag to unset
    :return: new flag value
    """
    return flags & ~flag


def _flagsget_(dev, iosock: Optional[socket.socket] = None):
    """
    gets the device's flags
    :param dev: device name:
    :param iosock: ioctl socket
    :returns: device flags
    """
    if iosock is None:
        return _iostub_(_flagsget_, dev)

    try:
        flag = SIOCGIFFLAGS
        ret = io_transfer(iosock, flag, ifreq(dev, flag))
        return struct.unpack_from(ifr_flags, ret, IFNAMELEN)[0]
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


def _flagsset_(dev, flags, iosock: Optional[socket.socket] = None):
    """
    gets the device's flags
    :param dev: device name:
    :param flags: flags to set
    :param iosock: ioctl socket
    :returns: device flags after operation
    """
    if iosock is None:
        return _iostub_(_flagsset_, dev, flags)

    try:
        flag = SIOCSIFFLAGS
        ret = io_transfer(iosock, flag, ifreq(dev, flag, [flags]))
        return struct.unpack_from(ifr_flags, ret, IFNAMELEN)[0]
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)


#### ADDITIONAL PARSING FOR PHYINFO ####


def _iftypes_(i):
    """
    wraps the IFTYPES list to handle index errors
    :param i:
    :returns: the string IFTYPE corresponding to i
    """
    try:
        return IFTYPES[i]
    except IndexError:
        return "Unknown mode ({0})".format(i)


def _bands_(bs):
    """
    extracts supported freqs, rates from bands
    :param bs: a list of one or more unparsed band attributes
    :returns: dict of the form
     band: one of {'2GHz'|'5GHz'|'UNK (n)'} -> band dict
     band dict ->
      HT: HT is supported by the Card on this band
      VHT: VHT is supported by the Card on this band
      rates: list of supported rates
      rfs: list of supported frequencies
      rf-data: list of dicts of rf-data where rf-data[i] contains info
       regarding rf[i]
    """
    # NOTE: in addition to RF and rates there are HT data included in the
    # band info ATT we do not parse these (see "phy info notes 3.txt")
    bands = {}
    for idx, band in bs:
        # the index tell us what band were in (enum nl80211_band)
        try:
            idx = NL80211_BANDS[idx]
        except IndexError:
            idx = "UNK ({0})".format(idx)
        bands[idx] = {
            "HT": False,
            "VHT": False,
            "rates": None,
            "rfs": None,
            "rf-data": None,
        }

        # now we delve into multiple levels of nesting
        for bidx, battr in nla_parse_nested(band):
            # There are other data here (see nl80211_h nl80211_band_attr)
            # that we are not currently using
            if bidx == NL80211_BAND_ATTR_RATES:
                try:
                    bands[idx]["rates"] = _band_rates_(battr)
                except EnvironmentError:
                    bands[idx]["rates"] = []
            elif bidx == NL80211_BAND_ATTR_FREQS:
                try:
                    bands[idx]["rfs"], bands[idx]["rf-data"] = _band_rfs_(battr)
                except EnvironmentError:
                    bands[idx]["rfs"], bands[idx]["rf-data"] = [], []
            elif bidx in [
                NL80211_BAND_ATTR_HT_MCS_SET,
                NL80211_BAND_ATTR_HT_CAPA,
                NL80211_BAND_ATTR_HT_AMPDU_FACTOR,
                NL80211_BAND_ATTR_HT_AMPDU_DENSITY,
            ]:
                bands[idx]["HT"] = True
            elif bidx in [NL80211_BAND_ATTR_VHT_MCS_SET, NL80211_BAND_ATTR_VHT_CAPA]:
                bands[idx]["VHT"] = True
    return bands


def _band_rates_(rs):
    """
    unpacks individual rates from packed rates
    :param rs: packed rates
    :returns: a list of rates in Mbits
    NOTE: ATT we ignore any short preamble specifier
    """
    rates = []
    # unlike other nested attributes, the 'index' into rates is actually
    # a counter (which we'll ignore)
    for _, attr in nla_parse_nested(rs):
        # the nested attribute itself is a nested attribute. The idx indexes
        # the enum nl80211_bitrate_attr of which we are only concerned w/ rate
        for idx, bitattr in nla_parse_nested(attr):
            if idx == NL80211_BITRATE_ATTR_RATE:
                rates.append(struct.unpack_from("I", bitattr, 0)[0] * 0.1)
    return rates


def _band_rfs_(rs):
    """
    unpacks individual RFs (and accompanying data) from packed rfs
    :param rs: packed frequencies
    :returns: a tuple t = (freqs: list of supported RFS (MHz), data: list of dicts)
    where for each i in freqs, data[i] is the corresponding data having the
    form {}
    """
    rfs = []
    rfds = []
    # like rates, the index here is a counter and fattr is a nested attribute
    for _, fattr in nla_parse_nested(rs):
        # RF data being compiled ATT we are ignoring DFS related and infrared
        # related. rfd is initially defined with max-tx, radar, 20Mhz and 10Mhz
        # with 'default' values.
        # Additional values may be returned by the kernel. If present they will
        # be appended to not-permitted as the following strings
        #  HT40-, HT40+, 80MHz, 160MHz and outdoor.
        # If present in not-permitted, they represent False Flags
        rfd = {
            "max-tx": 0,  # Card's maximum tx-power on this RF
            "enabled": True,  # w/ current reg. dom. RF is enabled
            "20Mhz": True,  # w/ current reg. dom. 20MHz operation is allowed
            "10Mhz": True,  # w/ current reg. dom. 10MHz operation is allowed
            "radar": False,  # w/ current reg. dom. radar detec. required on RF
            "not-permitted": [],  # additional flags
        }
        for rfi, rfattr in nla_parse_nested(fattr):
            # rfi is the index into enum nl80211_frequency_attr
            if rfi == NL80211_FREQUENCY_ATTR_FREQ:
                rfs.append(struct.unpack_from("I", rfattr, 0)[0])
            elif rfi == NL80211_FREQUENCY_ATTR_DISABLED:
                rfd["enabled"] = False
            elif rfi == NL80211_FREQUENCY_ATTR_MAX_TX_POWER:  # in mBm
                rfd["max-tx"] = struct.unpack_from("I", rfattr, 0)[0] / 100
            elif rfi == NL80211_FREQUENCY_ATTR_NO_HT40_MINUS:
                rfd["not-permitted"].append("HT40-")
            elif rfi == NL80211_FREQUENCY_ATTR_NO_HT40_PLUS:
                rfd["not-permitted"].append("HT40+")
            elif rfi == NL80211_FREQUENCY_ATTR_NO_80MHZ:
                rfd["not-permitted"].append("80MHz")
            elif rfi == NL80211_FREQUENCY_ATTR_NO_160MHZ:
                rfd["not-permitted"].append("160MHz")
            elif rfi == NL80211_FREQUENCY_ATTR_INDOOR_ONLY:
                rfd["not-permitted"].append("outdoor")
            elif rfi == NL80211_FREQUENCY_ATTR_NO_20MHZ:
                rfd["20MHz"] = False
            elif rfi == NL80211_FREQUENCY_ATTR_NO_10MHZ:
                rfd["10MHz"] = False
        rfds.append(rfd)
    return rfs, rfds


def _unparsed_rf_(band):
    """
    (LEGACY) extract list of supported freqs packed byte stream band
    :param band: packed byte string from NL80211_ATTR_WIPHY_BANDS
    :returns: list of supported frequencies
    """
    rfs = []
    for freq in freqs():
        if band.find(struct.pack("I", freq)) != -1:
            rfs.append(freq)
    return rfs


def _commands_(command):
    """
    converts numeric commands to string version
    :param command: list of command constants
    :returns: list of supported commands as strings
    """
    cs = []
    for _, cmd in command:  # rather than an index, commands use a counter, ignore it
        try:
            # use numeric command to lookup string version in form
            #    @NL80211_CMD_<CMD>
            # and strip "@NL80211_CMD_". NOTE: some commands may have multiple
            # string synonyms, in that case, take the first one. Finally, make
            # it lowercase
            cmd = cmdbynum(struct.unpack_from("I", cmd, 0)[0])
            if type(cmd) is type([]):
                cmd = cmd[0]
            cs.append(cmd[13:].lower())  # skip NL80211_CMD_
        except KeyError:
            # kernel 4 added commands not found in kernel 3 nlh8022.h.
            # keep this just in case new commands pop up again
            cs.append("unknown cmd ({0})".format(cmd))
    return cs


def _ciphers_(ciphers):
    """
    identifies supported ciphers
    :param ciphers: the cipher suite stream
    :returns: a list of supported ciphers
    """
    ss = []
    for cipher in ciphers:  # ciphers is a set and not nested
        try:
            ss.append(WLAN_CIPHER_SUITE_SELECTORS[cipher])
        except KeyError as e:
            # we could do nothing, or append 'rsrv' but we'll add a little
            # for testing/future identificaion purposes
            ss.append("RSRV-{0}".format(hex(int(e.__str__()))))
    return ss


#### ADDITIONAL PARSING FOR STAINFO


def _rateinfo_(ri):
    """
    parses the rate info stream returning a bitrate dict
    :param ri: rate info stream
    :returns: bitrate dict having the key->value pairs
     rate: bitrate in 100kbits/s
     legacy: fallback bitrate in 100kbits/s (only present if rate is not determined)
     mcs-index: mcs index (0..32) (only present if 802.11n)
     gi: guard interval oneof {0=short|1=long} (only present if 802.11n)
     width: channel width oneof {20|40}
    NOTE: references enum nl80211_rate_info
    """
    bitrate = {"rate": None, "legacy": None, "mcs-index": None, "gi": 1, "width": 20}
    for i, attr in nla_parse_nested(ri):
        if i == NL80211_RATE_INFO_BITRATE32:
            bitrate["rate"] = struct.unpack_from("I", attr, 0)[0] * 0.1
        elif i == NL80211_RATE_INFO_BITRATE:  # legacy fallback rate
            bitrate["legacy"] = struct.unpack_from("H", attr, 0)[0]
        elif i == NL80211_RATE_INFO_MCS:
            bitrate["mcs-index"] = struct.unpack_from("B", attr, 0)[0]
        elif i == NL80211_RATE_INFO_40_MHZ_WIDTH:  # flag
            bitrate["width"] = 40
        elif i == NL80211_RATE_INFO_SHORT_GI:  # flag
            bitrate["gi"] = 0

    # clean it up before returning
    # remove legacy if we have rate or make rate = legacy if we dont have rate
    # remove mcs-index and short gi and 40 MHz if there is no mcs-index
    if bitrate["legacy"] and not bitrate["rate"]:
        bitrate["rate"] = bitrate["legacy"]
    if bitrate["rate"] and bitrate["legacy"]:
        del bitrate["legacy"]
    if bitrate["mcs-index"] is None:
        del bitrate["mcs-index"]
        del bitrate["gi"]
        del bitrate["width"]

    return bitrate


#### NETLINK/IOCTL PARAMETERS ####


def _ifindex_(dev, iosock: Optional[socket.socket] = None):
    """
    gets the ifindex for device
    :param dev: device name:
    :param iosock: ioctl socket
    :returns: ifindex of device
    NOTE: the ifindex can aslo be found in /sys/class/net/<nic>/ifindex
    """
    if iosock is None:
        return _iostub_(_ifindex_, dev)

    try:
        flag = SIOCGIFINDEX
        ret = io_transfer(iosock, flag, ifreq(dev, flag))
        return struct.unpack_from(ifr_ifindex, ret, IFNAMELEN)[0]
    except AttributeError as e:
        raise EnvironmentError(EINVAL, e)
    except struct.error as e:
        raise EnvironmentError(EUNDEF, f"Error parsing results: {e}")


def _familyid_(nlsock: NLSocket):
    """
    extended version: get the family id
    :param nlsock: netlink socket
    :returns: the family id of nl80211
    NOTE:
     In addition to the family id, we get:
      CTRL_ATTR_FAMILY_NAME = nl80211\x00
      CTRL_ATTR_VERSION = \x01\x00\x00\x00 = 1
      CTRL_ATTR_HDRSIZE = \x00\x00\x00\x00 = 0
      CTRL_ATTR_MAXATTR = \xbf\x00\x00\x00 = 191
      CTRL_ATTR_OPS
      CTRL_ATTR_MCAST_GROUPS
     but for now, these are not used
    """
    global _FAM80211ID_
    if _FAM80211ID_ is None:
        # family id is not instantiated, do so now
        msg = nlmsg_new(
            nltype=GENL_ID_CTRL, cmd=CTRL_CMD_GETFAMILY, flags=NLM_F_REQUEST | NLM_F_ACK
        )
        nla_put_string(msg, NL80211_GENL_NAME, CTRL_ATTR_FAMILY_NAME)
        nl_sendmsg(nlsock, msg)
        rmsg = nl_recvmsg(nlsock)
        _FAM80211ID_ = nla_find(rmsg, CTRL_ATTR_FAMILY_ID)
    return _FAM80211ID_


#### TRANSLATION FUNCTIONS ####


def _iostub_(fct, *argv):
    """
    translates from traditional ioctl <cmd> to extended <cmd>ex
    :param fct: function to translate to
    :param argv: parameters to the function
    :returns: the results of fct
    """
    iosock = io_socket_alloc()
    try:
        argv = list(argv) + [iosock]
        return fct(*argv)
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, strerror(e.errno))
    except EnvironmentError:
        raise  # catch and rethrow
    finally:
        io_socket_free(iosock)


def _nlstub_(fct, *argv):
    """
    translates from traditional netlink <cmd> to extended <cmd>ex
    :param fct: function to translate to
    :param argv: parameters to the function
    :returns: rresults of fucntion
    """
    nlsock = None
    try:
        nlsock = nl_socket_alloc(timeout=2)
        argv = list(argv) + [nlsock]
        # print(argv)
        return fct(*argv)
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, strerror(e.errno))
    except EnvironmentError:
        raise
    finally:
        if nlsock:
            nl_socket_free(nlsock)


#### PENDING ####


def _fut_chset(card: Card, ch, chw, nlsock: Optional[NLSocket] = None):
    """
    set current channel on device (iw phy <card.phy> set channel <ch> <chw>
    :param card: Card object
    :param ch: channel number
    :param chw: channel width oneof {None|'HT20'|'HT40-'|'HT40+'}
    :param nlsock: netlink socket
    uses the newer NL80211_CMD_SET_CHANNEL vice iw's depecrated version which
    uses *_SET_WIPHY however, ATT does not work raise Errno 22 Invalid Argument
    NOTE: This only works for cards in monitor mode
    """
    if ch not in channels():
        raise EnvironmentError(EINVAL, "Invalid channel")
    if chw not in CHTYPES:
        raise EnvironmentError(EINVAL, "Invalid channel width")
    if nlsock is None:
        return _nlstub_(_fut_chset, card, ch, chw)

    try:
        msg = nlmsg_new(
            nltype=_familyid_(nlsock),
            cmd=NL80211_CMD_SET_CHANNEL,
            flags=NLM_F_REQUEST | NLM_F_ACK,
        )
        nla_put_u32(msg, card.idx, NL80211_ATTR_IFINDEX)
        nla_put_u32(msg, ch2rf(ch), NL80211_ATTR_WIPHY_FREQ)
        nla_put_u32(msg, CHTYPES.index(chw), NL80211_ATTR_WIPHY_CHANNEL_TYPE)
        nl_sendmsg(nlsock, msg)
        _ = nl_recvmsg(nlsock)
    except AttributeError:
        raise EnvironmentError(EINVAL, "Invalid Card")
    except EnvironmentError as e:
        raise EnvironmentError(e.errno, e.strerror)
