/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

//My includes
#include "include/headers.p4"
#include "include/parsers.p4"


/** Checksum的验证阶段(每收到一个包均需验证checksum，以确保该包是完整的没被修改过的) **/
control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/** Ingress处理 **/
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    
    register<bit<9>>(PORT_NUM) qdepth_table;
    
    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;    //到达新目标，更新源MAC地址
        hdr.ethernet.dstAddr = dstAddr;                 //查表可得到下一跳的目标Mac地址
        standard_metadata.egress_spec = port;           //查表得到输出端口
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;                //更新TTL
    }

    action set_egress_type (bit<4> egress_type){
        meta.egress_type = egress_type;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
        }
        size = 1024;
        default_action = drop;
    }

    table egress_type {
        //表的建立过程已在routing-controller.py的set_egress_type_table()声明
        key = { //对出端口进行匹配
            standard_metadata.egress_spec: exact;
        }
        actions = {
            set_egress_type; //查表得知下一个邻节点是主机还是交换机，并保存至元数据中的egress_type
            NoAction;
        }
        size=64;
        default_action = NoAction;
    }

    apply {
        if (hdr.ipv4.isValid()){
            ipv4_lpm.apply();
            egress_type.apply();
            if (hdr.flowinfo.isValid()){
                //
                qdepth_table.write((bit<32>)standard_metadata.ingress_port, (bit<9>)hdr.flowinfo.deq_qdepth);
            }
            else {
                //如果下一跳是交换机并且是「刚刚从主机出发」，则将Flowinfo首部嵌入到数据包中
                if (meta.egress_type == TYPE_EGRESS_SWITCH) {
                    //更新ipv4固定首部
                    hdr.ipv4.ihl = hdr.ipv4.ihl + 8;                //ipv4_option_t + flowinfo_t 的总长度为256bit（8个双字）
                    hdr.ipv4.totalLen = hdr.ipv4.totalLen + 32;     //256 bits = 32 bytes
                    //插入ipv4的可选字段（基础部分）
                    hdr.ipv4_option.setValid();
                    hdr.ipv4_option.optionLength = 32;              //256 bits = 32 bytes
                    hdr.ipv4_option.option = TYPE_FLOWINFO;
                    //将flowinfo插入ipv4的可选字段
                    hdr.flowinfo.setValid();
                    hdr.flowinfo.padding = 0;
                    hdr.flowinfo.ingress_ts = 0;
                    hdr.flowinfo.egress_ts = 0;
                    hdr.flowinfo.enq_qdepth = 0;
                    hdr.flowinfo.deq_qdepth = 0;
                    hdr.flowinfo.ipv4_srcAddr = hdr.ipv4.srcAddr;
                    hdr.flowinfo.ipv4_dstAddr = hdr.ipv4.dstAddr;
                    hdr.flowinfo.tcp_sport = hdr.tcp.srcPort;
                    hdr.flowinfo.tcp_dport = hdr.tcp.dstPort;
                    hdr.flowinfo.protocol = hdr.ipv4.protocol;
                }
            }
            
        }
    }
}

/** Egress处理 **/
control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {    
    apply {
        if (hdr.flowinfo.isValid()){
            hdr.flowinfo.ingress_ts = standard_metadata.ingress_global_timestamp;
            hdr.flowinfo.egress_ts = standard_metadata.egress_global_timestamp;
            //hdr.flowinfo.enq_qdepth = standard_metadata.enq_qdepth;
            hdr.flowinfo.enq_qdepth = hdr.flowinfo.enq_qdepth + 1;      //【TODO】迭代交换机序号
            hdr.flowinfo.deq_qdepth = standard_metadata.deq_qdepth;     //更新出队列深度
            if (hdr.flowinfo.deq_qdepth > THRESHOLD){
                hdr.flowinfo.padding = (bit<2>)hdr.flowinfo.enq_qdepth; //【TODO】记录发生Microburst的交换机
            }
        }
    }
}

/** Checksum计算（调用时期：egress后、deparser前） **/
control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
        update_checksum(
            hdr.ipv4.isValid(), //前提条件是 header 格式正确
            { 
                hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.dscp,
                hdr.ipv4.ecn,
                hdr.ipv4.totalLen,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.fragOffset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr 
            },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/** 交换机架构 **/
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;