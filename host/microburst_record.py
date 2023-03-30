#!/usr/bin/env python3
import sys
import os, time
import csv
from flowinfo import *
from scapy.all import sniff, get_if_list, get_if_hwaddr
from scapy.all import Ether, IP, UDP, TCP, Raw, ls

curdate = time.strftime("%m%d-%H-%M", time.localtime())
fa_dir = 'host/log'
output_file = fa_dir + '/%s.csv' % curdate

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
    if IP in pkt:
        #print_flowinfo(pkt)
        record_depth(pkt, tscale = 1)
        sys.stdout.flush()

def print_flowinfo(pkt, selected = False):
    if FLOWINFO in pkt:
        print(pkt[FLOWINFO].deq_qdepth)
    

def record_depth(pkt, tscale = 100):
    if FLOWINFO not in pkt:
        return
    if pkt[FLOWINFO].egress_ts % tscale != 0:
        return

    print("%d,%d,%d" % (pkt[FLOWINFO].egress_ts, pkt[FLOWINFO].deq_qdepth, len(pkt)))

    with open(output_file, mode='a') as file:
        writer = csv.writer(file)
        writer.writerow((pkt[FLOWINFO].egress_ts, pkt[FLOWINFO].deq_qdepth))


def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    #print("sniffing on %s" % iface)
    
    sys.stdout.flush()                      # 显式地让缓冲区的内容输出

    if not os.path.exists(fa_dir):
        os.makedirs(fa_dir)

    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp(us)', 'Queue Depth(number of packets)'])
    
    #print("timestamp(us),Queue Length(number of packets)")

    sniff(iface = iface,      # 指定要在哪个网络接口上进行抓包
          prn = lambda x: handle_pkt(x))    #每当一个符合filter的报文被探测到时，就会执行回调函数

if __name__ == '__main__':
    main()