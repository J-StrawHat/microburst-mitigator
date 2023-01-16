/** Headers **/
typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;


header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<6>    dscp;
    bit<2>    ecn;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header ipv4_option_t {
    bit<1> copyFlag;
    bit<2> optClass;
    bit<5> option;
    bit<8> optionLength;
}

header flowinfo_t{
    bit<32> ipv4_srcAddr;
    bit<32> ipv4_dstAddr;
    bit<16> tcp_sport;
    bit<16> tcp_dport;
    bit<8>  protocol;
    bit<48> ingress_ts;
    bit<48> egress_ts; 
    bit<19> enq_qdepth;
    bit<19> deq_qdepth; 
    bit<2>  padding; // 238 bits of telemetry data + 2 bits of padding + 16 bits of IPOption header = 256 bits (multiple of 32)
} 

header tcp_t{
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<1>  cwr;
    bit<1>  ece;
    bit<1>  urg;
    bit<1>  ack;
    bit<1>  psh;
    bit<1>  rst;
    bit<1>  syn;
    bit<1>  fin;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

struct metadata {
    bit<14> ecmp_hash;
    bit<14> ecmp_group_id;
}

struct headers {
    ethernet_t     ethernet;
    ipv4_t         ipv4;
    ipv4_option_t  ipv4_option;
    flowinfo_t     flowinfo; 
    tcp_t          tcp;
}

