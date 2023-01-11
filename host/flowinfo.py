from scapy.all import Packet, IPOption, BitField, ByteField, IntField
from scapy.layers.inet import _IPOption_HDR

class FLOWINFO(IPOption):
    name = "FLOWINFO"
    option = 99
    fields_desc = [
        _IPOption_HDR,
#        ByteField("type", 99),
        ByteField("len", 64),
        IntField("RFS", 0),
        BitField("retcnt", 0, 4),
        BitField("flowid", 0, 3),
        BitField("FLAGS", 0, 1),
        ByteField("END", 0)
    ]

