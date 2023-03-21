from mininet.log import lg, info
from mininet.util import pmonitor
from p4utils.mininetlib.network_API import NetworkAPI
import subprocess
import os, sys, re, time
import csv
import numpy as np
from jinja2 import Environment, FileSystemLoader

leaf_bw = 100
spine_bw = 400
background_flow_size = 100
burst_flow_size = 50
# 200 50
# 20 5
curdate = time.strftime("%m%d_%H", time.localtime())
fa_dir_pre = 'log/%s_tcp_%d_%d/%s_tcp_%d_%d_' % (curdate, background_flow_size, burst_flow_size, curdate, background_flow_size, burst_flow_size)

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
    network_api.setBw("h1", "s1", leaf_bw)
    network_api.setBw("h2", "s1", leaf_bw)
    network_api.setBw("h3", "s2", leaf_bw)
    network_api.setBw("h4", "s2", leaf_bw)
    network_api.setBw("h5", "s3", leaf_bw)
    network_api.setBw("h6", "s3", leaf_bw)
    network_api.setBw("h7", "s4", leaf_bw)
    network_api.setBw("h8", "s4", leaf_bw)

    network_api.setBw("s1", "s5", spine_bw)
    network_api.setBw("s2", "s5", spine_bw)
    network_api.setBw("s4", "s5", spine_bw)
    network_api.setBw("s2", "s6", spine_bw)
    network_api.setBw("s3", "s6", spine_bw)
    network_api.setBw("s4", "s6", spine_bw)
    network_api.setBw("s2", "s7", spine_bw)
    network_api.setBw("s4", "s7", spine_bw)

    # Assignment strategy
    network_api.l3()

    # Nodes general options
    network_api.disablePcapDumpAll()
    network_api.disableLogAll()
    network_api.disableCli()
    #network_api.enableCli()

def run_iperf(net, bg_bw, bg_size, burst_bw, burst_size):
    h1, h3, h5 = net.get('h1', 'h3', 'h5')

    h3.cmd('iperf -s -p 5000 &')
    h3.cmd('tcpdump -i h3-eth0 -w pcap/h1_h3.pcap tcp port 5000 &')
    h3.cmd('iperf -s -p 5001 &')
    h3.cmd('tcpdump -i h3-eth0 -w pcap/h5_h3.pcap tcp port 5001 &')

    h1.sendCmd('iperf -c %s -b %dM -n %dM -p 5000' % (h3.IP(), bg_bw, bg_size) )
    h5.sendCmd('iperf -c %s -b %dM -n %dM -p 5001' % (h3.IP(), burst_bw, burst_size) )


    h1_out = h1.waitOutput()
    h5_out = h5.waitOutput()

    h3.cmd('kill $(pgrep tcpdump)')

    bg_retra = h1.cmd('tshark -r pcap/h1_h3.pcap -Y tcp.analysis.retransmission | wc -l').split('\r\n')[1] 
    burst_retra = h5.cmd('tshark -r pcap/h5_h3.pcap -Y tcp.analysis.retransmission | wc -l').split('\r\n')[1]
    
    print('[Retransmission]')
    print('Background:', bg_retra, ' Burst:', burst_retra)
    #print(h1_out)
    #print( h1.cmd(' tshark -r pcap/h1_h3.pcap  -qz \'io,stat,1,FRAMES\' '))
    #print( h5.cmd(' tshark -r pcap/h5_h3.pcap  -qz \'io,stat,1,FRAMES\' '))

    bg_fct = h1.cmd(' tshark -r pcap/h1_h3.pcap  -qz \'io,stat,1,FRAMES\' | grep Duration | awk \'{print $3}\' ').split('\r\n')[1]  
    # iperf的持续时间通常比实际FCT要短，因为它不考虑连接建立和关闭的时间以及其他任何传输数据以外的延迟时间

    #print(h5_out)
    burst_fct = h5.cmd(' tshark -r pcap/h5_h3.pcap  -qz \'io,stat,1,FRAMES\' | grep Duration | awk \'{print $3}\' ').split('\r\n')[1] 
    
    print('[FCT]')
    print('Background:', bg_fct, ' Burst:', burst_fct)
    print()

    bg_res = {'FCT(sec)':float(bg_fct), 'Retransmission':int(bg_retra)}
    burst_res = {'FCT(sec)':float(burst_fct), 'Retransmission':int(burst_retra)}
    return bg_res, burst_res


def run_iperf_loop(net, idx, bg_bw, burst_bw, bg_size, burst_size):
    bg_fcts, bg_retrans = [], []
    burst_fcts, burst_retrans = [], []
    for i in range(15):
        print("=========== [%d] round %d ===========" % (idx, i + 1))
        bg_res, burst_res = run_iperf(net, bg_bw = bg_bw, bg_size = bg_size, burst_bw = burst_bw, burst_size = burst_size)
        bg_fcts.append(bg_res["FCT(sec)"])
        bg_retrans.append(bg_res["Retransmission"])
        burst_fcts.append(burst_res["FCT(sec)"])
        burst_retrans.append(burst_res["Retransmission"])

    bg_fcts_avg = sum(bg_fcts)/len(bg_fcts)
    bg_retrans_avg = sum(bg_retrans)/len(bg_retrans)
    bg_retrans_p95 = np.percentile(bg_retrans, 95)

    burst_fcts_avg = sum(burst_fcts)/len(burst_fcts)
    burst_retrans_avg = sum(burst_retrans)/len(burst_retrans)
    burst_retrans_p95 = np.percentile(burst_retrans, 95)

    print('\033[96m' + "=== round end (bg:%f Mbps, %d MBytes) (burst:%f Mbps, %d MBytes) ===" % (bg_bw, bg_size, burst_bw, burst_size) + '\033[0m')
    print("background", bg_fcts_avg, bg_retrans_avg, bg_retrans_p95)
    print("burst", burst_fcts_avg, burst_retrans_avg, burst_retrans_p95)
    bg_res_tuple = (bg_fcts_avg, bg_retrans_avg, bg_retrans_p95)
    burst_res_tuple = (burst_fcts_avg, burst_retrans_avg, burst_retrans_p95)
    return bg_res_tuple, burst_res_tuple

def run_measurement(net, deflect_mode = 0, bg_load = 25, bg_size = 20, burst_size = 5):
    agg_road_list = []
    bg_fcts_list, bg_retrans_avg_list, bg_retrans_p95_list = [], [], []
    burst_fcts_list, burst_retrans_avg_list, burst_retrans_p95_list = [], [], []
    if bg_load == 25: 
        agg_road_list = [35, 45, 55, 65, 75, 85, 95]
    elif bg_load == 50:
        agg_road_list = [55, 65, 75, 85, 95]
    elif bg_load == 75:
        agg_road_list = [80, 85, 90, 95]
    idx = 1
    for cur_agg_road in agg_road_list:
        print('\033[96m' + "=== [%d] round begin (bg:%f Mbps, %d MBytes) (burst:%f Mbps, %d MBytes) ===" % (idx, 0.01 * bg_load * leaf_bw, bg_size, 0.01 * (cur_agg_road - bg_load) * leaf_bw, burst_size) + '\033[0m')
        bg_test_res, burst_test_res = run_iperf_loop(net, idx,
                                                    bg_bw = 0.01 * bg_load * leaf_bw, 
                                                    burst_bw = 0.01 * (cur_agg_road - bg_load) * leaf_bw,
                                                    bg_size = bg_size,
                                                    burst_size = burst_size)
        bg_fcts_list.append(bg_test_res[0])
        bg_retrans_avg_list.append(bg_test_res[1])
        bg_retrans_p95_list.append(bg_test_res[2])

        burst_fcts_list.append(burst_test_res[0])
        burst_retrans_avg_list.append(burst_test_res[1])
        burst_retrans_p95_list.append(burst_test_res[2])

        idx += 1
    
    fa_dir = fa_dir_pre + str(deflect_mode)
    if not os.path.exists(fa_dir):
        os.makedirs(fa_dir)
    bg_rows = zip(agg_road_list, bg_fcts_list, bg_retrans_avg_list, bg_retrans_p95_list)
    bg_log_filename = fa_dir + '/tcp_result_bg%d_bg_bgn%d_burstn%d.csv' % (bg_load, bg_size, burst_size)
    burst_rows = zip(agg_road_list, burst_fcts_list, burst_retrans_avg_list, burst_retrans_p95_list)
    burst_log_filename = fa_dir + '/tcp_result_bg%d_burst_bgn%d_burstn%d.csv' % (bg_load, bg_size, burst_size)

    with open(bg_log_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Aggregated Network Load (%)', 'Mean FCT (s)', 'Mean number of packet retransmission', 'P95 number of packet retransmission'])
        writer.writerows(bg_rows)
    
    with open(burst_log_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Aggregated Network Load (%)', 'Mean FCT (s)', 'Mean number of packet retransmission', 'P95 number of packet retransmission'])
        writer.writerows(burst_rows)

total_start_time = time.time()
for i in [0, 1, 2, 3]:
    env = Environment(loader=FileSystemLoader('p4src/include'))
    template = env.get_template('constants.p4template')

    output = template.render(deflect_mode=i, threshold = 25)
    #print(output)

    # 将渲染后的代码写入文件中
    with open('p4src/include/constants.p4', 'w') as f:
        f.write(output)

    network_api = NetworkAPI()
    init_topology(network_api)

    network_api.startNetwork()
    print('\033[92m' + '&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&' + '\033[0m')
    net = network_api.net

    h1, h2, h3, h4, h5 = net.getNodeByName('h1', 'h2', 'h3', 'h4', 'h5')

    print(h1.cmd("ping -c5 {}".format(h2.IP())))

    start_time = time.time()

    run_measurement(net, deflect_mode = i, bg_size=background_flow_size, burst_size=burst_flow_size)

    run_measurement(net, deflect_mode = i, bg_load=50, bg_size=background_flow_size, burst_size=burst_flow_size)

    #run_iperf(net, bg_bw=75, bg_size=100, burst_bw=5, burst_size=50)
    run_measurement(net, deflect_mode = i, bg_load=75, bg_size=background_flow_size, burst_size=burst_flow_size)

    end_time = time.time()

    print('\033[92m' + '&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&' + '\033[0m')
    network_api.stopNetwork()
    print("Runtime：", end_time - start_time, "s")
total_end_time = time.time()
print('\033[92m' + 'Runtimes:%f'%(total_end_time - total_start_time) + '\033[0m')
