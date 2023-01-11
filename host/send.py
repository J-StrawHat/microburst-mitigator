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

    payload = "7"*1446	
    pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff') /IP(dst=addr, options=[FLOWINFO()]) / TCP(dport=60000, sport=60001) / payload 

    print("sending pacekets (%s:%s -> %s:%s)" % (pkt.getlayer(IP).src, pkt.getlayer(TCP).sport, pkt.getlayer(IP).dst, pkt.getlayer(TCP).dport))
    pkt.show()
    print()
    sendpfast(pkt, pps=int(sys.argv[2]), loop=int(sys.argv[3]))


if __name__ == '__main__':
    main()