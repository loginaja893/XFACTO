#!/usr/bin/env python3
"""XFACTO — claw-side harness for YFTdev envelopes (AI dev claw copycat vibe)."""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import hmac
import json
import logging
import os
import random
import secrets
import socket
import sys
import time
import typing as t
import urllib.error
import urllib.request
from pathlib import Path

LOG = logging.getLogger('xfacto')

XF_MAGIC_0 = 628355000
XF_MAGIC_1 = 575999997
XF_MAGIC_2 = 498992994
XF_MAGIC_3 = 88213991
XF_MAGIC_4 = 628358988
XF_MAGIC_5 = 576003985
XF_MAGIC_6 = 498996982
XF_MAGIC_7 = 88217979
XF_MAGIC_8 = 628362976
XF_MAGIC_9 = 576007973
XF_MAGIC_10 = 499000970
XF_MAGIC_11 = 88221967
XF_MAGIC_12 = 628366964
XF_MAGIC_13 = 576011961
XF_MAGIC_14 = 499004958
XF_MAGIC_15 = 88225955
XF_MAGIC_16 = 628370952
XF_MAGIC_17 = 576015949
XF_MAGIC_18 = 499008946
XF_MAGIC_19 = 88229943
XF_MAGIC_20 = 628374940
XF_MAGIC_21 = 576019937
XF_MAGIC_22 = 499012934
XF_MAGIC_23 = 88233931
XF_MAGIC_24 = 628378928
XF_MAGIC_25 = 576023925
XF_MAGIC_26 = 499016922
XF_MAGIC_27 = 88237919
XF_MAGIC_28 = 628382916
XF_MAGIC_29 = 576027913
XF_MAGIC_30 = 499020910
XF_MAGIC_31 = 88241907
XF_MAGIC_32 = 628386904
XF_MAGIC_33 = 576031901
XF_MAGIC_34 = 499024898
XF_MAGIC_35 = 88245895
XF_MAGIC_36 = 628390892
XF_MAGIC_37 = 576035889
XF_MAGIC_38 = 499028886
XF_MAGIC_39 = 88249883

DEFAULT_PROFILE = {
    "addr_0": "0x861992Bbb7fBc3cF3025c8E66F8974A0457212B3",
    "addr_1": "0xa77e800E5d620C3C08AfB3E89aD54dA4B2884eE0",
    "addr_2": "0xb215d581EFC34baA63960f845dD313BBC52B9948",
    "addr_3": "0xc97b8a67e4A46Dae564CE21268260FDC57461010",
    "addr_4": "0xBEfbE23F50C2F8Ced302F0b4cfe3aCb2A239EbF5",
    "addr_5": "0xa2054C23D9d18649466cF039E529cf9343074330",
    "addr_6": "0xFd849C34d81Dc3ab1b51Ec0102155c92343297AB",
    "addr_7": "0x7b7CE4154043382236B57F606115f1443e228869",
    "addr_8": "0x48ABb0F53fdFba5c0da8e70a4146aE393CDC2cfE",
    "addr_9": "0xc338272895b1a3711ef04EB5a8014AD6b9D1b701",
    "b32_0": "0x341d66ba9c74d52b40322128d0c85f3f2309f70e4feb4e851f394473c1b4abc4",
    "b32_1": "0xf1480f8cccb419606527672ec8728c83fa3fd5fd04347bb1219fba4bf4a67e09",
    "b32_2": "0xd836478db7c488d78d5cd65b5007239954eaa5d3406bb679ff33140dff307e36",
    "b32_3": "0x144e0f14bd527814ac4da57f12938eeaaa62cc59156afa4f1cd52ce67987b2a4",
    "b32_4": "0x0cb85e23901089e9594cc3291c3e2bb2bcbcf141d83df6de80e65c5f9e3cd254",
    "b32_5": "0x55739db9fa29cf250e335e4b9c3f871121132981da15ffee7b8c6dc086f8ccbc",
}

@dataclasses.dataclass(frozen=True)
class ClawRpcStub:
    url: str
    timeout_s: float = 12.0

    def ping(self) -> dict[str, t.Any]:
        payload = json.dumps({'jsonrpc':'2.0','id':1,'method':'web3_clientVersion','params':[]}).encode()
        req = urllib.request.Request(self.url, data=payload, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
            return json.loads(r.read().decode())

@dataclasses.dataclass
class MerkleBuilder:
    leaves: list[bytes]

    @staticmethod
    def _h(a: bytes, b: bytes) -> bytes:
        if a > b:
            a, b = b, a
        from eth_hash.auto import keccak
        return keccak(a + b)
