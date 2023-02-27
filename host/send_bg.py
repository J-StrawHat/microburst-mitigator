import subprocess
import matplotlib.pyplot as plt
import datetime, os, time

aggregate_load = 105
background_load = 55
is_udp_flow = True
flow_interval = 0
flow_type = "bg"
iperf_version = 2

def run_iperf(fa_dir = 'log', idx = '1', ip_addr = '10.2.3.2', bandwidth = '25M', flowsize = '5M', is_udp = True, iperf_mode = 2):
    date_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    file_name = fa_dir + "/iperf_" + flow_type + "_" + idx + "_" + bandwidth + "_" + flowsize
    iperf_cmd = []
    if iperf_mode == 3:
        iperf_cmd = ['iperf3', '-c', ip_addr, '-b', bandwidth, '-n', flowsize, '-p', '5001']
    elif iperf_mode == 2:
        iperf_cmd = ['iperf', '-c', ip_addr, '-b', bandwidth, '-n', flowsize, '-p', '5001', '-w', '10M']
    if is_udp:
        iperf_cmd.append('-u')
        file_name += "_u.txt"
    else:
        file_name += ".txt"
    
    with open(file_name, 'w') as f:
        subprocess.run(iperf_cmd, stdout=f)

    res = dict()

    with open(file_name, 'r') as f:
        for line in f:
            la = line.split(" ")
            if iperf_mode == 3:
                if is_udp and 'receiver' in line: 
                    fct_a = la[5].split("-")
                    res["FCT(sec)"] = float(fct_a[1])

                    res["Transfer(MBytes)"] = float(la[10])

                    res["Bandwidth(Mbits/sec)"] = float(la[13])

                    res["Jitter(ms)"] = float(la[16])

                    lost_a = la[19].split("/")
                    res["Lost"] = int(lost_a[0]) / int(lost_a[1])

                    break

                elif not is_udp and 'receiver' in line:
                    fct_a = la[5].split("-")
                    res["FCT(sec)"] = float(fct_a[1])

                    res["Transfer(MBytes)"] = float(la[10])

                    res["Bandwidth(Mbits/sec)"] = float(la[13])

                    break
            elif iperf_mode == 2:
                if is_udp and '%' in line: 
                    fct_a = la[3].split("-")
                    res["FCT(sec)"] = float(fct_a[1])

                    res["Transfer(MBytes)"] = float(la[6])

                    res["Bandwidth(Mbits/sec)"] = float(la[9])

                    res["Jitter(ms)"] = float(la[13])

                    lost_a = la[-2].split("/")
                    res["Lost"] = int(lost_a[0]) / int(lost_a[1])

                    break

                elif not is_udp and 'sec' in line:
                    fct_a = la[3].split("-")
                    res["FCT(sec)"] = float(fct_a[1])

                    res["Transfer(MBytes)"] = float(la[6])

                    res["Bandwidth(Mbits/sec)"] = float(la[9])

                    break
    print(res)

    return res

def iperf_loop(bg = 25, agg = 35, is_udp = True, period = 3, iperf_mode=2): # 20次microburst事件
    X, fcts, transfers, jitters, loss = [], [], [], [], []
    burst = agg - bg
    if burst <= 0:
        print("Error: burst <= 0")
        return -1
    
    fa_dir = "log/log_bg" + str(bg) + "_agg" + str(agg)
    if is_udp:
        fa_dir += "_u" 
    if not os.path.exists(fa_dir):
        os.mkdir(fa_dir)

    if flow_type == "burst":
        bd, fz = burst, '5M'
    elif flow_type == "bg":
        bd, fz = bg, '20M'

    for i in range(0, 20):
        mymap = run_iperf(fa_dir=fa_dir, idx=str(i), bandwidth=str(bd) + "M", flowsize=fz, is_udp=is_udp, iperf_mode=iperf_version)
        fcts.append(mymap["FCT(sec)"])
        if is_udp:
            jitters.append(mymap["Jitter(ms)"])
            loss.append(mymap["Lost"])
        time.sleep(period)
    fcts_avg = sum(fcts)/len(fcts)
    jitters_avg = sum(jitters)/len(jitters)
    lost_avg = sum(loss)/len(loss)
    print(fcts_avg, jitters_avg, lost_avg)
    print("FCT", fcts)
    print("Jitter", jitters)
    print("Lost", loss)

    # 每个agg参数下，生成一个报告
    with open(fa_dir + "/iperf_a_" + flow_type + "_report.txt", "w") as f:
        f.write(str(fcts_avg) + " " + str(jitters_avg) + " " + str(lost_avg))
        f.write("\n")
        for e in fcts:
            f.write(str(e) + " ")
        f.write("\n")
        for e in jitters:
            f.write(str(e) + " ")
        f.write("\n")
        for e in loss:
            f.write(str(e) + " ")

    # （未区分模式）在总报告下追加数据
    with open("log/report/" + flow_type + "_report.txt", "a") as f:
        f.write(str(fcts_avg) + " " + str(jitters_avg) + " " + str(lost_avg) + "\n")

    return X, fcts, jitters, loss


if not os.path.exists("log/report"):
    os.makedirs("log/report", mode=0o777)
iperf_loop(bg=background_load, agg=aggregate_load, is_udp=is_udp_flow, period=flow_interval)
