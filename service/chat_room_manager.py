import socket
from common import utiles
import threading
import json
from PyQt5.QtCore import pyqtSignal,QObject

class ChatRoomManager(QObject):
    on_msg_update_signal = pyqtSignal(int,object)
    
    
    def __init__(self,room_ip,room_port,nickname):
        super().__init__()
        self.room_ip = room_ip
        self.room_port = room_port
        self.nickname = nickname
        self.tcp_client = None
    
    
    def send_msg(self,msg):
        if self.tcp_client is None:
            print("请先建立连接")
            return
        
        self.tcp_client.send(msg.encode("UTF-8"))
        
             
    def run_forever(self):
        #连接TCP服务器,room.ip,room.port
        self.tcp_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.tcp_client.connect((self.room_ip,self.room_port))
        print(f"服务器连接成功 {self.room_ip}:{self.room_port}")
        self.tcp_client.send(self.nickname.encode("UTF-8"))
        try:
            while True:
                bytes_data = self.tcp_client.recv(4096)
                if bytes_data:
                    msg = utiles.decode_data(bytes_data)
                    json_dict = json.loads(msg)
                    print(json_dict)
                    code = json_dict['code']
                    data = json_dict['data']
                    self.on_msg_update_signal.emit(code,data)
                else:
                    break
        except Exception as e:
            print(e)
        finally:
            self.tcp_client.close()
            self.tcp_client = None
    
        
    def enter(self):
        thread = threading.Thread(target=self.run_forever,daemon=True)
        thread.start()
        
        