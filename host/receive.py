#!/usr/bin/env python3
import sys
import os
from flowinfo import *
from scapy.all import sniff, get_if_list, get_if_hwaddr
from scapy.all import Ether, IP, UDP, TCP, Raw, ls

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
    print("Packet Received:")
    pkt.show()
#    hexdump(pkt)
    sys.stdout.flush()
    print()

def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(filter="tcp", iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()