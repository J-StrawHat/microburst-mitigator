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
    //write(in bit<32> index, in T value);
    //read(out T result, in bit<32> index);
    register<bit<9>>(1)         port_num_recorder;  //记录当前交换机有多少个端口
    register<bit<32>>(FLOW_NUM) deflect_idx_table;  //记录不同流当前已分配的偏转ID  
    register<bit<32>>(FLOW_NUM) reorder_idx_table;  //记录不同流「下一个」需恢复的偏转ID 
    //register<bit<2>>(1)         status_recorder;    //记录当前交换机的偏转模式(0→1→2)
    //register<bit<9>>(1)         tmp_recorder; 
    register<bit<19>>(PORT_NUM) qdepth_table;       //记录邻居交换机的深度情况（注意，端口0是连接Thrift服务器的）
    register<bit<1>>(PORT_NUM)  port_type_recorder; //记录各端口所连接的节点类型
    register<bit<9>>(PORT_NUM)  last_port_table;    //上一个策略所选用的端口
    bit<19>                     cur_deq_qdepth;
    bit<19>                     min_deq_qdepth;
    bit<9>                      min_deq_dqdepth_idx;
    bit<2>                      cur_status = 0;
    bit<32>                     cur_deflect_idx = 0;
    bit<32>                     cur_reorder_idx = 0;
    bit<1>                      deflect_flag = 0;

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;    //到达新目标，更新源MAC地址
        hdr.ethernet.dstAddr = dstAddr;                 //查表可得到下一跳的目标Mac地址
        standard_metadata.egress_spec = port;           //查表得到输出端口
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;                //更新TTL
    }

    action set_egress_type (bit<1> egress_type){
        meta.egress_type = egress_type;
    }

    action get_random_port_with_type(){
        //需要已知port_nums
        random(meta.tmp_port, 9w1, meta.port_nums);
        port_type_recorder.read(meta.port_type, (bit<32>)meta.tmp_port);
    }

    action get_random_switch_port(){
        get_random_port_with_type();
        if(meta.port_type != TYPE_EGRESS_SWITCH){
            get_random_port_with_type();
        }
        if(meta.port_type != TYPE_EGRESS_SWITCH){
            get_random_port_with_type();
        }
        if(meta.port_type != TYPE_EGRESS_SWITCH){
            get_random_port_with_type();
        }
        if(meta.port_type != TYPE_EGRESS_SWITCH){
            get_random_port_with_type();
        }
        if(meta.port_type != TYPE_EGRESS_SWITCH){
            get_random_port_with_type();
        }
        if(meta.port_type != TYPE_EGRESS_SWITCH){
            get_random_port_with_type();
        }
        if(meta.port_type != TYPE_EGRESS_SWITCH){
            get_random_port_with_type();
        }
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
                //从「深度记录表」中读出当前出端口的队列深度，并存放到cur_deq_qdepth
                qdepth_table.read(cur_deq_qdepth, (bit<32>)standard_metadata.egress_spec);
                //读出当前交换机的端口数量（边界）
                port_num_recorder.read(meta.port_nums, 0);
                //读出当前交换机已分配、已恢复的偏转ID
                deflect_idx_table.read(cur_deflect_idx, (bit<32>)hdr.flowinfo.flow_id);
                reorder_idx_table.read(cur_reorder_idx, (bit<32>)hdr.flowinfo.flow_id);
                //确定当前的转换状态
                if(cur_deflect_idx == 0 && cur_reorder_idx == 0){
                    cur_status = 0;
                    if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_RECIRC && DEFLECTION_MODE != 0){
                        cur_status = 1;         //深度超出阈值，需要进行偏转
                    }
                    else {
                        cur_status = 0;
                    }
                }
                else if(cur_deflect_idx != 0 && cur_reorder_idx == 0){
                    if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_RECIRC){
                        cur_status = 2;         //深度变浅了，准备停止偏转
                    }
                    else {
                        cur_status = 1;
                    }
                }
                else if(cur_deflect_idx != 0 && cur_reorder_idx != 0){
                    cur_status = 2;
                }
            
                if(cur_status == 1){
                    if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_RECIRC){
                        //流状态已经切换到「偏转」，当前的预警包需要在ingress结尾丢弃
                        //此时 deflect_idx = 0
                        drop();
                    }
                    else if (hdr.flowinfo.deflect_idx == 0){
                        //如果当前数据包未被分配过偏转ID，则需要从寄存器中分配一个偏转ID给当前数据包
                        hdr.flowinfo.deflect_idx = cur_deflect_idx;
                    }
                    cur_deflect_idx = cur_deflect_idx + 1;
                    //更新记录表上的最新偏转ID
                    deflect_idx_table.write((bit<32>)hdr.flowinfo.flow_id, cur_deflect_idx);
                }
                else if (cur_status == 2){
                    if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_RECIRC){
                        //此时 reorder_idx = 0
                        drop();
                        //更新「下一个」待恢复（待匹配）的偏转ID
                        cur_reorder_idx = cur_reorder_idx + 1;
                        reorder_idx_table.write((bit<32>)hdr.flowinfo.flow_id, cur_reorder_idx);
                    }
                    else if(cur_reorder_idx != hdr.flowinfo.deflect_idx){
                        //两偏转ID不匹配，需要将包进行偏转
                        deflect_flag = 1;
                        if(hdr.flowinfo.deflect_idx == 0){
                            //如果当前数据包未被分配过偏转ID，则从寄存器中分配一个偏转ID：
                            hdr.flowinfo.deflect_idx = cur_deflect_idx;
                            //更新记录表上的最新偏转ID
                            cur_deflect_idx = cur_deflect_idx + 1;
                            deflect_idx_table.write((bit<32>)hdr.flowinfo.flow_id, cur_deflect_idx);               
                        }
                    }
                    else { //包所携带的偏转ID和待恢复的ID匹配（说明符合流的包次序）
                        deflect_flag = 0; //当前的数据包不需偏转

                        //更新「下一个」待恢复的偏转ID
                        cur_reorder_idx = cur_reorder_idx + 1;                        
                        if(cur_deflect_idx == cur_reorder_idx){ //待分配的偏转ID，和待恢复(匹配)的偏转ID相等
                            //说明偏转的数据包已全部被恢复到原次序
                            deflect_idx_table.write((bit<32>)hdr.flowinfo.flow_id, 0);
                            reorder_idx_table.write((bit<32>)hdr.flowinfo.flow_id, 0);
                            cur_status = 0; //转换状态
                            hdr.flowinfo.deflect_idx = 0; //匹配即可去掉deflect_id
                        }
                        else {
                            reorder_idx_table.write((bit<32>)hdr.flowinfo.flow_id, cur_reorder_idx);
                        }

                    }
                }

                if(cur_status == 1 || deflect_flag == 1){     //即将出的端口，比较拥塞
                    if (DEFLECTION_MODE == 1){      //Random Deflection

                        get_random_port_with_type();
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }

                        standard_metadata.egress_spec = meta.tmp_port;
                    }
                    else if(DEFLECTION_MODE == 2){  //Selective Deflection                      
                        //随机选出一个端口 a
                        get_random_port_with_type();
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        qdepth_table.read(min_deq_qdepth, (bit<32>)meta.tmp_port);
                        min_deq_dqdepth_idx = meta.tmp_port;
                        
                        //随机选出一个端口 b
                        get_random_port_with_type();
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        if(meta.port_type != TYPE_EGRESS_SWITCH){
                            get_random_port_with_type();
                        }
                        qdepth_table.read(cur_deq_qdepth, (bit<32>)meta.tmp_port);
                        if(min_deq_qdepth > cur_deq_qdepth){
                            min_deq_qdepth = cur_deq_qdepth;
                            min_deq_dqdepth_idx = meta.tmp_port;
                        }

                        //查询上一个决策所使用的端口 c
                        last_port_table.read(meta.tmp_port, (bit<32>)standard_metadata.egress_spec);
                        if(meta.tmp_port != 0){ //如果历史端口为0，说明从未做出决策
                            qdepth_table.read(cur_deq_qdepth, (bit<32>)meta.tmp_port);
                            if(min_deq_qdepth > cur_deq_qdepth){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = meta.tmp_port;
                            }
                        }
                        
                        //更新历史端口相关信息
                        last_port_table.write((bit<32>)standard_metadata.egress_spec, min_deq_dqdepth_idx);
                        standard_metadata.egress_spec = min_deq_dqdepth_idx;
                    }
                    else if(DEFLECTION_MODE == 3){ // 假定有8个端口
                        min_deq_qdepth = 524287;
                        min_deq_dqdepth_idx = 0;
                        //检查端口1
                        qdepth_table.read(cur_deq_qdepth, 1); 
                        port_type_recorder.read(meta.port_type, 1);
                        if(min_deq_qdepth > cur_deq_qdepth && meta.port_type == TYPE_EGRESS_SWITCH){
                            min_deq_qdepth = cur_deq_qdepth;
                            min_deq_dqdepth_idx = 1;
                        }
                        if(meta.port_nums > 2){ //检查端口2
                            qdepth_table.read(cur_deq_qdepth, 2);
                            port_type_recorder.read(meta.port_type, 2);
                            if(min_deq_qdepth > cur_deq_qdepth && meta.port_type == TYPE_EGRESS_SWITCH){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 2;
                            }
                        }
                        if(meta.port_nums > 3){ //检查端口3
                            qdepth_table.read(cur_deq_qdepth, 3);
                            port_type_recorder.read(meta.port_type, 3);
                            if(min_deq_qdepth > cur_deq_qdepth && meta.port_type == TYPE_EGRESS_SWITCH){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 3;
                            }
                        }
                        if(meta.port_nums > 4){ //检查端口4
                            qdepth_table.read(cur_deq_qdepth, 4);
                            port_type_recorder.read(meta.port_type, 4);
                            if(min_deq_qdepth > cur_deq_qdepth && meta.port_type == TYPE_EGRESS_SWITCH){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 4;
                            }
                        }
                        if(meta.port_nums > 5){ //检查端口5
                            qdepth_table.read(cur_deq_qdepth, 5);
                            port_type_recorder.read(meta.port_type, 5);
                            if(min_deq_qdepth > cur_deq_qdepth && meta.port_type == TYPE_EGRESS_SWITCH){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 5;
                            }
                        }
                        if(meta.port_nums > 6){ //检查端口6
                            qdepth_table.read(cur_deq_qdepth, 6);
                            port_type_recorder.read(meta.port_type, 6);
                            if(min_deq_qdepth > cur_deq_qdepth && meta.port_type == TYPE_EGRESS_SWITCH){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 6;
                            }
                        }
                        if(meta.port_nums > 7){ //检查端口7
                            qdepth_table.read(cur_deq_qdepth, 7);
                            port_type_recorder.read(meta.port_type, 7);
                            if(min_deq_qdepth > cur_deq_qdepth && meta.port_type == TYPE_EGRESS_SWITCH){
                                min_deq_qdepth = cur_deq_qdepth;
                                min_deq_dqdepth_idx = 7;
                            }
                        }
                        standard_metadata.egress_spec = min_deq_dqdepth_idx;
                    }
                }
                port_type_recorder.read(meta.port_type, (bit<32>)standard_metadata.egress_spec);
                if (SHOW_FLOWINFO && meta.port_type == TYPE_EGRESS_HOST){
                    clone(CloneType.I2E, 100);
                }
            }
            else {
                port_type_recorder.read(meta.port_type, (bit<32>)standard_metadata.egress_spec);
                //如果下一跳是交换机并且是「刚刚从主机出发」，则将Flowinfo首部嵌入到数据包中
                if (meta.port_type == TYPE_EGRESS_SWITCH) {
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
            
            meta.cur_status = cur_status;
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
        if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_EGRESS_CLONE){
            meta.notice = 1;
            recirculate_preserving_field_list((bit<8>)FieldLists.recir_fl);
            egress_drop(); 
        }
        else if (hdr.flowinfo.isValid()){
            hdr.flowinfo.egress_ts = standard_metadata.egress_global_timestamp;
            //hdr.flowinfo.deflect_idx = hdr.flowinfo.deflect_idx + 1;        //【TODO】迭代交换机序号
            hdr.flowinfo.deq_qdepth = standard_metadata.deq_qdepth;         //更新出队列深度

            if (standard_metadata.deq_qdepth > THRESHOLD && meta.cur_status == 0){ //当前状态本来是正常转发，但是出队列深度超出阈值
                clone(CloneType.E2E, 100);
            }
            else if (standard_metadata.deq_qdepth <= THRESHOLD && meta.cur_status == 1){ //当前状态本来是转发，但是出队列深度超出阈值
                clone(CloneType.E2E, 100);
            }

            if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_NORMAL && meta.port_type == TYPE_EGRESS_HOST ){    //如果下一跳是主机，说明将要结束
                hdr.ipv4.ihl = hdr.ipv4.ihl - 5;                //ipv4_option_t + flowinfo_t 的总长度为256bit（8个双字）
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 20;     //256 bits = 32 bytes
                hdr.ipv4_option.setInvalid();
                hdr.flowinfo.setInvalid();
            }
            else if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE){
                //对于ingress克隆的数据包，不需要剔除flowinfo首部
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