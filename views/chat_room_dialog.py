
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


import sys
sys.path.append("../")

from ui.Ui_chat_room_dialog import Ui_ChatRoomDialog
from models.chat_models import *
from service.chat_room_manager import ChatRoomManager

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
        self.model = QStringListModel()
        self.members = set()
        self.chat_room = ChatRoomManager(self.room.ip,self.room.port,self.nickname)
        self.init_ui()
        self.init_data()
        
        
    
    @pyqtSlot(int,object)
    def on_msg_update(self,code,data):
        #print(f"code:{code}")
        #print(f"data:{data}")
        if code == 4: #群公告
            self.ui.edit_notice.setPlainText(data)
        elif code == 0: #历史消息
            #清楚已有历史消息
            self.ui.edit_recv.clear()
            for item in data:
                self.append_msg_to_dialog(item)
        elif code == 1: #新消息
            for item in data:
                self.append_msg_to_dialog(item)
        elif code == 2: #客户端列表
            for item in data:
                name,(ip, port) = item
                member_str = f"{name}{ip,port}"
                print(member_str)
                self.members.add(member_str)
            
            self.model.setStringList(sorted(self.members))
            self.ui.lv_members.setModel(self.model)

    def append_msg_to_dialog(self, item):
        nickname = item['nickname']
        from_data = item['from']
        message = item['message']
        time = item['time']
        self.ui.edit_recv.appendHtml(
                f"<font color='blue'>{nickname}</font>"
                f"<font color='gray'>({from_data})</font>"
                f"<font color='red'>{time}</font>"
                )
        self.ui.edit_recv.appendHtml(f"<font color='black'>{message}</font>")
        self.ui.edit_recv.appendPlainText("")
                
                
    def init_data(self):
        self.chat_room.enter()
        
    
    def send_msg(self):
        msg = self.ui.edit_send.toPlainText()
        if msg == "":
            print("消息不能为空")
            return
        self.chat_room.send_msg(msg)
        self.ui.edit_send.clear()
    
      
    def init_ui(self):
        self.chat_room.on_msg_update_signal.connect(self.on_msg_update)
        self.ui.btn_send.clicked.connect(self.send_msg)
        self.ui.btn_close.clicked.connect(self.close)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ip = "192.168.148.67"
    room_info = {
        "name": "90后交友群",
        "ip": ip,
        "port": 8001
    }
    chat_room = ChatRoom(room_info,(ip,15555))
    dialog = ChatRoomDialog(None, chat_room, "小煤球")
    dialog.show()
    sys.exit(app.exec_())