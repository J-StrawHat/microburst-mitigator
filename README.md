# microburst-mitigator

## 拓扑结构

![](./fattree.png)

## 常用命令

```bash
ssh -Y zwx@10.211.55.4
```

```bash
sudo p4run --config p4app-fattree.json
```

BMv2 Mininet CLI:

```bash
xterm h1 h3 h5
```

H1 & H5：

```bash
cd host; python send.py 10.2.3.2 6700 30000
```

H3:

```bash
cd host; python receive.py
```

## 参考

+ [The BMv2 Simple Switch target](https://github.com/p4lang/behavioral-model/blob/main/docs/simple_switch.md#pseudocode-for-what-happens-at-the-end-of-ingress-and-egress-processing)
+ [Congestion Aware Load Balancing](https://github.com/nsg-ethz/p4-learning/tree/master/exercises/10-Congestion_Aware_Load_Balancing)
+ [Burstradar](https://github.com/harshgondaliya/burstradar/blob/master/burstradar.p4)
 