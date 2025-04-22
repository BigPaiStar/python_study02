
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import socket


import sys
sys.path.append("../")

from ui.Ui_chat_room_dialog import Ui_ChatRoomDialog
from models.chat_models import *
from common import utiles

class ChatRoomDialog(QDialog):

    def __init__(self, parent=None, room: ChatRoom = None, nickname = "匿名"):
        super().__init__(parent)
        self.ui = Ui_ChatRoomDialog()
        self.ui.setupUi(self)
        # 可以通过此设置，固定对话框的大小
        self.setFixedSize(self.width(), self.height())
        self.room = room
        self.nickname = nickname
        self.setWindowTitle(f"聊天室:{room.name}({room.ip}:{room.port}){[nickname]}")
        
        
        self.init_ui()
        self.init_data()
    
    
    
    
    
    def init_data(self):
        #连接TCP服务器,room.ip,room.port
        tcp_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        tcp_client.connect((self.room.ip,self.room.port))
        print(f"服务器连接成功 {self.room.ip}:{self.room.port}")
        tcp_client.send(self.nickname.encode("UTF-8"))
        try:
            while True:
                bytes_data = tcp_client.recv(4096)
                if bytes_data:
                    msg = utiles.decode_data(bytes_data)
                    print(msg)
                else:
                    break
        except Exception as e:
            print(e)
        finally:
            tcp_client.close()
    
        
    def init_ui(self):
        nickname = "aaa"
        ip,port = "192.168.89.198",12345
        self.ui.edit_recv.appendHtml(
            f"<font color='blue'>{nickname}</font>"
            f"<font color='gray'>({ip}:{port})</font>"
            f"<font color='red'>日期 时间</font>"
        )
        self.ui.edit_recv.appendHtml(f"<font color='black'>消息内容</font>")
        self.ui.edit_recv.appendPlainText("")
        self.ui.edit_notice.append("群公告消息")
        model = QStringListModel()
        model.setStringList([
            "a(192.168.89.198)",
            "b(192.168.89.198)",
            "c(192.168.89.198)",
        ])
        self.ui.lv_members.setModel(model)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ip = "192.168.89.198"
    room_info = {
        "name": "90后交友群",
        "ip": ip,
        "port": 8001
    }
    chat_room = ChatRoom(room_info,(ip,15555))
    dialog = ChatRoomDialog(None, chat_room, "小煤球")
    dialog.show()
    sys.exit(app.exec_())