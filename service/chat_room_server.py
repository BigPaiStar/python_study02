import socket
import json
import time
import sys
sys.path.append("../")

import threading
from common.utiles import *

CODE_MSG_HISTORY = 0
CODE_NEW_MSG = 1
CODE_CLIENT_LIST = 2
CODE_NOTICE = 4


class Client:

    def __init__(self, nickname: str, client_socket: socket.socket, ip_port: tuple):
        self.client_nickname: str = nickname
        self.client_socket: socket.socket = client_socket
        self.ip_port: tuple = ip_port

    def __str__(self):
        return f"{self.client_nickname} {self.ip_port}"

    def __eq__(self, other):
        return self.ip_port == other.ip_port


class Broadcaster:
    # 掩码位数
    mask_bits_dict = {
        "192": 24,
        "172": 23,  # 16
    }
    broadcast_port = 8000
    """
    广播者，用于把服务器地址消息广播出去
    """

    def __init__(self, name, host, port):
        self.chatroom_name = name
        self.server_host = host
        self.server_port = port
        self.broadcast_thread = None

        # 根据server_host和掩码位数计算广播地址
        mask_bits = self.mask_bits_dict[self.server_host.split(".")[0]]
        self.BROADCAST_ADDR = (calculate_broadcast_address(self.server_host, mask_bits), self.broadcast_port)

    def run(self):
        # 开启子线程，一直全局发送UDP广播，让客户端发现服务器
        self.broadcast_thread = threading.Thread(target=self.__broadcast)
        self.broadcast_thread.daemon = True
        self.broadcast_thread.start()

    def __broadcast(self):
        """
        广播UDP消息给所有局域网设备
        消息格式：{
            "name":"90年代的小青年",
            "ip":"172.16.0.123",
            "port":8000,
        }
        :return:
        """

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        try:
            while True:
                message = {
                    "name": self.chatroom_name,
                    "ip": self.server_host,
                    "port": self.server_port,
                }
                udp_socket.sendto(f"{json.dumps(message)}\r\n".encode("utf-8"),
                                  self.BROADCAST_ADDR)
                # 间隔2秒发送一次
                time.sleep(2)
        except Exception as e:
            print(e)
            print("广播异常，服务器无法被发现!")
        finally:
            udp_socket.close()


BUFFER_SIZE = 2048  # 接收缓冲区大小


class BaseServer:

    def __init__(self):
        # 历史消息， 最多100条
        self.msg_list = []
        # 客户端列表, 指定条目类型为 Client
        self.client_list: list[Client] = []

    @staticmethod
    def wrap_data(code, msg="success", data=None):
        return {
            "code": code,
            "msg": msg,
            "data": data
        }

    def send(self, client, code, msg, data):
        obj = self.wrap_data(code, msg, data)
        json_str = json.dumps(obj) + "\r\n"
        client.send(json_str.encode())

    def send_all(self, code, msg, data):
        for client in self.client_list:
            try:
                self.send(client.client_socket, code, msg, data)
            except:
                print("发送消息失败，客户端已断开:", client.client_nickname, client.ip_port)
                if client in self.client_list:
                    self.client_list.remove(client)

    def send_msg_to_all(self, data):

        self.send_all(CODE_NEW_MSG, "msg", [data])

        self.msg_list.append(data)
        # 只保留最新的100条
        self.msg_list = self.msg_list[-100:]

    def append_client(self, client_socket, ip_port):
        # ConnectionResetError: [WinError 10054]; 远程主机强迫关闭了一个现有的连接。
        recv_data = None
        try:
            recv_data = client_socket.recv(BUFFER_SIZE)
            # 接受客户端发来的昵称
        except ConnectionResetError as e:
            print("远程主机强迫关闭了一个现有的连接。客户端已断开:", ip_port)

        if not recv_data:
            return None

        nickname = decode_data(recv_data)
        client = Client(nickname, client_socket, ip_port)
        self.client_list.append(client)
        return client


class ChatServer(BaseServer):

    def __init__(self, chatroom_name):
        super().__init__()
        self.chatroom_name = chatroom_name

        # 设置服务器信息
        self.server_host = ''  # 服务器IP地址
        self.SERVER_PORT = 8001  # 服务器端口号

        # 获取本地所有IP地址，过滤出192或172开头的IP地址
        ip_list = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if
                   ip.startswith("192.168") or ip.startswith("172.16")]
        # 如果没有获取到IP地址，则默认使用本地IP地址
        if not ip_list:
            self.server_host = ""
        else:
            ip_list.sort()
            # 找到ip_list中192.168.38开头的条目
            for ip in ip_list:
                if ip.startswith("192.168.38"):
                    ip_list.remove(ip)
                    ip_list.insert(0, ip)
                    break
            # 放到最前边
            self.server_host = ip_list[0]

        self.broadcaster = Broadcaster(self.chatroom_name, self.server_host, self.SERVER_PORT)
        self.broadcaster.run()

        print(f"本机局域网IP:{ip_list},广播地址:{self.broadcaster.BROADCAST_ADDR}")

        self.notice = f"聊天室地址:{self.server_host}:{self.SERVER_PORT} \r\n这里是你温馨的港湾,欢迎来到这里!"
        try:
            # 创建服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置地址可以重用
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.server_socket.bind((self.server_host, self.SERVER_PORT))
            self.server_socket.listen(128)
        except Exception as e:
            print(type(e), e)
            raise Exception(wrap_color(f"服务器启动失败，无法在指定端口启动【{self.SERVER_PORT}】监听!", Color.RED))

    def run(self):

        print(
            f"聊天室 [{wrap_color(self.chatroom_name, Color.YELLOW)}] 服务器启动成功\r\n",
            wrap_color(f"TCP服务器地址:[{self.server_host}:{self.SERVER_PORT}] 等待客户端连接...", Color.GREEN)
        )
        while True:
            new_client, ip_port = self.server_socket.accept()
            print("新客户端已连接:", ip_port)
            # 开启线程
            t1 = threading.Thread(target=self.handle_new_client, args=(new_client, ip_port))
            # 设置线程守护
            t1.daemon = True
            t1.start()

    def handle_new_client(self, client_socket, ip_port):
        client: Client = self.append_client(client_socket, ip_port)

        if client is None:
            return

        nickname = client.client_nickname
        time.sleep(0.5)

        try:
            # 把最近10条消息发送给客户端
            self.send_history_msg(client_socket)
            time.sleep(0.2)
            # 把群公告发给客户端
            self.send_notice(client_socket)
            time.sleep(0.2)
            # 把所有客户端列表发送给每个客户端
            self.send_client_list()
            time.sleep(0.2)

            # 把新客户端加入聊天室的消息发送给所有客户端
            msg = f"欢迎来自 {ip_port} 的【{nickname}】加入聊天室！"
            print(msg)
            # 通知所有客户端
            self.new_msg(msg)

            while True:
                recv_data = client_socket.recv(BUFFER_SIZE)
                if recv_data:
                    msg = decode_data(recv_data)
                    print(client, ":", msg)
                    self.new_msg(msg, client)
                else:
                    raise Exception("客户端断开连接!")
        except:
            exit_msg = f"来自 {ip_port} 的客户端【{nickname}】下线了"
            print(exit_msg)
            if client is not None and client in self.client_list:
                self.client_list.remove(client)
                self.new_msg(exit_msg)
                # 重新发送客户端列表
                self.send_client_list()
        finally:
            client_socket.close()

    def new_msg(self, message, from_client=None):
        if not message:
            return

        if from_client:
            msg_sender = from_client.client_nickname
            msg_addr = from_client.ip_port
        else:
            msg_sender = "系统消息"
            msg_addr = (self.server_host, self.SERVER_PORT)

        data = {
            "nickname": msg_sender,
            "from": msg_addr,
            "message": message,
            "time": current_time_str(),
        }
        self.send_msg_to_all(data)

    def send_history_msg(self, client_socket):
        recent_msg_list = self.msg_list[-10:]
        self.send(client_socket, CODE_MSG_HISTORY, "消息记录", recent_msg_list)

    def send_client_list(self):
        clients = [(c.client_nickname, c.ip_port) for c in self.client_list]
        self.send_all(CODE_CLIENT_LIST, "客户端列表", clients)

    def send_notice(self, client_socket):
        self.send(client_socket, CODE_NOTICE, "群公告", self.notice)


if __name__ == '__main__':
    args = sys.argv[1:]
    chatroom_name = None
    if len(args) > 0:
        chatroom_name = args[0]

    while chatroom_name is None or chatroom_name == "":
        chatroom_name = input("请输入聊天室名称:")
        chatroom_name = chatroom_name.strip()

    chatroom = ChatServer(chatroom_name)
    chatroom.run()