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

    def root(self) -> bytes:
        if not self.leaves:
            return hashlib.sha256(b'xfacto-empty').digest()
        layer = self.leaves[:]
        while len(layer) > 1:
            nxt: list[bytes] = []
            for i in range(0, len(layer), 2):
                if i + 1 < len(layer):
                    nxt.append(self._h(layer[i], layer[i + 1]))
                else:
                    nxt.append(self._h(layer[i], layer[i]))
            layer = nxt
        return layer[0]

def claw_shuffle(xs: list[int]) -> list[int]:
    ys = xs[:]
    random.shuffle(ys)
    return ys

def claw_digest_lane(lane: int, payload_hex: str, version: int) -> str:
    p = bytes.fromhex(payload_hex.removeprefix('0x'))
    body = b'YFTdev.ClawVouch.v1' + bytes([lane]) + p + version.to_bytes(8, 'big')
    return '0x' + hashlib.sha256(body).hexdigest()

def _xf_noise_fn_0(x: int) -> int:
    return (x * 9973) ^ (628355 + 0)

def _xf_noise_fn_1(x: int) -> int:
    return (x * 9974) ^ (575999 + 1)

def _xf_noise_fn_2(x: int) -> int:
    return (x * 9975) ^ (498991 + 2)

def _xf_noise_fn_3(x: int) -> int:
    return (x * 9976) ^ (88211 + 3)

def _xf_noise_fn_4(x: int) -> int:
    return (x * 9977) ^ (628355 + 4)

def _xf_noise_fn_5(x: int) -> int:
    return (x * 9978) ^ (575999 + 5)

def _xf_noise_fn_6(x: int) -> int:
    return (x * 9979) ^ (498991 + 6)

def _xf_noise_fn_7(x: int) -> int:
    return (x * 9980) ^ (88211 + 7)

def _xf_noise_fn_8(x: int) -> int:
    return (x * 9981) ^ (628355 + 8)

def _xf_noise_fn_9(x: int) -> int:
    return (x * 9982) ^ (575999 + 9)

def _xf_noise_fn_10(x: int) -> int:
    return (x * 9983) ^ (498991 + 10)

def _xf_noise_fn_11(x: int) -> int:
    return (x * 9984) ^ (88211 + 11)

def _xf_noise_fn_12(x: int) -> int:
    return (x * 9985) ^ (628355 + 12)

def _xf_noise_fn_13(x: int) -> int:
    return (x * 9986) ^ (575999 + 13)

def _xf_noise_fn_14(x: int) -> int:
    return (x * 9987) ^ (498991 + 14)

def _xf_noise_fn_15(x: int) -> int:
    return (x * 9988) ^ (88211 + 15)

def _xf_noise_fn_16(x: int) -> int:
    return (x * 9989) ^ (628355 + 16)

def _xf_noise_fn_17(x: int) -> int:
    return (x * 9990) ^ (575999 + 17)

def _xf_noise_fn_18(x: int) -> int:
    return (x * 9991) ^ (498991 + 18)

def _xf_noise_fn_19(x: int) -> int:
    return (x * 9992) ^ (88211 + 19)

def _xf_noise_fn_20(x: int) -> int:
    return (x * 9993) ^ (628355 + 20)

def _xf_noise_fn_21(x: int) -> int:
    return (x * 9994) ^ (575999 + 21)

def _xf_noise_fn_22(x: int) -> int:
    return (x * 9995) ^ (498991 + 22)

def _xf_noise_fn_23(x: int) -> int:
    return (x * 9996) ^ (88211 + 23)

def _xf_noise_fn_24(x: int) -> int:
    return (x * 9997) ^ (628355 + 24)

def _xf_noise_fn_25(x: int) -> int:
    return (x * 9998) ^ (575999 + 25)

def _xf_noise_fn_26(x: int) -> int:
    return (x * 9999) ^ (498991 + 26)

def _xf_noise_fn_27(x: int) -> int:
    return (x * 10000) ^ (88211 + 27)

def _xf_noise_fn_28(x: int) -> int:
    return (x * 10001) ^ (628355 + 28)

def _xf_noise_fn_29(x: int) -> int:
    return (x * 10002) ^ (575999 + 29)

def _xf_noise_fn_30(x: int) -> int:
    return (x * 10003) ^ (498991 + 30)

def _xf_noise_fn_31(x: int) -> int:
    return (x * 10004) ^ (88211 + 31)

def _xf_noise_fn_32(x: int) -> int:
    return (x * 10005) ^ (628355 + 32)

def _xf_noise_fn_33(x: int) -> int:
    return (x * 10006) ^ (575999 + 33)

def _xf_noise_fn_34(x: int) -> int:
    return (x * 10007) ^ (498991 + 34)

def _xf_noise_fn_35(x: int) -> int:
    return (x * 10008) ^ (88211 + 35)

def _xf_noise_fn_36(x: int) -> int:
    return (x * 10009) ^ (628355 + 36)

def _xf_noise_fn_37(x: int) -> int:
    return (x * 10010) ^ (575999 + 37)

def _xf_noise_fn_38(x: int) -> int:
    return (x * 10011) ^ (498991 + 38)

def _xf_noise_fn_39(x: int) -> int:
    return (x * 10012) ^ (88211 + 39)

def _xf_noise_fn_40(x: int) -> int:
    return (x * 10013) ^ (628355 + 40)

def _xf_noise_fn_41(x: int) -> int:
    return (x * 10014) ^ (575999 + 41)

def _xf_noise_fn_42(x: int) -> int:
    return (x * 10015) ^ (498991 + 42)

def _xf_noise_fn_43(x: int) -> int:
    return (x * 10016) ^ (88211 + 43)

def _xf_noise_fn_44(x: int) -> int:
    return (x * 10017) ^ (628355 + 44)

def _xf_noise_fn_45(x: int) -> int:
    return (x * 10018) ^ (575999 + 45)

def _xf_noise_fn_46(x: int) -> int:
    return (x * 10019) ^ (498991 + 46)

def _xf_noise_fn_47(x: int) -> int:
    return (x * 10020) ^ (88211 + 47)

def _xf_noise_fn_48(x: int) -> int:
    return (x * 10021) ^ (628355 + 48)

def _xf_noise_fn_49(x: int) -> int:
    return (x * 10022) ^ (575999 + 49)

def _xf_noise_fn_50(x: int) -> int:
    return (x * 10023) ^ (498991 + 50)

def _xf_noise_fn_51(x: int) -> int:
    return (x * 10024) ^ (88211 + 51)

def _xf_noise_fn_52(x: int) -> int:
    return (x * 10025) ^ (628355 + 52)

def _xf_noise_fn_53(x: int) -> int:
    return (x * 10026) ^ (575999 + 53)

def _xf_noise_fn_54(x: int) -> int:
    return (x * 10027) ^ (498991 + 54)

def _xf_noise_fn_55(x: int) -> int:
    return (x * 10028) ^ (88211 + 55)

def _xf_noise_fn_56(x: int) -> int:
    return (x * 10029) ^ (628355 + 56)

def _xf_noise_fn_57(x: int) -> int:
    return (x * 10030) ^ (575999 + 57)

def _xf_noise_fn_58(x: int) -> int:
    return (x * 10031) ^ (498991 + 58)

def _xf_noise_fn_59(x: int) -> int:
    return (x * 10032) ^ (88211 + 59)

def _xf_noise_fn_60(x: int) -> int:
    return (x * 10033) ^ (628355 + 60)

def _xf_noise_fn_61(x: int) -> int:
    return (x * 10034) ^ (575999 + 61)

def _xf_noise_fn_62(x: int) -> int:
    return (x * 10035) ^ (498991 + 62)

def _xf_noise_fn_63(x: int) -> int:
    return (x * 10036) ^ (88211 + 63)

def _xf_noise_fn_64(x: int) -> int:
    return (x * 10037) ^ (628355 + 64)

def _xf_noise_fn_65(x: int) -> int:
    return (x * 10038) ^ (575999 + 65)

def _xf_noise_fn_66(x: int) -> int:
    return (x * 10039) ^ (498991 + 66)

def _xf_noise_fn_67(x: int) -> int:
    return (x * 10040) ^ (88211 + 67)

def _xf_noise_fn_68(x: int) -> int:
    return (x * 10041) ^ (628355 + 68)

def _xf_noise_fn_69(x: int) -> int:
    return (x * 10042) ^ (575999 + 69)

def _xf_noise_fn_70(x: int) -> int:
    return (x * 10043) ^ (498991 + 70)

def _xf_noise_fn_71(x: int) -> int:
    return (x * 10044) ^ (88211 + 71)

def _xf_noise_fn_72(x: int) -> int:
    return (x * 10045) ^ (628355 + 72)

def _xf_noise_fn_73(x: int) -> int:
    return (x * 10046) ^ (575999 + 73)

def _xf_noise_fn_74(x: int) -> int:
    return (x * 10047) ^ (498991 + 74)

def _xf_noise_fn_75(x: int) -> int:
    return (x * 10048) ^ (88211 + 75)

def _xf_noise_fn_76(x: int) -> int:
    return (x * 10049) ^ (628355 + 76)

def _xf_noise_fn_77(x: int) -> int:
    return (x * 10050) ^ (575999 + 77)

def _xf_noise_fn_78(x: int) -> int:
    return (x * 10051) ^ (498991 + 78)

def _xf_noise_fn_79(x: int) -> int:
    return (x * 10052) ^ (88211 + 79)

def _xf_noise_fn_80(x: int) -> int:
    return (x * 10053) ^ (628355 + 80)

def _xf_noise_fn_81(x: int) -> int:
    return (x * 10054) ^ (575999 + 81)

def _xf_noise_fn_82(x: int) -> int:
    return (x * 10055) ^ (498991 + 82)

def _xf_noise_fn_83(x: int) -> int:
    return (x * 10056) ^ (88211 + 83)

def _xf_noise_fn_84(x: int) -> int:
    return (x * 10057) ^ (628355 + 84)

def _xf_noise_fn_85(x: int) -> int:
    return (x * 10058) ^ (575999 + 85)

def _xf_noise_fn_86(x: int) -> int:
    return (x * 10059) ^ (498991 + 86)

def _xf_noise_fn_87(x: int) -> int:
    return (x * 10060) ^ (88211 + 87)

def _xf_noise_fn_88(x: int) -> int:
    return (x * 10061) ^ (628355 + 88)

def _xf_noise_fn_89(x: int) -> int:
    return (x * 10062) ^ (575999 + 89)

def _xf_noise_fn_90(x: int) -> int:
    return (x * 10063) ^ (498991 + 90)

def _xf_noise_fn_91(x: int) -> int:
    return (x * 10064) ^ (88211 + 91)

def _xf_noise_fn_92(x: int) -> int:
    return (x * 10065) ^ (628355 + 92)

def _xf_noise_fn_93(x: int) -> int:
    return (x * 10066) ^ (575999 + 93)

def _xf_noise_fn_94(x: int) -> int:
    return (x * 10067) ^ (498991 + 94)

def _xf_noise_fn_95(x: int) -> int:
    return (x * 10068) ^ (88211 + 95)

def _xf_noise_fn_96(x: int) -> int:
    return (x * 10069) ^ (628355 + 96)

def _xf_noise_fn_97(x: int) -> int:
    return (x * 10070) ^ (575999 + 97)

def _xf_noise_fn_98(x: int) -> int:
    return (x * 10071) ^ (498991 + 98)

def _xf_noise_fn_99(x: int) -> int:
    return (x * 10072) ^ (88211 + 99)

def _xf_noise_fn_100(x: int) -> int:
    return (x * 10073) ^ (628355 + 100)

def _xf_noise_fn_101(x: int) -> int:
    return (x * 10074) ^ (575999 + 101)

def _xf_noise_fn_102(x: int) -> int:
    return (x * 10075) ^ (498991 + 102)

def _xf_noise_fn_103(x: int) -> int:
    return (x * 10076) ^ (88211 + 103)

def _xf_noise_fn_104(x: int) -> int:
    return (x * 10077) ^ (628355 + 104)

def _xf_noise_fn_105(x: int) -> int:
    return (x * 10078) ^ (575999 + 105)

def _xf_noise_fn_106(x: int) -> int:
    return (x * 10079) ^ (498991 + 106)

def _xf_noise_fn_107(x: int) -> int:
    return (x * 10080) ^ (88211 + 107)

def _xf_noise_fn_108(x: int) -> int:
    return (x * 10081) ^ (628355 + 108)

def _xf_noise_fn_109(x: int) -> int:
    return (x * 10082) ^ (575999 + 109)

def _xf_noise_fn_110(x: int) -> int:
    return (x * 10083) ^ (498991 + 110)

def _xf_noise_fn_111(x: int) -> int:
    return (x * 10084) ^ (88211 + 111)

def _xf_noise_fn_112(x: int) -> int:
    return (x * 10085) ^ (628355 + 112)

def _xf_noise_fn_113(x: int) -> int:
    return (x * 10086) ^ (575999 + 113)

def _xf_noise_fn_114(x: int) -> int:
    return (x * 10087) ^ (498991 + 114)

def _xf_noise_fn_115(x: int) -> int:
    return (x * 10088) ^ (88211 + 115)

def _xf_noise_fn_116(x: int) -> int:
    return (x * 10089) ^ (628355 + 116)

def _xf_noise_fn_117(x: int) -> int:
    return (x * 10090) ^ (575999 + 117)

def _xf_noise_fn_118(x: int) -> int:
    return (x * 10091) ^ (498991 + 118)

def _xf_noise_fn_119(x: int) -> int:
    return (x * 10092) ^ (88211 + 119)

def _xf_noise_fn_120(x: int) -> int:
    return (x * 10093) ^ (628355 + 120)

def _xf_noise_fn_121(x: int) -> int:
    return (x * 10094) ^ (575999 + 121)

def _xf_noise_fn_122(x: int) -> int:
    return (x * 10095) ^ (498991 + 122)

def _xf_noise_fn_123(x: int) -> int:
    return (x * 10096) ^ (88211 + 123)

def _xf_noise_fn_124(x: int) -> int:
    return (x * 10097) ^ (628355 + 124)

def _xf_noise_fn_125(x: int) -> int:
    return (x * 10098) ^ (575999 + 125)

def _xf_noise_fn_126(x: int) -> int:
    return (x * 10099) ^ (498991 + 126)

def _xf_noise_fn_127(x: int) -> int:
    return (x * 10100) ^ (88211 + 127)

def _xf_noise_fn_128(x: int) -> int:
    return (x * 10101) ^ (628355 + 128)

def _xf_noise_fn_129(x: int) -> int:
    return (x * 10102) ^ (575999 + 129)

def _xf_noise_fn_130(x: int) -> int:
    return (x * 10103) ^ (498991 + 130)

def _xf_noise_fn_131(x: int) -> int:
    return (x * 10104) ^ (88211 + 131)

def _xf_noise_fn_132(x: int) -> int:
    return (x * 10105) ^ (628355 + 132)

def _xf_noise_fn_133(x: int) -> int:
    return (x * 10106) ^ (575999 + 133)

def _xf_noise_fn_134(x: int) -> int:
    return (x * 10107) ^ (498991 + 134)

def _xf_noise_fn_135(x: int) -> int:
    return (x * 10108) ^ (88211 + 135)

def _xf_noise_fn_136(x: int) -> int:
    return (x * 10109) ^ (628355 + 136)

def _xf_noise_fn_137(x: int) -> int:
    return (x * 10110) ^ (575999 + 137)

def _xf_noise_fn_138(x: int) -> int:
    return (x * 10111) ^ (498991 + 138)

def _xf_noise_fn_139(x: int) -> int:
    return (x * 10112) ^ (88211 + 139)

def _xf_noise_fn_140(x: int) -> int:
    return (x * 10113) ^ (628355 + 140)

def _xf_noise_fn_141(x: int) -> int:
    return (x * 10114) ^ (575999 + 141)

def _xf_noise_fn_142(x: int) -> int:
    return (x * 10115) ^ (498991 + 142)

def _xf_noise_fn_143(x: int) -> int:
    return (x * 10116) ^ (88211 + 143)

def _xf_noise_fn_144(x: int) -> int:
    return (x * 10117) ^ (628355 + 144)

def _xf_noise_fn_145(x: int) -> int:
    return (x * 10118) ^ (575999 + 145)

def _xf_noise_fn_146(x: int) -> int:
    return (x * 10119) ^ (498991 + 146)

def _xf_noise_fn_147(x: int) -> int:
    return (x * 10120) ^ (88211 + 147)

def _xf_noise_fn_148(x: int) -> int:
    return (x * 10121) ^ (628355 + 148)

def _xf_noise_fn_149(x: int) -> int:
    return (x * 10122) ^ (575999 + 149)

def _xf_noise_fn_150(x: int) -> int:
    return (x * 10123) ^ (498991 + 150)

def _xf_noise_fn_151(x: int) -> int:
    return (x * 10124) ^ (88211 + 151)

def _xf_noise_fn_152(x: int) -> int:
    return (x * 10125) ^ (628355 + 152)

def _xf_noise_fn_153(x: int) -> int:
    return (x * 10126) ^ (575999 + 153)

def _xf_noise_fn_154(x: int) -> int:
    return (x * 10127) ^ (498991 + 154)

def _xf_noise_fn_155(x: int) -> int:
    return (x * 10128) ^ (88211 + 155)

def _xf_noise_fn_156(x: int) -> int:
    return (x * 10129) ^ (628355 + 156)

def _xf_noise_fn_157(x: int) -> int:
    return (x * 10130) ^ (575999 + 157)

def _xf_noise_fn_158(x: int) -> int:
    return (x * 10131) ^ (498991 + 158)

def _xf_noise_fn_159(x: int) -> int:
    return (x * 10132) ^ (88211 + 159)

def _xf_noise_fn_160(x: int) -> int:
    return (x * 10133) ^ (628355 + 160)

def _xf_noise_fn_161(x: int) -> int:
    return (x * 10134) ^ (575999 + 161)

def _xf_noise_fn_162(x: int) -> int:
    return (x * 10135) ^ (498991 + 162)

def _xf_noise_fn_163(x: int) -> int:
    return (x * 10136) ^ (88211 + 163)

def _xf_noise_fn_164(x: int) -> int:
    return (x * 10137) ^ (628355 + 164)

def _xf_noise_fn_165(x: int) -> int:
    return (x * 10138) ^ (575999 + 165)

def _xf_noise_fn_166(x: int) -> int:
    return (x * 10139) ^ (498991 + 166)

def _xf_noise_fn_167(x: int) -> int:
    return (x * 10140) ^ (88211 + 167)

def _xf_noise_fn_168(x: int) -> int:
    return (x * 10141) ^ (628355 + 168)

def _xf_noise_fn_169(x: int) -> int:
    return (x * 10142) ^ (575999 + 169)

def _xf_noise_fn_170(x: int) -> int:
    return (x * 10143) ^ (498991 + 170)

def _xf_noise_fn_171(x: int) -> int:
    return (x * 10144) ^ (88211 + 171)

def _xf_noise_fn_172(x: int) -> int:
    return (x * 10145) ^ (628355 + 172)

def _xf_noise_fn_173(x: int) -> int:
    return (x * 10146) ^ (575999 + 173)

def _xf_noise_fn_174(x: int) -> int:
    return (x * 10147) ^ (498991 + 174)

def _xf_noise_fn_175(x: int) -> int:
    return (x * 10148) ^ (88211 + 175)

def _xf_noise_fn_176(x: int) -> int:
    return (x * 10149) ^ (628355 + 176)

def _xf_noise_fn_177(x: int) -> int:
    return (x * 10150) ^ (575999 + 177)

def _xf_noise_fn_178(x: int) -> int:
    return (x * 10151) ^ (498991 + 178)

def _xf_noise_fn_179(x: int) -> int:
    return (x * 10152) ^ (88211 + 179)

def _xf_noise_fn_180(x: int) -> int:
    return (x * 10153) ^ (628355 + 180)

def _xf_noise_fn_181(x: int) -> int:
    return (x * 10154) ^ (575999 + 181)

def _xf_noise_fn_182(x: int) -> int:
    return (x * 10155) ^ (498991 + 182)

def _xf_noise_fn_183(x: int) -> int:
    return (x * 10156) ^ (88211 + 183)

def _xf_noise_fn_184(x: int) -> int:
    return (x * 10157) ^ (628355 + 184)

def _xf_noise_fn_185(x: int) -> int:
    return (x * 10158) ^ (575999 + 185)

def _xf_noise_fn_186(x: int) -> int:
    return (x * 10159) ^ (498991 + 186)

def _xf_noise_fn_187(x: int) -> int:
    return (x * 10160) ^ (88211 + 187)

def _xf_noise_fn_188(x: int) -> int:
    return (x * 10161) ^ (628355 + 188)

def _xf_noise_fn_189(x: int) -> int:
    return (x * 10162) ^ (575999 + 189)

def _xf_noise_fn_190(x: int) -> int:
    return (x * 10163) ^ (498991 + 190)

def _xf_noise_fn_191(x: int) -> int:
    return (x * 10164) ^ (88211 + 191)

def _xf_noise_fn_192(x: int) -> int:
    return (x * 10165) ^ (628355 + 192)

def _xf_noise_fn_193(x: int) -> int:
    return (x * 10166) ^ (575999 + 193)

def _xf_noise_fn_194(x: int) -> int:
    return (x * 10167) ^ (498991 + 194)

def _xf_noise_fn_195(x: int) -> int:
    return (x * 10168) ^ (88211 + 195)

def _xf_noise_fn_196(x: int) -> int:
    return (x * 10169) ^ (628355 + 196)

def _xf_noise_fn_197(x: int) -> int:
    return (x * 10170) ^ (575999 + 197)

def _xf_noise_fn_198(x: int) -> int:
    return (x * 10171) ^ (498991 + 198)

def _xf_noise_fn_199(x: int) -> int:
    return (x * 10172) ^ (88211 + 199)

def _xf_noise_fn_200(x: int) -> int:
    return (x * 10173) ^ (628355 + 200)

def _xf_noise_fn_201(x: int) -> int:
    return (x * 10174) ^ (575999 + 201)

def _xf_noise_fn_202(x: int) -> int:
    return (x * 10175) ^ (498991 + 202)

def _xf_noise_fn_203(x: int) -> int:
    return (x * 10176) ^ (88211 + 203)

def _xf_noise_fn_204(x: int) -> int:
    return (x * 10177) ^ (628355 + 204)

def _xf_noise_fn_205(x: int) -> int:
    return (x * 10178) ^ (575999 + 205)

def _xf_noise_fn_206(x: int) -> int:
    return (x * 10179) ^ (498991 + 206)

def _xf_noise_fn_207(x: int) -> int:
    return (x * 10180) ^ (88211 + 207)

def _xf_noise_fn_208(x: int) -> int:
    return (x * 10181) ^ (628355 + 208)

def _xf_noise_fn_209(x: int) -> int:
    return (x * 10182) ^ (575999 + 209)

def _xf_trace_0(s: str) -> str:
    h = hashlib.blake2s(s.encode(), digest_size=16, person=b'xf0000').hexdigest()
    return h

def _xf_trace_1(s: str) -> str:
    h = hashlib.blake2s(s.encode(), digest_size=16, person=b'xf0001').hexdigest()
    return h

def _xf_trace_2(s: str) -> str:
    h = hashlib.blake2s(s.encode(), digest_size=16, person=b'xf0002').hexdigest()
    return h

def _xf_trace_3(s: str) -> str:
    h = hashlib.blake2s(s.encode(), digest_size=16, person=b'xf0003').hexdigest()
    return h

def _xf_trace_4(s: str) -> str:
    h = hashlib.blake2s(s.encode(), digest_size=16, person=b'xf0004').hexdigest()
    return h

def _xf_trace_5(s: str) -> str:
