from scapy.all import BitField, ByteField, ShortEnumField, ByteEnumField, Emph, DestIPField, SourceIPField
from scapy.layers.inet import IPOption, _IPOption_HDR, IP_PROTOS, TCP_SERVICES

class FLOWINFO(IPOption):
    name = "FLOWINFO"
    option = 31
    fields_desc = [ 
        _IPOption_HDR,
        ByteField("length", 2),
        Emph(SourceIPField("src", "dst")),
        Emph(DestIPField("dst", "127.0.0.1")),
        ShortEnumField("tcp_sport", 20, TCP_SERVICES),
        ShortEnumField("tcp_dport", 80, TCP_SERVICES),
        ByteEnumField("protocol", 0, IP_PROTOS),
        BitField("ingress_ts", 0, 48),
        BitField("egress_ts", 0, 48),
        BitField("enq_qdepth", 0, 19),
        BitField("deq_qdepth", 0, 19),
        BitField("padding", 0, 2) 
    ]

