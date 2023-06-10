import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pylab import mpl

def plot_retrans(x_arr, y_arr_0, y_arr_1, y_arr_2, step, bg_load, filename):
    y_ticks = step
    ax.clear()
    ax.grid()
    ins0 = ax.plot(x_arr, y_arr_0, label='Avg', marker='o')
    ins1 = ax.plot(x_arr, y_arr_1, label='P95', marker='s')
    ins2 = ax.plot(x_arr, y_arr_2, label='FCT', marker='s')
    lns = ins0 + ins1 + ins2
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc="upper left")
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Number of packet retransmission")

    ax.set_xticks(x_arr)
    ax.set_yticks(y_ticks)
    ax.set_ylim(bottom=0)
    # plt.show()


    # plt.show()
    plt.savefig('%s_bg%d_%s.svg' % (fa_dir_str, bg_load, filename))
    ax.clear()

def do_plot(filename, step):
    retrans_avg_list = [[], [], []]
    retrans_p95_list = [[], [], []]
    fct_avg_list = [[], [], []]
    t_list = list(range(0, 64, 4))

    for t in t_list:
        bg_t = pd.read_csv(fa_dir_str + '%d/tcp_result_%s.csv' % (t, filename))
        bg_t = pd.DataFrame(bg_t)
        retrans_avg = bg_t['Mean number of packet retransmission']
        retrans_p95 = bg_t['P95 number of packet retransmission']
        fct_avg = bg_t['Mean FCT (s)']

        for bg_load_idx in range(1):
            retrans_avg_list[bg_load_idx].append(retrans_avg[bg_load_idx])
            retrans_p95_list[bg_load_idx].append(retrans_p95[bg_load_idx])
            fct_avg_list[bg_load_idx].append(fct_avg[bg_load_idx])


    for bg_load_idx in range(1):
        print(retrans_avg_list[bg_load_idx])
        plot_retrans(t_list, retrans_avg_list[bg_load_idx], retrans_p95_list[bg_load_idx], fct_avg_list[bg_load_idx], step, (bg_load_idx + 1) * 25, filename)

mpl.rcParams['font.sans-serif'] = ['Times New Roman'] # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题
fig,ax = plt.subplots()
ax.figsize=(48,48)
plt.rcParams['figure.figsize'] = (6.0, 4.0)
plt.rcParams['image.interpolation'] = 'nearest' # 设置 interpolation style
plt.rcParams['image.cmap'] = 'gray' # 设置 颜色 style
plt.rcParams['savefig.dpi'] = 300 #图片像素
plt.rcParams['figure.dpi'] = 300 #分辨率

bg_bw = 25
bg_n = 100
burst_n = 50
bg_filename = 'bg_bgn%d_burstn%d' % (bg_n, burst_n)
burst_filename = 'burst_bgn%d_burstn%d' % (bg_n, burst_n)
fa_dir_str_pre = '0406_13_tcp_100_50'

fa_dir_str = 'log/' + fa_dir_str_pre + '/' + fa_dir_str_pre + '_3_t'

bg_step = [10 * i for i in range(0, 7)]
do_plot(bg_filename, bg_step)
burst_step = [4.5 * i for i in range(0, 7)]
do_plot(burst_filename, burst_step)



