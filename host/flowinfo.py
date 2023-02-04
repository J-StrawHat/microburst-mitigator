from scapy.all import BitField, ByteField, ShortEnumField, ByteEnumField, Emph, DestIPField, SourceIPField
from scapy.layers.inet import IPOption, _IPOption_HDR, IP_PROTOS, TCP_SERVICES

class FLOWINFO(IPOption):
    name = "FLOWINFO"
    option = 31
    fields_desc = [ 
        _IPOption_HDR,
        ByteField("length", 2),
        BitField("flow_id", 0, 12),
        BitField("egress_ts", 0, 48),
        BitField("deq_qdepth", 0, 19),
        BitField("deflect_idx", 0, 32),
        BitField("padding", 0, 33) 
    ]

