/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

//My includes
#include "include/headers.p4"
#include "include/parsers.p4"
#define SHOW_FLOWINFO false
#define DEFLECTION_MODE 0       //0:不偏转; 1:随机偏转; 2:随机选2个取局部最小值; 3:遍历取全局最小值

/** Checksum的验证阶段(每收到一个包均需验证checksum，以确保该包是完整的没被修改过的) **/
control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/** Ingress处理 **/
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    //write(in bit<32> index, in T value);
    //read(out T result, in bit<32> index);
    register<bit<9>>(1)         port_num_recorder; //记录当前交换机有多少个端口
    //register<bit<9>>(1)         tmp_recorder; 
    register<bit<19>>(PORT_NUM) qdepth_table; //记录邻居交换机的深度情况（注意，端口0是连接Thrift服务器的）
    register<bit<19>>(2)        min_qdepth_recorder;
    bit<19>                     cur_deq_qdepth;
    bit<19>                     min_deq_qdepth;
    bit<9>                      min_deq_dqdepth_idx;
    bit<9>                      tmp_port;

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

            if (hdr.tcp.isValid()){
                meta.src_port = hdr.tcp.srcPort;
                meta.dst_port = hdr.tcp.dstPort;
            }
            else if (hdr.udp.isValid()){
                meta.src_port = hdr.udp.srcPort;
                meta.dst_port = hdr.udp.dstPort;
            }

            if (hdr.flowinfo.isValid()){
                //将入端口的队列深度（告知其他邻近的交换机的队列深度）记录到「深度记录表」中
                qdepth_table.write((bit<32>)standard_metadata.ingress_port, hdr.flowinfo.deq_qdepth);
                //读出并维护最小深度
                min_qdepth_recorder.read(min_deq_qdepth, 1);
                if (min_deq_qdepth >= hdr.flowinfo.deq_qdepth) {
                    min_qdepth_recorder.write(0, (bit<19>)standard_metadata.ingress_port);  //更新端口号
                    min_qdepth_recorder.write(1, hdr.flowinfo.deq_qdepth);                  //更新深度
                    min_deq_qdepth = hdr.flowinfo.deq_qdepth;                               //更新临时变量
                }
                //从「深度记录表」中读出当前出端口的队列深度，并存放到cur_deq_qdepth
                qdepth_table.read(cur_deq_qdepth, (bit<32>)standard_metadata.egress_port);
                //读出当前交换机的端口数量（边界）
                port_num_recorder.read(meta.port_nums, 0);
                if(cur_deq_qdepth > THRESHOLD){     //即将出的端口，比较拥塞
                    if (DEFLECTION_MODE == 1){      //Random Deflection
                        random(tmp_port, 9w1, meta.port_nums);
                        //tmp_recorder.write(0, tmp_port); Debug使用
                        standard_metadata.egress_spec = tmp_port;
                    }
                    else if(DEFLECTION_MODE == 2){  //Selective Deflection
                        min_deq_qdepth = cur_deq_qdepth;
                        min_deq_dqdepth_idx = standard_metadata.egress_port;
                        random(tmp_port, 9w1, meta.port_nums);
                        qdepth_table.read(cur_deq_qdepth, (bit<32>)tmp_port);
                        if(min_deq_qdepth > cur_deq_qdepth){
                            min_deq_qdepth = cur_deq_qdepth;
                            min_deq_dqdepth_idx = tmp_port;
                        }
                        random(tmp_port, 9w1, meta.port_nums);
                        qdepth_table.read(cur_deq_qdepth, (bit<32>)tmp_port);
                        if(min_deq_qdepth > cur_deq_qdepth){
                            min_deq_qdepth = cur_deq_qdepth;
                            min_deq_dqdepth_idx = tmp_port;
                        }
                        standard_metadata.egress_spec = min_deq_dqdepth_idx;
                    }
                    else if(DEFLECTION_MODE == 3){ // 假定有8个端口
                        min_deq_qdepth = cur_deq_qdepth;
                        min_deq_dqdepth_idx = standard_metadata.egress_port;
                        qdepth_table.read(cur_deq_qdepth, 1);
                        if(min_deq_qdepth > cur_deq_qdepth){
                            min_deq_qdepth = cur_deq_qdepth;
                            min_deq_dqdepth_idx = 1;
                        }
                        if(meta.port_nums > 2){
                            qdepth_table.read(cur_deq_qdepth, 2);
                            if(min_deq_qdepth > cur_deq_qdepth){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 2;
                            }
                        }
                        if(meta.port_nums > 3){
                            qdepth_table.read(cur_deq_qdepth, 3);
                            if(min_deq_qdepth > cur_deq_qdepth){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 3;
                            }
                        }
                        if(meta.port_nums > 4){
                            qdepth_table.read(cur_deq_qdepth, 4);
                            if(min_deq_qdepth > cur_deq_qdepth){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 4;
                            }
                        }
                        if(meta.port_nums > 5){
                            qdepth_table.read(cur_deq_qdepth, 5);
                            if(min_deq_qdepth > cur_deq_qdepth){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 5;
                            }
                        }
                        if(meta.port_nums > 6){
                            qdepth_table.read(cur_deq_qdepth, 6);
                            if(min_deq_qdepth > cur_deq_qdepth){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 6;
                            }
                        }
                        if(meta.port_nums > 7){
                            qdepth_table.read(cur_deq_qdepth, 7);
                            if(min_deq_qdepth > cur_deq_qdepth){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 7;
                            }
                        }
                        standard_metadata.egress_spec = min_deq_dqdepth_idx;
                    }
                }

            }
            else {
                
                //如果下一跳是交换机并且是「刚刚从主机出发」，则将Flowinfo首部嵌入到数据包中
                if (meta.egress_type == TYPE_EGRESS_SWITCH) {
                    //更新ipv4固定首部
                    hdr.ipv4.ihl = hdr.ipv4.ihl + 5;                //ipv4_option_t + flowinfo_t 的总长度为256bit（8个双字）
                    hdr.ipv4.totalLen = hdr.ipv4.totalLen + 20;     //256 bits = 32 bytes
                    //插入ipv4的可选字段（基础部分）
                    hdr.ipv4_option.setValid();
                    hdr.ipv4_option.optionLength = 20;              //256 bits = 32 bytes
                    hdr.ipv4_option.option = TYPE_FLOWINFO;
                    //将flowinfo插入ipv4的可选字段
                    hdr.flowinfo.setValid();

                    hash(hdr.flowinfo.flow_id,
                        HashAlgorithm.crc16,
                        (bit<1>)0,
                        {
                            hdr.ipv4.dstAddr,
                            hdr.ipv4.srcAddr,
                            meta.src_port,
                            meta.dst_port,
                            hdr.ipv4.protocol
                        },
                        (bit<12>)FLOW_NUM); //哈希得到flow-id

                    hdr.flowinfo.egress_ts = 0;
                    hdr.flowinfo.deq_qdepth = 0;
                    hdr.flowinfo.deflect_idx = 0;
                    hdr.flowinfo.padding = 0;
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
            hdr.flowinfo.egress_ts = standard_metadata.egress_global_timestamp;
            hdr.flowinfo.deflect_idx = hdr.flowinfo.deflect_idx + 1;        //【TODO】迭代交换机序号
            hdr.flowinfo.deq_qdepth = standard_metadata.deq_qdepth;         //更新出队列深度

            if (!SHOW_FLOWINFO && meta.egress_type == TYPE_EGRESS_HOST){    //如果下一跳是主机，说明将要结束
                hdr.ipv4.ihl = hdr.ipv4.ihl - 5;                //ipv4_option_t + flowinfo_t 的总长度为256bit（8个双字）
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 20;     //256 bits = 32 bytes
                hdr.ipv4_option.setInvalid();
                hdr.flowinfo.setInvalid();
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