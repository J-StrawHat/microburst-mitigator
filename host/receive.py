#!/usr/bin/env python3
import sys
import os, time
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
    if IP in pkt:
        pkt_cnt = pkt_cnt + 1
        ip_src, ip_dst = pkt[IP].src, pkt[IP].dst
        if TCP in pkt:
            sport, dport, flags = pkt[TCP].sport, pkt[TCP].dport, pkt[TCP].flags
            print("%sth Packet Received: (%s:%s -> %s:%s) - %s " % (pkt_cnt, ip_src, sport, ip_dst, dport, flags))
            if flags == 'F': # 如果是流的最后一个数据包
                flow_time = pkt.time
                print("[!] Flow from %s:%d to %s:%d completed in %f seconds" % (ip_src, sport, ip_dst, dport, flow_time))
            if flags == 0x01:
                print(time.time())
                pkt[TCP].show()

        #print_flowinfo(pkt)
        

        # msg = tcp.payload.load.decode('UTF-8') 【TODO】iperf工具似乎不带load

        sys.stdout.flush()
        print()

def print_flowinfo(pkt, selected = False):
    if FLOWINFO in pkt:
        if selected:
            if pkt[FLOWINFO].padding != 0:
                pkt[FLOWINFO].show()
        else:
            pkt[FLOWINFO].show()

def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    
    sys.stdout.flush()                      # 显式地让缓冲区的内容输出
    sniff(iface = iface,      # 指定要在哪个网络接口上进行抓包
          prn = lambda x: handle_pkt(x))    #每当一个符合filter的报文被探测到时，就会执行回调函数

if __name__ == '__main__':
    main()