import numpy as np
import matplotlib.pyplot as plt

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['Times New Roman'] # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题


samplenum2=np.arange(10,200+2,10)
x10 = samplenum2


accuracy10sigmoid_test=[0.863, 0.898, 0.964, 0.985, 0.975, 0.985, 0.989, 0.992, 0.992, 0.99, 0.989, 0.991, 0.988, 0.995, 0.994, 0.995, 1.0, 0.999, 0.996, 0.995]
accuracy10tanh_test=[0.88, 0.968, 0.99, 0.985, 0.987, 0.988, 0.979, 0.986, 0.989, 0.988, 0.99, 0.987, 0.985, 0.993, 0.992, 0.993, 0.989, 0.99, 0.981, 0.991]
accuracy10relu_test=[0.931, 0.9, 0.933, 0.947, 0.953, 0.967, 0.98, 0.985, 0.973, 0.981, 0.985, 0.985, 0.986, 0.979, 0.985, 0.984, 0.984, 0.982, 0.978, 0.976]
#面向对象的绘图方式
rect1 = [0.14, 0.35, 0.77, 0.6]
fig,ax = plt.subplots()
ax.figsize=(48,48)
plt.rcParams['figure.figsize'] = (6.0, 4.0)
plt.rcParams['image.interpolation'] = 'nearest' # 设置 interpolation style
plt.rcParams['image.cmap'] = 'gray' # 设置 颜色 style
plt.rcParams['savefig.dpi'] = 300 #图片像素
plt.rcParams['figure.dpi'] = 300 #分辨率

ins0=ax.plot(x10,accuracy10tanh_test, label = 'tanh',marker='o')
ins1=ax.plot(x10,accuracy10relu_test, label = 'relu',marker='s')
ins2=ax.plot(x10,accuracy10sigmoid_test, label = 'sigmoid',marker='v')
lns = ins0+ins1+ins2
labs = [l.get_label() for l in lns]
ax.legend(lns, labs, loc="lower right")#loc="lower right" 图例右下角
ax.set_xlabel("Iteration")
ax.set_ylabel("Accuracy")
#ax.set_title("xxx0-10")
ax.set_xticks(x10)
ax.set_yticks([0.7,0.9,0.95,1.0])
#ax.grid()
plt.savefig('xxx0-10-0.png')



