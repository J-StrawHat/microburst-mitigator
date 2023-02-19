from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_thrift_API import SimpleSwitchThriftAPI

PORT_NUM = 8
MAX_VALUE = 2 ** 18 - 1

class RoutingController(object):

    def __init__(self):                                 # 0.创建RoutingController实例
        self.topo = load_topo('topology.json')
        self.controllers = {}
        self.init()                                     # 1.调用自定义的初始化方法

    def init(self):
        self.connect_to_switches()
        self.reset_states()
        self.set_table_defaults()
        self.set_register_defaults()

    def reset_states(self):
        [controller.reset_state() for controller in self.controllers.values()]

    def connect_to_switches(self):                      # 2.连接至thrift服务器
        for p4switch in self.topo.get_p4switches():     # 该函数返回值示例：{'s1':{'isHost': False, 'isSwitch': True, ...}, ...}
            thrift_port = self.topo.get_thrift_port(p4switch)
            # self.controllers[p4switch] = SimpleSwitchThriftAPI(thrift_port)
            cur_api = SimpleSwitchThriftAPI(thrift_port)
            cur_api.mirroring_add(100, PORT_NUM)
            self.controllers[p4switch] = cur_api
            # 建立键值对映射：{'sw_name' : SimpleSwitchThriftAPI()}

    def set_table_defaults(self):
        for controller in self.controllers.values():    #遍历所有的API操作对象，设置其默认的Action
            controller.table_set_default("ipv4_lpm", "drop", [])
            #controller.table_set_default("ecmp_group_to_nhop", "drop", [])

    def set_register_defaults(self):
        for sw_name, controller in self.controllers.items():
            port_nums = len(self.topo.get_interfaces_to_node(sw_name))
            controller.register_write("port_num_recorder", [0, 1], port_nums)
            controller.register_write("qdepth_table", [0, PORT_NUM], 0)
            controller.register_write("min_qdepth_recorder", [0, 2], MAX_VALUE)

    def set_egress_type_table(self):
        # 利用拓扑信息，学习每一个交换机的邻节点是交换机/主机
        for sw_name, controller in self.controllers.items():

            for intf, node in self.topo.get_interfaces_to_node(sw_name).items():
                # 遍历本交换机中的每一个接口intf（对应邻节点node）
                port_number = self.topo.interface_to_port(sw_name, intf) # 获取本交换机指定接口的端口号

                if self.topo.isHost(node):          # 如果邻节点是主机
                    node_type_num = 1
                elif self.topo.isP4Switch(node):    # 如果邻节点是P4交换机
                    node_type_num = 2

                print("table_add at {}:".format(sw_name))
                self.controllers[sw_name].table_add("egress_type", "set_egress_type", [str(port_number)], [str(node_type_num)])


    def route(self):
        for sw_name, controller in self.controllers.items():    # 遍历每一个交换机（边的起点）
            for sw_dst in self.topo.get_p4switches():           # 遍历另一个交换机（边的目的/终点）

                if sw_name == sw_dst:                           # 如果起点和目的刚好是「同一」交换机，那么为该交换机所直接连接的主机Host，添加流表条目
                    for host in self.topo.get_hosts_connected_to(sw_name):          # 遍历该交换机所连接的主机
                        sw_port = self.topo.node_to_node_port_num(sw_name, host)    # 得到所连接的端口号
                        host_ip = self.topo.get_host_ip(host) + "/32"               # （L3网络）主机IP地址格式：10.x.y.2
                        host_mac = self.topo.get_host_mac(host)

                        #add rule
                        print("table_add at {}:".format(sw_name))
                        self.controllers[sw_name].table_add("ipv4_lpm", "ipv4_forward", [str(host_ip)], [str(host_mac), str(sw_port)])

                else:                                           # 如果对方（边的目的节点）交换机有主机相连
                    if self.topo.get_hosts_connected_to(sw_dst):
                        # 找到两交换机之间的最短路径（列表），每条路径是一个元组，包含各途径的结点
                        paths = self.topo.get_shortest_paths_between_nodes(sw_name, sw_dst)

                        # 遍历对方交换机所连的主机
                        for host in self.topo.get_hosts_connected_to(sw_dst):
                            next_hop = paths[0][1] # 直接选择列表中的第一条路径（paths[0]），选择其下一跳节点

                            host_ip = self.topo.get_host_ip(host) + "/24"
                            sw_port = self.topo.node_to_node_port_num(sw_name, next_hop)    # 是找到起点的出端口
                            dst_sw_mac = self.topo.node_to_node_mac(next_hop, sw_name)      # 是找到目的的MAC地址

                            #add rule
                            print("table_add at {}:".format(sw_name))
                            self.controllers[sw_name].table_add("ipv4_lpm", "ipv4_forward", [str(host_ip)],
                                                                [str(dst_sw_mac), str(sw_port)])

                            
    def main(self):
        self.set_egress_type_table()
        self.route()


if __name__ == "__main__":
    controller = RoutingController().main()
