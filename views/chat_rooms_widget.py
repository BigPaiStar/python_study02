import json
import socket
import sys
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
sys.path.append("../")
from common.qt_worker import Worker
from common.utiles import decode_data
from models.chat_models import ChatRoom
from ui.Ui_chat_rooms_widget import Ui_ChatRoomsWidget
from views.chat_room_dialog import ChatRoomDialog

BUFFER_SIZE = 2048


# 自定义RoomModel，用来显示聊天室列表
class RoomModel(QAbstractListModel):

    def __init__(self, rooms: list, parent=None):
        super().__init__(parent)
        self.datas: list[ChatRoom] = rooms

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.datas)

    def data(self, index: QModelIndex, role=None):
        if role == Qt.DisplayRole:
            return str(self.datas[index.row()])

    # 根据索引获取聊天室
    def get_data(self, index):
        return self.datas[index]

    def update_data(self, rooms):
        self.datas = rooms
        self.layoutChanged.emit()


class ChatRoomsWidget(QWidget):

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # 创建对象
        self.ui = Ui_ChatRoomsWidget()
        self.ui.setupUi(self)

        # self.setWindowModality(Qt.NonModal)

        # 初始化内容
        # self.manager = ThreadManager()
        # ----------------------------------------------------------------
        self.is_recv = True
        # refresh_worker = Worker(self.run_recv_thread, listen=8000)
        # refresh_worker.signal_connect(msg_handler=self.on_room_msg_handler)
        # self.manager.start_worker(refresh_worker)
        self.worker_thread = Worker(self.run_recv_thread, kwargs={"listen": 8000})
        self.worker_thread.signal_connect(msg_handler=self.on_room_msg_handler)
        self.worker_thread.start()
        # ---------------------------------------------------------------
        self.chat_rooms = {}
        # 初始化一些临时测试的聊天室列表数据
        # self.model = QStringListModel()
        self.model = RoomModel([])

        # 初始化ui
        self.init_ui()

        # 初始化数据
        self.init_data()

        # 开启定时任务，定时5s移除过期的聊天室（超过10秒未收到此聊天室广播），并更新列表
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.clear_chat_rooms)
        self.timer.start(5000)

    def clear_chat_rooms(self):
        # 移除过期的聊天室
        now = time.time()
        copy_rooms = self.chat_rooms.copy()
        for key, room in copy_rooms.items():
            if now - room.update_time > 10:
                self.chat_rooms.pop(key)
        # 更新列表
        self.update_chat_room_list()

    def __del__(self):
        if self.worker_thread:
            self.worker_thread.stop()

    def run_recv_thread(self, worker: Worker, listen):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            udp_socket.bind(("", listen))
            while worker.is_running:
                try:
                    recv_data, ip_port = udp_socket.recvfrom(BUFFER_SIZE)
                    recv_msg = decode_data(recv_data)
                    worker.emit_msg((recv_msg, ip_port))
                except Exception as e:
                    print(e)
                    break

        return "聊天室列表接收线程结束"

    def on_room_msg_handler(self, recv_data):
        recv_msg, ip_port = recv_data
        # 解析并将聊天室信息加入到聊天室列表
        try:
            chat_room = json.loads(recv_msg)
        except Exception as e:
            # 如果解析失败，直接返回
            return

        if not isinstance(chat_room, dict):
            # 如果不是字典，直接返回
            return

        if not all([key in chat_room for key in ["ip", "port", "name"]]):
            # 如果不包含ip、port、name三个key，则不是聊天室，不添加
            return

        print("recv {} room: {}".format(ip_port, chat_room))

        room = ChatRoom(chat_room, ip_port)

        self.chat_rooms["{}:{}".format(*ip_port)] = room
        self.update_chat_room_list()

    def init_ui(self):
        # 列表数据可选中不可编辑
        self.ui.listView.setEditTriggers(self.ui.listView.NoEditTriggers)
        # 列表数据单选
        self.ui.listView.setSelectionMode(self.ui.listView.SingleSelection)
        # 列表条目双击事件
        self.ui.listView.doubleClicked.connect(self.on_list_item_double_clicked)

        self.ui.btn_join.clicked.connect(self.on_btn_join)
        self.ui.btn_create.clicked.connect(self.on_btn_create)

    def on_btn_join(self):
        # 获取选中的聊天室
        selected_index = self.ui.listView.currentIndex()
        # print(selected_index, selected_index.row(), type(selected_index))
        if selected_index is None or selected_index.row() == -1:
            print("未选中条目")
            return

        room = self.model.get_data(selected_index.row())

        self.join_chat(room)

    def join_chat(self, room):
        nickname, confirm = QInputDialog.getText(self, "加入聊天室", "请输入昵称", text="")
        if not confirm:
            return

        nickname = nickname.strip()
        if not nickname:
            QMessageBox.warning(self, "警告", "昵称不能为空")
            return

        dialog = ChatRoomDialog(self, room, nickname)
        dialog.show()

    def on_btn_create(self):
        print("create click")

    def on_list_item_double_clicked(self, selected_index: QModelIndex):
        room = self.model.get_data(selected_index.row())
        print("join room:", room)
        self.join_chat(room)

    def init_data(self):
        self.ui.listView.setModel(self.model)
        # 初始化一些假的测试数据
        # self.chat_rooms["1"] = ChatRoom(ip="1", port=11, name="111")
        # self.chat_rooms["2"] = ChatRoom(ip="2", port=22, name="222")
        # self.chat_rooms["3"] = ChatRoom(ip="3", port=33, name="333")
        self.model.update_data(list(self.chat_rooms.values()))

    def update_chat_room_list(self):
        # 将self.chat_rooms转成字符串列表，格式为 name (ip:port)
        chat_rooms = list(self.chat_rooms.values())
        # 对values里的值按照字符串排序
        chat_rooms.sort(key=lambda x: str(x))

        self.model.update_data(chat_rooms)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = ChatRoomsWidget()
    window.show()

    sys.exit(app.exec_())