#!/usr/bin/env python
""" attributes defines netlink attribute policies and functions.

Copyright (C) 2016  Dale V. Patterson (wraith.wireless@yandex.com)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

Redistribution and use in source and binary forms, with or without modifications,
are permitted provided that the following conditions are met:
 o Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
 o Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
 o Neither the name of the orginal author Dale V. Patterson nor the names of any
   contributors may be used to endorse or promote products derived from this
   software without specific prior written permission.

For lack of a better place to put these, this defines attribute datatypes from
genetlink.h and imports those defined in nl80211_c.

NOTE: I only use the datatype ignoring minlength, maxlength

"""

__name__ = "attributes"
__license__ = "GPLv3"
__version__ = "0.0.2"
__date__ = "April 2016"
__author__ = "Dale Patterson"
__maintainer__ = "Dale Patterson"
__email__ = "wraith.wireless@yandex.com"
__status__ = "Production"

from .netlink_h import NLA_UNSPEC, NLA_NESTED, NLA_U32, NLA_U16, NLA_STRING
from .genetlink_h import (
    CTRL_ATTR_UNSPEC,
    CTRL_ATTR_FAMILY_ID,
    CTRL_ATTR_FAMILY_NAME,
    CTRL_ATTR_VERSION,
    CTRL_ATTR_HDRSIZE,
    CTRL_ATTR_MAXATTR,
    CTRL_ATTR_OPS,
    CTRL_ATTR_MCAST_GROUPS,
    CTRL_ATTR_OP_UNSPEC,
    CTRL_ATTR_OP_ID,
    CTRL_ATTR_OP_FLAGS,
    CTRL_ATTR_MCAST_GRP_NAME,
    CTRL_ATTR_MCAST_GRP_UNSPEC,
    CTRL_ATTR_MCAST_GRP_ID,
)
from .wireless.nl80211_c import nl80211_policy


def nla_datatype(policy, attr):
    """
    determines the appropriate attribute datatype as found in policy
    :param policy: policy name
    :param attr: attribute type
    :returns: a datatype as specified in netlink_h
    NOTE: will return NLA_UNSPEC if given attr can not be found in policy
    """
    try:
        return nla_dts[policy][attr]
    except (KeyError, IndexError):
        return NLA_UNSPEC


# map string names to datatype lists
nla_dts = {}
nla_dts_set = {}

#### CTRL_ATTR_*
# commented out below to determine if nested _OPS and _MCAST_GROUPS
# was causing an infinite loop in nla_parse_nested
nla_dts["ctrl_attr"] = {
    CTRL_ATTR_UNSPEC: NLA_UNSPEC,
    CTRL_ATTR_FAMILY_ID: NLA_U16,
    CTRL_ATTR_FAMILY_NAME: NLA_STRING,
    CTRL_ATTR_VERSION: NLA_U32,
    CTRL_ATTR_HDRSIZE: NLA_U32,
    CTRL_ATTR_MAXATTR: NLA_U32,
    CTRL_ATTR_OPS: NLA_NESTED,
    # CTRL_ATTR_OPS: NLA_UNSPEC,
    CTRL_ATTR_MCAST_GROUPS: NLA_NESTED,
}
# CTRL_ATTR_MCAST_GROUPS: NLA_UNSPEC}

#### CTRL_ATTR_OP_*
nla_dts["ctrl_attr_op"] = {
    CTRL_ATTR_OP_UNSPEC: NLA_UNSPEC,
    CTRL_ATTR_OP_ID: NLA_U32,
    CTRL_ATTR_OP_FLAGS: NLA_U32,
}

#### CTRL_ATTR_MCAST_*
nla_dts["ctrl_attr_mcast"] = {
    CTRL_ATTR_MCAST_GRP_UNSPEC: NLA_UNSPEC,
    CTRL_ATTR_MCAST_GRP_NAME: NLA_STRING,
    CTRL_ATTR_MCAST_GRP_ID: NLA_U32,
}

nla_dts["nl80211_attr"] = nl80211_policy
