#!/usr/bin/env python3
import argparse
import sys
import socket
import random
import struct
import time
from flowinfo import *
from scapy.all import sendp, sendpfast, get_if_list, get_if_hwaddr
from scapy.all import Ether, IP, TCP

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

def main():
    if len(sys.argv)<3:
        print('pass 2 arguments: <destination> <pps> <loop>"')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    for i in range(int(sys.argv[2])):
        payload = str(i) * 100
        pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff') /IP(dst=addr) / TCP(dport=60000, sport=60001) / payload 
        print("sending %sth pacekets (%s:%s -> %s:%s)" % (i, pkt.getlayer(IP).src, pkt.getlayer(TCP).sport, pkt.getlayer(IP).dst, pkt.getlayer(TCP).dport))
        pkt.show2()
        print()
        sendp(pkt, iface=iface)


if __name__ == '__main__':
    main()