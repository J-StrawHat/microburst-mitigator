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
    
    register<bit<9>>(1) tmp_recorder;
    register<bit<9>>(1) tmp_recorder_2;
    register<macAddr_t>(8) port_recorder;
    

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;    //到达新目标，更新源MAC地址
        hdr.ethernet.dstAddr = dstAddr;                 //查表可得到下一跳的目标Mac地址
        standard_metadata.egress_spec = port;           //查表得到输出端口
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;                //更新TTL
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

    apply {
        if (hdr.ipv4.isValid()){
            ipv4_lpm.apply();
            tmp_recorder.read(meta.tmp_cnt, 0);
            meta.tmp_cnt = meta.tmp_cnt + 1;
            tmp_recorder.write((bit<32>)0, meta.tmp_cnt);
            bit<1> notice = meta.notice + 1;
            bit<9> inst_type = (bit<9>)standard_metadata.instance_type;
            if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_RECIRC){
                tmp_recorder_2.write((bit<32>)0, inst_type);
            }
            tmp_recorder_2.read(inst_type, 0);
        }
    }
}

/** Egress处理 **/
control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {    
    action egress_drop() {
        mark_to_drop(standard_metadata);
    }
    apply {
        if (meta.tmp_cnt == 4){ //当前状态本来是正常转发，但是出队列深度超出阈值
            clone(CloneType.E2E, 100);
        }
        else if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_EGRESS_CLONE){
            meta.notice = 1;
            recirculate_preserving_field_list((bit<8>)FieldLists.recir_fl);
        }
        if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_RECIRC){
            bit<1> t = 0;
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