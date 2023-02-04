#!/usr/bin/env python3
import sys
import os
from flowinfo import *
from scapy.all import sniff, get_if_list, get_if_hwaddr
from scapy.all import Ether, IP, UDP, TCP, Raw, ls

pkt_cnt = 0

def get_if():
    iface=None
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

def handle_pkt(pkt):
    global pkt_cnt
    pkt_cnt = pkt_cnt + 1
    ip = pkt.getlayer(IP)
    # flow_info = ip.options[0]

    tcp = pkt.getlayer(TCP)
    # msg = tcp.payload.load.decode('UTF-8') 【TODO】iperf工具似乎不带load
    # if flow_info.padding != 0:
    print("%sth Packet Received: (%s:%s -> %s:%s)" % (pkt_cnt, ip.src, tcp.sport, ip.dst, tcp.dport))
    # flow_info.show()
    # ip.show()
    sys.stdout.flush()
    print()

def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    
    tmp = IP(dst = '10.1.1.2')
    sys.stdout.flush()                      # 显式地让缓冲区的内容输出
    sniff(filter="ip dst " + tmp.src, iface = iface,      # 指定要在哪个网络接口上进行抓包
          prn = lambda x: handle_pkt(x))    #每当一个符合filter的报文被探测到时，就会执行回调函数

if __name__ == '__main__':
    main()