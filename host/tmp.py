import subprocess
import matplotlib.pyplot as plt
import datetime

# run iperf server
def run_iperf():
    iperf_cmd = ['iperf', '-s', '-i', '1', '-t', '10']
    bandwidths = []
    iperf_process = subprocess.Popen(iperf_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        rt_data = iperf_process.stdout.readline().decode()
        if rt_data != "":
            print(rt_data, end="")
            if "Mbits/sec" in rt_data:
                bandwidth = float(rt_data.split(" ")[-2])
                bandwidths.append(bandwidth)
        else:
            break
    # return iperf_process.wait()
    return bandwidths

def plot_iperf_results(data):
    plt.plot(data)
    plt.xlabel("Time (s)")
    plt.ylabel("Bandwidth (Mbits/sec)")
    plt.title("Iperf Results")
    # plt.show()

    date_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    file_name = "./iperf_res_" + date_str + ".svg"
    plt.savefig(file_name)

results = run_iperf()
plot_iperf_results(results)
