from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import threading
import sys
sys.path.append("../")

from ui.Ui_serial_assist_widget import Ui_SerialAssistWidget
from drivers.driver_serial import*
from views.serial_setting_dialog import SerialSettingDialog
from common import utiles

class SerialAssistWidget(QWidget):
    
    def __init__(self,parent=None):
        super().__init__(parent)
        self.main_window:QMainWindow = parent
        self.ui = Ui_SerialAssistWidget()
        self.ui.setupUi(self)
        self.devices = []
        self.sd:SerialDevice = None
        
        self.init_ui()
        self.refresh_devices()
    
    
    def refresh_devices(self):
        self.devices = scan_serial_ports()
        device_name = [item[1] for item in self.devices]
        self.ui.cb_device.clear()    
        self.ui.cb_device.addItems(device_name)
    
    
    def update_connect_ui(self):
        if self.sd is not None:
            #当前已连接
            self.ui.label_status.setPixmap(QPixmap(":/icon/connect2"))
            self.ui.btn_connect.setText("断开连接(已连接)")
        else:
            #当前未连接
            self.ui.label_status.setPixmap(QPixmap(":/icon/disc2"))
            self.ui.btn_connect.setText("连接设备")
            
        
    def show_setting_dialog(self):
        dialog = SerialSettingDialog()
        res = dialog.exec_()
        if res == QDialog.Accepted:
            self.ui.cb_baud.setCurrentIndex(self.ui.cb_baud.findText(dialog.baudrate))
            
    
    def run_serial_assist(self,port,baud_rate,device_name):
        self.sd = SerialDevice(port,baud_rate=baud_rate,timeout=None)
        if not self.sd.open():
            print("连接失败")
            self.sd = None
            self.update_connect_ui()
            return
        
        print("连接成功")
        bar:QStatusBar = self.main_window.statusBar()
        bar.showMessage(f"{device_name}连接成功",3000)
        self.update_connect_ui()
        try:
            while True:
                data = self.sd.readline()
                data = data.rstrip()
                if data:
                    msg = utiles.decode_data(data)
                    self.ui.edit_recv.append(msg)
                    print(utiles.decode_data(data))
                else:
                    break   
        except Exception as e:
            print(e)
        finally:
            bar.showMessage(f"{device_name}已断开",3000)
            self.sd.close()
            self.sd = None
            self.update_connect_ui()
    
    
    def on_connect_clicked(self):
        if self.sd is not None:
            self.sd.close()
            self.sd = None
            self.update_connect_ui()
            return
 
        device_index = self.ui.cb_device.currentIndex()
        if device_index == -1:
            print("请先选择设备")
            QMessageBox.warning(self,"警告","请先选择设备")
            return
        
        device = self.devices[device_index]
        port = device[0]
        device_name = device[1]
        baud_rate = int(self.ui.cb_baud.currentText())
        thread = threading.Thread(target=self.run_serial_assist,args=(port,baud_rate,device_name),daemon=True)
        thread.start()
        
     
    def on_send_clicked(self):
        if self.sd == None:
            print("请先连接设备")
            QMessageBox.warning(self,"警告","请先连接设备")
            return
        
        text = self.ui.edit_send.toPlainText()
        if text == "":
            print("请先输入要发送的数据")
            QMessageBox.warning(self,"警告","请先输入要发送的数据")
            return
        self.sd.write(f"{text}\n".encode("UTF-8"))
        
    
    def init_ui(self):
        self.ui.btn_refresh.clicked.connect(self.refresh_devices)
        self.ui.btn_settings.clicked.connect(self.show_setting_dialog)
        self.ui.btn_connect.clicked.connect(self.on_connect_clicked)
        self.ui.btn_send.clicked.connect(self.on_send_clicked)


def main():
    app = QApplication(sys.argv)
    window = SerialAssistWidget()
    window.show()
    sys.exit(app.exec_())
    
    
if __name__ == '__main__':
    main()