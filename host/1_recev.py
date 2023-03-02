#!/usr/bin/env python3
import sys
import os, time
from flowinfo import *
from scapy.all import sniff, get_if_list, get_if_hwaddr
from scapy.all import Ether, IP, UDP, TCP, Raw, ls

from collections import Counter


def sniff_packets(src_ip, dst_ip, src_port, dst_port):
    # 过滤表达式
    filter_str = 'tcp and src host {0} and dst host {1} and src port {2} and dst port {3}'.format(src_ip, dst_ip, src_port, dst_port)

    # 过滤出源IP和目的IP匹配，源端口和目的端口匹配，TCP标志为PUSH+ACK的TCP报文
    # filter_str = f"tcp and src host {src_ip} and dst host {dst_ip} and src port {src_port} and dst port {dst_port} "
    # and tcp[tcpflags] & tcp-push != 0 and tcp[tcpflags] & tcp-ack != 0
    # 开始嗅探数据包
    pkts = sniff(filter=filter_str, timeout=60)

    # 统计重传次数
    total_packets = len(pkts)
    retransmit_packets = total_packets - len(set(pkt[TCP].seq for pkt in pkts))
    retransmit_rate = retransmit_packets / total_packets
    print(f"Retransmit rate: {retransmit_rate:.3f}, Total packets: {total_packets}")

sniff_packets('10.1.1.2', '10.2.3.2', 5000, 5001)

'''
tcp[tcpflags] & (tcp-rst|tcp-ack) == (tcp-rst|tcp-ack)

'''