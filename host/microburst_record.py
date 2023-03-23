#!/usr/bin/env python3
import sys
import os, time
import csv
from flowinfo import *
from scapy.all import sniff, get_if_list, get_if_hwaddr
from scapy.all import Ether, IP, UDP, TCP, Raw, ls

curdate = time.strftime("%m%d_%H", time.localtime())
fa_dir = 'log'
output_file = fa_dir + '/%s.csv' % curdate
ts_list, qdepth_list = [], []

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
        # print_flowinfo(pkt)
        record_depth(pkt, tscale = 100)
        sys.stdout.flush()

def print_flowinfo(pkt, selected = False):
    if FLOWINFO in pkt:
        print(pkt[FLOWINFO].deq_qdepth)

def record_depth(pkt, tscale = 100):
    if FLOWINFO not in pkt:
        return
    if pkt[FLOWINFO].egress_ts % tscale != 0:
        return
    qdepth_list.append(pkt[FLOWINFO].deq_qdepth)
    ts_list.append(pkt[FLOWINFO].egress_ts)

    if pkt[FLOWINFO].egress_ts % (tscale * 1000) == 0:
        with open(output_file, mode='a') as file:
            writer = csv.writer(file)
            writer.writerows(zip(ts_list, qdepth_list))
        ts_list.clear()
        qdepth_list.clear()

def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    
    sys.stdout.flush()                      # 显式地让缓冲区的内容输出

    if not os.path.exists('fa_dir'):
        os.makedirs(fa_dir)

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp(us)', 'Queue Length(number of packets)'])

    sniff(iface = iface,      # 指定要在哪个网络接口上进行抓包
          prn = lambda x: handle_pkt(x))    #每当一个符合filter的报文被探测到时，就会执行回调函数

if __name__ == '__main__':
    main()