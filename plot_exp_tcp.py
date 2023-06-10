import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pylab import mpl

def plot_retrans(opt_str, data_0, data_1, data_2, data_3, filename, fa_dir_str, step, bg = 0):
    x_arr = data_0['Aggregated Network Load (%)']
    y_arr_0 = data_0[opt_str]
    y_arr_1 = data_1[opt_str]
    y_arr_2 = data_2[opt_str]
    y_arr_3 = data_3[opt_str]
    y_ticks = []
    '''
    t = bg
    li = max(y_arr_0.max(), y_arr_1.max(), y_arr_3.max())
    while t - step <= li:
        y_ticks.append(t)
        t += step
    '''
    y_ticks = step


    ax.clear()
    ax.grid()
    ins0 = ax.plot(x_arr, y_arr_0, label='basic forwarding', marker='o')
    ins1 = ax.plot(x_arr, y_arr_1, label='random deflection', marker='s')
    ins3 = ax.plot(x_arr, y_arr_3, label='selective deflection', marker='v')
    ins2 = ax.plot(x_arr, y_arr_2, label='power-of-two-choices deflection', marker='D')
    lns = ins0 + ins1 + ins2 + ins3
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc="upper left", fontsize=14.5)
    ax.set_xlabel("Aggregated Network Load (%)", fontsize=20)
    ax.set_ylabel(opt_str, fontsize=17)

    ax.set_xticks(x_arr)
    ax.set_yticks(y_ticks)
    ax.set_ylim(bottom=bg)
    # plt.show()
    fileinfo = ''
    if opt_str == 'Mean FCT (s)':
        fileinfo = 'fct'
    elif opt_str == 'Mean number of packet retransmission':
        fileinfo = 'retrans_avg'
    elif opt_str == 'P95 number of packet retransmission':
        fileinfo = 'retrans_p95'

    # plt.show()
    plt.tight_layout()
    plt.savefig('%s_%s_%s.svg' % (fa_dir_str, fileinfo, filename), format='svg')
    ax.clear()


mpl.rcParams['font.size'] = 20 # 指定默认字体
mpl.rcParams['font.sans-serif'] = ['Times New Roman'] # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题
fig,ax = plt.subplots()
ax.figsize=(48,48)
#plt.rcParams['figure.figsize'] = (6.0, 4.0)
plt.rcParams['image.interpolation'] = 'nearest' # 设置 interpolation style
plt.rcParams['image.cmap'] = 'gray' # 设置 颜色 style
#plt.rcParams['savefig.dpi'] = 300 #图片像素
#plt.rcParams['figure.dpi'] = 300 #分辨率

bg_bw = 75
bg_n = 200
burst_n = 50
bg_filename = 'bg%d_bg_bgn%d_burstn%d' % (bg_bw, bg_n, burst_n)
burst_filename = 'bg%d_burst_bgn%d_burstn%d' % (bg_bw, bg_n, burst_n)
fa_dir_str_pre = '0604_00_tcp_200_50'

fa_dir_str = 'log/' + fa_dir_str_pre + '/' + fa_dir_str_pre + '_'
bg_df0 = pd.read_csv(fa_dir_str + '0/tcp_result_%s.csv' % bg_filename)
bg_df0 = pd.DataFrame(bg_df0)
bg_df1 = pd.read_csv(fa_dir_str + '1/tcp_result_%s.csv' % bg_filename)
bg_df1 = pd.DataFrame(bg_df1)
bg_df2 = pd.read_csv(fa_dir_str + '2/tcp_result_%s.csv' % bg_filename)
bg_df2 = pd.DataFrame(bg_df2)
bg_df3 = pd.read_csv(fa_dir_str + '3/tcp_result_%s.csv' % bg_filename)
bg_df3 = pd.DataFrame(bg_df3)

burst_df0 = pd.read_csv(fa_dir_str + '0/tcp_result_%s.csv' % burst_filename)
burst_df0 = pd.DataFrame(burst_df0)
burst_df1 = pd.read_csv(fa_dir_str + '1/tcp_result_%s.csv' % burst_filename)
burst_df1 = pd.DataFrame(burst_df1)
burst_df2 = pd.read_csv(fa_dir_str + '2/tcp_result_%s.csv' % burst_filename)
burst_df2 = pd.DataFrame(burst_df2)
burst_df3 = pd.read_csv(fa_dir_str + '3/tcp_result_%s.csv' % burst_filename)
burst_df3 = pd.DataFrame(burst_df3)

opt_strs = ['Mean FCT (s)', 'Mean number of packet retransmission', 'P95 number of packet retransmission']

bg_step = [10 * i for i in range(0, 7)]
plot_retrans(opt_strs[1], bg_df0, bg_df1, bg_df2, bg_df3, bg_filename, fa_dir_str, bg_step)
burst_step = [4.5 * i for i in range(0, 7)]
plot_retrans(opt_strs[1], burst_df0, burst_df1, burst_df2, burst_df3, burst_filename, fa_dir_str, burst_step)



