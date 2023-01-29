#include "constants.p4"
/** Parser阶段 **/
parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType){
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.ihl){
            5 : dispatch_on_protocol; //说明由5个双字（四字节）组成，即IPv4最小首部
            default: parse_ipv4_options;
        }
    }

    state parse_ipv4_options {
        packet.extract(hdr.ipv4_option);
        transition select(hdr.ipv4_option.option){
            TYPE_FLOWINFO : parse_flowinfo;
            default: dispatch_on_protocol;
        }
    }

    state parse_flowinfo {
        packet.extract(hdr.flowinfo);
        transition dispatch_on_protocol;
    }

    state dispatch_on_protocol {
        transition select(hdr.ipv4.protocol){
            6 : parse_tcp;
            default: accept;
        }
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
        transition accept;
    }
}

/** Deparser阶段 **/
control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        //parsed headers have to be added again into the packet.
        //Only emited if valid
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.ipv4_option);
        packet.emit(hdr.flowinfo);
        packet.emit(hdr.tcp);
    }
}