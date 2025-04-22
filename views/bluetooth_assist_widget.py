from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys
import threading
sys.path.append("../")
from ui.Ui_bluetooth_assist_widget import Ui_BlAssistWidget
from drivers.driver_bluetooth import BluetoothDataTransfer
from common import utiles
import enum

class BluetoothStatus(enum.Enum):
    #默认状态
    DISCONNECT = 0
    #扫描中
    SCANING = 1
    #已连接
    CONNECTED = 2
    

class BlAssistWidget(QWidget):
    
    def __init__(self,parent=None):
        super().__init__(parent)
        #创建对象
        self.main_window:QMainWindow = parent
        self.ui = Ui_BlAssistWidget()
        #初始化内容
        self.ui.setupUi(self)
        self.bdt:BluetoothDataTransfer = None
        self.current_state = BluetoothStatus.DISCONNECT
        self.devices = []
        
        #初始化ui
        self.init_ui()
        
   
    def uptate_connect_ui(self):
        if self.current_state == BluetoothStatus.CONNECTED:
            #当前已连接
            self.ui.label_connect_status.setPixmap(QPixmap(":/icon/connect2"))
            self.ui.btn_connect.setText("断开连接(已连接)")  
            self.ui.btn_refresh.setEnabled(True) 
            self.ui.gb_connected.show()
            self.ui.label_device_addr.setText(self.bdt.target_address)
            self.ui.label_device_name.setText(self.bdt.target_name)
            
        elif self.current_state == BluetoothStatus.DISCONNECT:
            #当前未连接
            self.ui.label_connect_status.setPixmap(QPixmap(":/icon/disc2"))
            self.ui.btn_connect.setText("连接设备")
            self.ui.btn_refresh.setEnabled(True)
            self.ui.gb_connected.hide()
            
        else:
            #扫描中
            self.ui.btn_refresh.setEnabled(False)
            self.ui.btn_connect.setText("扫描中")
            self.ui.gb_connected.hide()
                
               
    def get_all_divices(self):
        self.devices = BluetoothDataTransfer.scan_devices()
        print(f"设备扫描完成,共找到{len(self.devices)}个设备")
        self.current_state = BluetoothStatus.DISCONNECT
        self.uptate_connect_ui()
        device_names = []
        for device in self.devices:
            name = device[1]
            if name == "":
                name = "Unknow"
            device_names.append(name)   
            print(device)
            
        self.ui.cb_divices.addItems(device_names)

    
    def init_data(self):
        self.ui.cb_divices.clear()
        print("正在扫描设备...")
        self.current_state = BluetoothStatus.SCANING
        self.uptate_connect_ui()
        thread = threading.Thread(target=self.get_all_divices,daemon=True)
        thread.start()
    
    
    def run_bluetooth_assist(self,device):
        
        addr,name = device
        print(device)
        self.bdt = BluetoothDataTransfer(addr,name,1)
        if not self.bdt.connect():
            print("连接失败")
            return
         
        print("连接成功")   
        self.current_state = BluetoothStatus.CONNECTED
        bar:QStatusBar = self.main_window.statusBar()
        bar.showMessage(f"连接{name}成功",3000)
        self.uptate_connect_ui()
        try:
            while True:
                bytes_data = self.bdt.receive_data()
                if bytes_data:
                    msg = utiles.decode_data(bytes_data)
                    self.ui.edit_recv.append(msg)
                else:
                    #主动调用disconnect或被动断开，bytes_data会收到长度为0的bytes
                    break
        except Exception as e:
            print(e)
        finally:
            print("蓝牙设备已断开")
            bar.showMessage(f"{name}已断开",3000)
            self.bdt.disconnect()
            self.bdt = None
            self.current_state = BluetoothStatus.DISCONNECT
            self.uptate_connect_ui()
        
        
    def on_connect_clicked(self):
        if self.current_state == BluetoothStatus.SCANING:
            return
        
        if self.current_state == BluetoothStatus.CONNECTED:
            self.bdt.disconnect()
            self.bdt = None
            self.current_state = BluetoothStatus.DISCONNECT
            self.uptate_connect_ui()
            return
        
        device_index = self.ui.cb_divices.currentIndex()
        if device_index == -1:
            print("请先选择设备")
            QMessageBox.warning(self,"警告","请先选择设备")
            return
        
        device = self.devices[device_index]
        thread = threading.Thread(target=self.run_bluetooth_assist,args=(device,),daemon=True)
        thread.start()
       
      
    def on_send_clicked(self):
        if self.bdt == None:
            print("请先连接设备")
            QMessageBox.warning(self,"警告","请先连接设备")
            return
        
        text = self.ui.edit_send.toPlainText()
        if text == "":
            print("请先输入要发送的数据")
            QMessageBox.warning(self,"警告","请先输入要发送的数据")
            return

        print(text)
        self.bdt.send_data(text)
      
        
    def init_ui(self):
        self.uptate_connect_ui()
        self.ui.btn_refresh.clicked.connect(self.init_data)
        self.ui.btn_connect.clicked.connect(self.on_connect_clicked)
        self.ui.btn_send.clicked.connect(self.on_send_clicked)


def main():
    app = QApplication(sys.argv)
    window = BlAssistWidget()
    window.show()
    sys.exit(app.exec_())
    
    
if __name__ == '__main__':
    main()