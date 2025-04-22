"""
MainWindow -> ToolBar,MenuBar,StatusBar

1.网络工具
2.串口工具
3.蓝牙助手
4.物联网数据平台
5.小车上位控制器
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
from ui.Ui_main_window import Ui_MainWindow
from views.net_assist_widget import NetAssistWidget
from views.serial_assist_widget import SerialAssistWidget
from views.bluetooth_assist_widget import BlAssistWidget
from views.chat_rooms_widget import ChatRoomsWidget

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        #创建对象
        self.ui = Ui_MainWindow()
        #初始化内容
        self.ui.setupUi(self)
        #初始化ui
        self.init_ui()
        
        
    def init_ui(self):
        self.ui.tabWidget.addTab(NetAssistWidget(self),"网络工具")
        self.ui.tabWidget.addTab(SerialAssistWidget(self),"串口助手")
        self.ui.tabWidget.addTab(BlAssistWidget(self),"蓝牙助手")
        self.ui.tabWidget.addTab(ChatRoomsWidget(self),"聊天室")
        #self.ui.tabWidget.setCurrentIndex(0)
        #self.ui.tabWidget.setCurrentIndex(1)
        #self.ui.tabWidget.setCurrentIndex(2)
        self.ui.tabWidget.setCurrentIndex(3)
        
        bar = self.statusBar()
        bar.showMessage("请点击连接",3000)
        

def main():
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    
    
if __name__ == '__main__':
    main()

