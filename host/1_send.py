#!/usr/bin/env python3
import argparse
import sys
import socket
import random
import struct
import time
from flowinfo import *
from scapy.all import send, sendp, sendpfast, get_if_list, get_if_hwaddr, RandInt, RandShort
from scapy.all import Ether, IP, TCP, Raw, srp
from datetime import datetime
import os

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

class T():
    seq = 1

def send_packets(src_mac, dst_mac, dst_ip, src_port, dst_port, bandwidth):
    
    # 构造TCP SYN报文
    syn_pkt = Ether(src=src_mac, dst=dst_mac)/IP(dst=dst_ip)/TCP(sport=src_port, dport=dst_port, flags='S')

    # 发送SYN报文并接收对应的SYN+ACK报文
    syn_ack_pkt = srp(syn_pkt)
    if syn_ack_pkt is None:
        print("Error: No SYN+ACK received!")
        return
    else:
        print("Success: SYN+ACK received ")


    # 发送SYN报文并接收对应的SYN+ACK报文
    answered, unanswered = srp(syn_pkt)
    if answered:
        print("Success: SYN+ACK received ")
        # 对于每个元组，第一个元素是发送的数据包，第二个元素是接收到的响应帧
        syn_ack_pkt = answered[0][1]
    else:
        print("Error: No SYN+ACK received!")
    

    # 构造TCP ACK报文
    ack_pkt = Ether(src=src_mac, dst=dst_mac)/IP(dst=dst_ip)/TCP(sport=src_port, dport=dst_port, flags='A', seq=syn_ack_pkt.ack, ack=syn_ack_pkt.seq + 1)

    # 发送TCP ACK数据包
    sendp(ack_pkt)

    # 计算发送间隔和每次发送的数据大小
    pkt_size = 1024
    delay = float(pkt_size * 8) / bandwidth

    # 发送数据包
    total_size = 0
    start_time = datetime.now()
    while total_size < 5 * 1024 * 1024:
        payload = os.urandom(pkt_size - 20)
        pkt = Ether(src=src_mac, dst=dst_mac)/IP(dst=dst_ip)/TCP(sport=src_port, dport=dst_port, flags='', seq=ack_pkt.seq, ack=syn_ack_pkt.seq + 1)/payload
        
        sendpfast(pkt, mbps=bandwidth, loop=0)
        
        ack_pkt.seq += len(payload)
        total_size += len(payload)
        print(total_size)
        # time.sleep(delay)

    # 构造TCP FIN报文
    fin_pkt = Ether(src=src_mac, dst=dst_mac)/IP(dst=dst_ip)/TCP(sport=src_port, dport=dst_port, flags='FA', seq=ack_pkt.seq, ack=syn_ack_pkt.seq + 1)

    # 发送FIN报文并接收对应的ACK报文
    ack_pkt = srp(fin_pkt)

    # 计算发送时间和吞吐量
    end_time = datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()
    throughput = total_size / elapsed_time
    print(f"Elapsed time: {elapsed_time:.3f}s, Throughput: {throughput/1024/1024:.3f}Mbps")

iface = get_if()
send_packets(get_if_hwaddr(iface), 'ff:ff:ff:ff:ff:ff', '10.2.3.2', 5000, 5001, 20)