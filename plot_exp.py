import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pylab import mpl

def plot_lost(opt_str, data_0, data_1, data_2, data_3, filename, step, bg = 0):
    x_arr = data_0['Aggregated Network Load (%)']
    y_arr_0 = data_0[opt_str] * 100
    y_arr_1 = data_1[opt_str] * 100
    y_arr_2 = data_1[opt_str] * 100
    y_arr_3 = data_3[opt_str] * 100
    y_ticks = []
    t = bg
    li = max(y_arr_0.max(), y_arr_1.max(), y_arr_2.max(), y_arr_3.max())
    while t - step <= li:
        y_ticks.append(t)
        t += step

    ax.clear()
    ax.grid()
    ins0 = ax.plot(x_arr, y_arr_0, label='basic forwarding', marker='o')
    ins1 = ax.plot(x_arr, y_arr_1, label='random deflection', marker='s')
    ins2 = ax.plot(x_arr, y_arr_2, label='power-of-two choices deflection', marker='D')
    ins3 = ax.plot(x_arr, y_arr_3, label='selective deflection', marker='v')
    lns = ins0 + ins1 + ins2 + ins3
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc="upper left")
    ax.set_xlabel("Aggregated Network Load (%)")
    ax.set_ylabel(opt_str)

    ax.set_xticks(x_arr)
    ax.set_yticks(y_ticks)
    ax.set_ylim(bottom=bg)
    # plt.show()
    fileinfo = ''
    if opt_str == 'Mean FCT (s)':
        fileinfo = 'fct'
    elif opt_str == 'Mean Jitter (ms)':
        fileinfo = 'jitter'
    elif opt_str == 'Mean Bandwidth (Mbps)':
        fileinfo = 'bd'
    elif opt_str == 'Mean Packet Lost (%)':
        fileinfo = 'lost'

    # plt.show()
    plt.savefig('log/%s_%s.svg' % (fileinfo, filename))
    ax.clear()



mpl.rcParams['font.sans-serif'] = ['Times New Roman'] # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题
fig,ax = plt.subplots()
ax.figsize=(48,48)
plt.rcParams['figure.figsize'] = (6.0, 4.0)
plt.rcParams['image.interpolation'] = 'nearest' # 设置 interpolation style
plt.rcParams['image.cmap'] = 'gray' # 设置 颜色 style
plt.rcParams['savefig.dpi'] = 300 #图片像素
plt.rcParams['figure.dpi'] = 300 #分辨率

bg_filename = 'bg25_bg_bgn50_burstn20'
burst_filename = 'bg25_burst_bgn50_burstn20'

bg_df0 = pd.read_csv('log/0/result_%s.csv' % bg_filename)
bg_df0 = pd.DataFrame(bg_df0)
bg_df1 = pd.read_csv('log/1/result_%s.csv' % bg_filename)
bg_df1 = pd.DataFrame(bg_df1)
bg_df2 = pd.read_csv('log/2/result_%s.csv' % bg_filename)
bg_df2 = pd.DataFrame(bg_df2)
bg_df3 = pd.read_csv('log/3/result_%s.csv' % bg_filename)
bg_df3 = pd.DataFrame(bg_df3)

burst_df0 = pd.read_csv('log/0/result_%s.csv' % burst_filename)
burst_df0 = pd.DataFrame(burst_df0)
burst_df1 = pd.read_csv('log/1/result_%s.csv' % burst_filename)
burst_df1 = pd.DataFrame(burst_df1)
burst_df2 = pd.read_csv('log/2/result_%s.csv' % burst_filename)
burst_df2 = pd.DataFrame(burst_df2)
burst_df3 = pd.read_csv('log/3/result_%s.csv' % burst_filename)
burst_df3 = pd.DataFrame(burst_df3)

opt_strs = ['Mean FCT (s)', 'Mean Jitter (ms)', 'Mean Bandwidth (Mbps)', 'Mean Packet Lost (%)']

plot_lost(opt_strs[3], bg_df0, bg_df1, bg_df2, bg_df3, bg_filename, 0.1)
plot_lost(opt_strs[3], burst_df0, burst_df1, burst_df2, burst_df3, burst_filename, 2.5)



