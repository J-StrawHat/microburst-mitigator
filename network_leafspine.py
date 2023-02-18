from mininet.log import lg, info
from mininet.util import pmonitor
from p4utils.mininetlib.network_API import NetworkAPI
import subprocess
import os, sys, re

def init_topology(network_api):
    # Network general options
    network_api.setLogLevel('info')
    network_api.execScript('python routing-controller.py', reboot=True)

    # Network definition
    network_api.addP4Switch('s1')
    network_api.addP4Switch('s2')
    network_api.addP4Switch('s3')
    network_api.addP4Switch('s4')
    network_api.addP4Switch('s5')
    network_api.addP4Switch('s6')
    network_api.addP4Switch('s7')
    network_api.setP4SourceAll('p4src/microburst_mitigator.p4')

    network_api.addHost('h1')
    network_api.addHost('h2')
    network_api.addHost('h3')
    network_api.addHost('h4')
    network_api.addHost('h5')
    network_api.addHost('h6')
    network_api.addHost('h7')
    network_api.addHost('h8')

    # Leaf
    network_api.addLink("h1", "s1")
    network_api.addLink("h2", "s1")
    network_api.addLink("h3", "s2")
    network_api.addLink("h4", "s2")
    network_api.addLink("h5", "s3")
    network_api.addLink("h6", "s3")
    network_api.addLink("h7", "s4")
    network_api.addLink("h8", "s4")

    # Spine 
    network_api.addLink("s1", "s5")
    network_api.addLink("s2", "s5")
    network_api.addLink("s4", "s5")

    network_api.addLink("s2", "s6")
    network_api.addLink("s3", "s6")
    network_api.addLink("s4", "s6")

    network_api.addLink("s2", "s7")
    network_api.addLink("s4", "s7")

    # Sets links bandwidth
    network_api.setBw("h1", "s1", 100)
    network_api.setBw("h2", "s1", 100)
    network_api.setBw("h3", "s2", 100)
    network_api.setBw("h4", "s2", 100)
    network_api.setBw("h5", "s3", 100)
    network_api.setBw("h6", "s3", 100)
    network_api.setBw("h7", "s4", 100)
    network_api.setBw("h8", "s4", 100)

    network_api.setBw("s1", "s5", 400)
    network_api.setBw("s2", "s5", 400)
    network_api.setBw("s4", "s5", 400)
    network_api.setBw("s2", "s6", 400)
    network_api.setBw("s3", "s6", 400)
    network_api.setBw("s4", "s6", 400)
    network_api.setBw("s2", "s7", 400)
    network_api.setBw("s4", "s7", 400)

    # Assignment strategy
    network_api.l3()

    # Nodes general options
    network_api.enablePcapDumpAll()
    network_api.disableLogAll()
    network_api.disableCli()
    # network_api.enableCli()

def run_iperf(net, bg_bw, bg_size, burst_bw, burst_size):
    h1, h3, h5 = net.get('h1', 'h3', 'h5')

    h3.cmd('iperf -s -u -p 5000 &')
    h3.cmd('iperf -s -u -p 5001 &')
    
    h1.sendCmd('iperf -c %s -b %dM -n %dM -p 5000 -u' % (h3.IP(), bg_bw, bg_size) )
    h5.sendCmd('iperf -c %s -b %dM -n %dM -p 5001 -u' % (h3.IP(), burst_bw, burst_size) )

    print("======== h1(Background) =========")
    bg_res = dict()
    h1_out = h1.waitOutput()
    print(h1_out)
    h1_result_line = h1_out.split('\n')[11] # 取出最终数据那一行
    la = h1_result_line.split(' ') # 将这一行的结果分割
    fct_a = la[3].split("-")
    bg_res["FCT(sec)"] = float(fct_a[1])
    bg_res["Transfer(MBytes)"] = float(la[6])
    bg_res["Bandwidth(Mbits/sec)"] = float(la[9])
    bg_res["Jitter(ms)"] = float(la[13])
    lost_a = la[-2].split("/")
    bg_res["Lost"] = int(lost_a[0]) / int(lost_a[1])
    
    print(bg_res)

    print("======== h5(Burst) =========")
    burst_res = dict()
    h5_out = h5.waitOutput()
    print(h5_out)
    h5_result_line = h5_out.split('\n')[11] # 取出最终数据那一行
    la = h5_result_line.split(' ') # 将这一行的结果分割
    fct_a = la[3].split("-")
    burst_res["FCT(sec)"] = float(fct_a[1])
    burst_res["Transfer(MBytes)"] = float(la[6])
    burst_res["Bandwidth(Mbits/sec)"] = float(la[9])
    burst_res["Jitter(ms)"] = float(la[13])
    lost_a = la[-2].split("/")
    burst_res["Lost"] = int(lost_a[0]) / int(lost_a[1])
    
    print(burst_res)

    return bg_res, burst_res

def run_measurement(net):
    bg_fcts, bg_jitters, bg_bandwidth, bg_loss = [], [], []
    burst_fcts, burst_jitters, burst_bandwidth, burst_loss = [], [], []
    for i in range(20):
        print("=========== round %d ===========" % (i + 1))
        bg_res, burst_res = run_iperf(net, bg_bw = 25, bg_size = 50, burst_bw = 80, burst_size = 20)
        bg_fcts.append(bg_res["FCT(sec)"])
        bg_jitters.append(bg_res["Jitter(ms)"])
        bg_bandwidth.append(bg_res["Bandwidth(Mbits/sec)"])
        bg_loss.append(bg_res["Lost"])
        burst_fcts.append(burst_res["FCT(sec)"])
        burst_jitters.append(burst_res["Jitter(ms)"])
        burst_bandwidth.append(burst_res["Bandwidth(Mbits/sec)"])
        burst_loss.append(burst_res["Lost"])

    bg_fcts_avg = sum(bg_fcts)/len(bg_fcts)
    bg_jitters_avg = sum(bg_jitters)/len(bg_jitters)
    bg_bandwidth_avg = sum(bg_bandwidth)/len(bg_bandwidth)
    bg_lost_avg = sum(bg_loss)/len(bg_loss)

    burst_fcts_avg = sum(burst_fcts)/len(burst_fcts)
    burst_jitters_avg = sum(burst_jitters)/len(burst_jitters)
    burst_bandwidth_avg = sum(burst_bandwidth)/len(burst_bandwidth)
    burst_lost_avg = sum(burst_loss)/len(burst_loss)

    print("=========== round end ===========")
    print("background", bg_fcts_avg, bg_jitters_avg, bg_bandwidth_avg, bg_lost_avg)
    print("burst", burst_fcts_avg, burst_jitters_avg, burst_bandwidth_avg, burst_lost_avg)


network_api = NetworkAPI()
init_topology(network_api)

network_api.startNetwork()
print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
net = network_api.net

h1, h2, h3, h4, h5 = net.getNodeByName('h1', 'h2', 'h3', 'h4', 'h5')

print(h1.cmd("ping -c5 {}".format(h2.IP())))


run_measurement(net)


print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
network_api.stopNetwork()