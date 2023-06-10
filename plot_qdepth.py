import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pylab import mpl

mpl.rcParams['font.size'] = 19
mpl.rcParams['font.sans-serif'] = ['Times New Roman'] # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题
#fig,ax = plt.subplots()
#ax.figsize=(48,48)
#plt.rcParams['figure.figsize'] = (6.0, 4.0)
#plt.rcParams['image.interpolation'] = 'nearest' # 设置 interpolation style
#plt.rcParams['image.cmap'] = 'gray' # 设置 颜色 style
#plt.rcParams['savefig.dpi'] = 300 #图片像素
#plt.rcParams['figure.dpi'] = 300 #分辨率

# 读取CSV数据
filename = 'log/0408-17-22'
data = pd.read_csv('%s.csv' % filename)
x = data.iloc[:, 0]  # timestamp(us)
delta = x[0]
x = [e - delta for e in x]
y = data.iloc[:, 1]  # Queue Length(number of packets)
print(x[-1])
# 绘制折线图

plt.ticklabel_format(style='sci',scilimits=(0,0),axis='x')

colors = ['#3B75AF', '#EE8635', '#C53B32', '#509F3D']
idx = 0

plt.plot(x, y, color=colors[idx])

x_steps = [i * (x[-1] / 6) for i in range(0, 7)]

plt.xticks(x_steps)
'''
plt.yticks([i * 2 for i in range(5)] + [10 * i for i in range(8)])
'''
plt.yticks([15 * i for i in range(6)])
ytick_list = plt.yticks()[0]  # 获取所有的y刻度
for ytick in ytick_list:
    plt.axhline(y=ytick, color='gray', linestyle='--')  # 在每个y刻度上绘制


plt.ylim(bottom = 0)
plt.xlabel('Timestamp (in microseconds)', fontsize=20)
plt.ylabel('Queue Depth (number of packets)', fontsize=20)
#plt.title('Queue Depth over Time', fontsize=20)
plt.tight_layout()
plt.savefig('%s_tcp_qdepth_n_%d.svg' % (filename, idx), format='svg')



