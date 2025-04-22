from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
sys.path.append("../")
from ui.Ui_net_assist_widget import Ui_NetAssistWidget
from common import utiles
import socket
import threading
import datetime

class NetAssistWidget(QWidget):
    
    def __init__(self,parent=None):
        super().__init__(parent)
        #创建对象
        self.main_window:QMainWindow = parent
        self.ui = Ui_NetAssistWidget()
        self.tcp_client = None
        self.tcp_server = None
        self.udp_socket = None
        self.tcp_server_clients = {}
        #初始化内容
        self.ui.setupUi(self)
        
        #初始化ui
        self.init_ui()
    
        
    def update_client_connect_status(self):
        """
        根据连接状态,更新按钮界面内容
        self.tcp_client is not None 已连接
        self.tcp_client is None 未连接
        """
        if self.tcp_client is None:
            #修改连接按钮图标和文字
            icon = QIcon()
            icon.addPixmap(QPixmap(":/icon/disc1"))
            self.ui.btn_connect.setIcon(icon)
            self.ui.btn_connect.setText("连接服务器")
        else:
            icon = QIcon()
            icon.addPixmap(QPixmap(":/icon/connect1"))
            self.ui.btn_connect.setIcon(icon)
            self.ui.btn_connect.setText("已连接(断开连接)")
    
    
    def run_tcp_client(self,target_ip,target_port):
        try:#创建socket对象
            self.tcp_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            target_addr = (target_ip,int(target_port))
            self.tcp_client.connect(target_addr)
            print("2.服务器连接成功")
            bar:QStatusBar = self.main_window.statusBar()
            bar.showMessage(f"连接{target_addr}服务器成功",3000)
            #更新本地IP和端口
            local_ip,local_port = self.tcp_client.getsockname() #获取本地分配到IP和port
            self.ui.cb_local_ip.setCurrentIndex(self.ui.cb_local_ip.findText(local_ip))
            self.ui.edit_local_port.setText(str(local_port))
                
            #修改连接按钮图标和文字
            self.update_client_connect_status()
            
            #循环接受服务端发来的数据
            while True:
                bytes_data = self.tcp_client.recv(2048)
                if bytes_data:
                    str_data = utiles.decode_data(bytes_data)
                    print(f"3.str_data:{str_data}")
                    self.ui.edit_recv.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]{str_data}")
                else:
                    #服务器关闭返回0字节
                    print("服务器关闭")
                    break
                
        except Exception as e:
            print(e)
            bar:QStatusBar = self.main_window.statusBar()
            bar.showMessage(f"连接失败:{e}",3000)
        finally:
            if self.tcp_client is not None:
                print("4.连接关闭")
                self.tcp_client.close()
                self.tcp_client = None
                self.update_client_connect_status()   
    
    
    def handle_client(self):
        if self.tcp_client is not None:
            print("已断开连接")
            #修改连接按钮图标和文字
            self.tcp_client.close()
            self.tcp_client = None
            self.update_client_connect_status()
            return
                
        print("1.连接服务器")
        target_ip = self.ui.edit_target_ip.text()
        target_port = self.ui.edit_target_port.text()
            
        if target_ip == "" or target_port == "":
            print("请先输入IP和端口号")
            QMessageBox.warning(self,"警告","请先输入IP和端口号")
            return
            
        thread = threading.Thread(target=self.run_tcp_client,args=(target_ip, target_port),daemon=True)
        thread.start()       
    
                         
    def update_server_connect_status(self):
        """
        根据连接状态,更新按钮界面内容
        self.tcp_server is not None 已连接
        self.tcp_server is None 未连接
        """
        if self.tcp_server is None:
            #修改连接按钮图标和文字
            print("服务器已断开连接")
            icon = QIcon()
            icon.addPixmap(QPixmap(":/icon/disc1"))
            self.ui.btn_connect.setIcon(icon)
            self.ui.btn_connect.setText("连接网络")
        else:
            icon = QIcon()
            icon.addPixmap(QPixmap(":/icon/connect1"))
            self.ui.btn_connect.setIcon(icon)
            self.ui.btn_connect.setText("已连接(断开连接)")   
    
            
    def handle_new_client(self,client_socket:socket.socket,client_addr):
        try:
            while True:
                bytes_data = client_socket.recv(2048)
                if bytes_data:
                    msg = utiles.decode_data(bytes_data)
                    self.ui.edit_recv.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][{client_addr}]{msg}")
                else:
                    break 
        except Exception as e:
            print(e)
        finally:
            print(f"客户端{client_addr}断开连接")
            self.ui.cb_connect_person.removeItem(self.ui.cb_connect_person.findText(str(client_addr)))
            del self.tcp_server_clients[str(client_addr)]
            client_socket.close()           
    
    
    def run_tcp_server(self,server_ip,server_port):
        self.tcp_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.tcp_server.bind((server_ip,int(server_port)))
        self.tcp_server.listen(128)
        self.update_server_connect_status()
        
        try:
            while True:
                client_socket,client_addr = self.tcp_server.accept()
                print(f"有新的客户端{client_addr}接入")
                self.tcp_server_clients[str(client_addr)] = client_socket
                self.ui.cb_connect_person.addItem(str(client_addr))
                thread = threading.Thread(target=self.handle_new_client,args=(client_socket,client_addr),daemon=True)
                thread.start() 
        except Exception as e:
            print(e)
        finally:
            if self.tcp_server is not None:
                self.tcp_server.close() 
                self.tcp_server = None
                self.update_server_connect_status()    
        
     
    def handle_server(self):
        if self.tcp_server is not None:
            self.tcp_server.close()
            self.tcp_server = None
            self.ui.cb_connect_person.clear()
            self.update_server_connect_status()
            return

        
        print("开启服务器")
        server_ip = self.ui.edit_target_ip.text()
        server_port = self.ui.edit_target_port.text()

        if server_port == "":
            print("请先输入端口号")
            QMessageBox.warning(self,"警告","请先输入端口号")
            return
        
        bar:QStatusBar = self.main_window.statusBar()
        bar.showMessage("服务器开启成功",3000)
        thread = threading.Thread(target=self.run_tcp_server,args=(server_ip,server_port),daemon=True)
        thread.start()
    
               
    def update_udp_connect_status(self):
        """
        根据连接状态,更新按钮界面内容
        self.udp_socket is not None 已连接
        self.udp_socket is None 未连接
        """
        if self.udp_socket is None:
            #修改连接按钮图标和文字
            print("服务器已断开连接")
            icon = QIcon()
            icon.addPixmap(QPixmap(":/icon/disc1"))
            self.ui.btn_connect.setIcon(icon)
            self.ui.btn_connect.setText("连接网络")
        else:
            icon = QIcon()
            icon.addPixmap(QPixmap(":/icon/connect1"))
            self.ui.btn_connect.setIcon(icon)
            self.ui.btn_connect.setText("已连接(断开连接)")  
     
                   
    def run_udp(self,local_ip,local_port):
        self.udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.udp_socket.bind((local_ip,int(local_port)))
        print("连接成功")
        bar:QStatusBar = self.main_window.statusBar()
        bar.showMessage("连接成功",3000)
        self.update_udp_connect_status()
        try:
            while True:
                bytes_data,udp_connect_addr = self.udp_socket.recvfrom(1024)
                self.ui.cb_connect_person.addItem(str(udp_connect_addr))
                msg = utiles.decode_data(bytes_data)
                print(msg)
                self.ui.edit_recv.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[{str(udp_connect_addr)}]{msg}")
        except Exception as e:
            print(e)
        finally:       
            if self.udp_socket is not None:     
                self.udp_socket.close()
                self.udp_socket = None
                self.update_udp_connect_status()
      
                     
    def handle_udp(self):
        if self.udp_socket is not None:
            print("已断开连接")
            #修改连接按钮图标和文字
            self.udp_socket.close()
            self.udp_socket = None
            self.update_udp_connect_status()
            return
            
        local_ip = self.ui.edit_target_ip.text()
        local_port = self.ui.edit_target_port.text()
        if local_port == "":
            print("请先输入端口号")
            QMessageBox.warning(self,"警告","请先输入端口号")
            return
        
        thread = threading.Thread(target=self.run_udp,args=(local_ip,local_port),daemon=True)
        thread.start()
    
             
    def on_connect_clicked(self):
        self.index = self.ui.cb_mode.currentIndex()
        if self.index == 0:
            self.handle_client()
        elif self.index == 1:
            self.handle_server()
        elif self.index == 2:
            self.handle_udp()
    
            
    def on_send_clicked(self):
        if self.index == 0:
            #判断是否连接
            if self.tcp_client is None:
                print("请先建立连接")
                return
            #取出用户输入的内容
            text = self.ui.edit_send.toPlainText()
            print(text)
            self.tcp_client.send(text.encode("UTF-8"))
            
        elif self.index == 1:
            #判断是否连接
            if self.tcp_server is None:
                print("请先建立连接")
                return
            text = self.ui.edit_send.toPlainText()
            current_client_addr = self.ui.cb_connect_person.currentText()
            self.tcp_server_clients[current_client_addr].send(text.encode("UTF-8"))
        
        elif self.index == 2: 
            #判断是否连接
            if self.udp_socket is None:
                print("请先建立连接")
                return
            #取出用户输入的内容
            text = self.ui.edit_send.toPlainText()
            target_str = self.ui.cb_connect_person.currentText()
            print(target_str)
            self.udp_socket.sendto(text.encode("UTF-8"), eval(target_str))
    
              
    def on_mode_changed(self):
        self.index = self.ui.cb_mode.currentIndex()
        if self.index == 0:
            self.ui.label_ip.setText("服务器IP:")
            self.ui.label_port.setText("服务器端口")
            self.ui.btn_connect.setText("连接服务器")
            self.ui.label_connect_person.hide()
            self.ui.cb_connect_person.hide()
            self.ui.label_local_ip.show()
            self.ui.label_local_port.show()
            self.ui.cb_local_ip.show()
            self.ui.edit_local_port.show()
        elif self.index == 1 or self.index == 2:
            self.ui.label_ip.setText("本地IP:")
            self.ui.label_port.setText("本地端口:")
            self.ui.btn_connect.setText("连接网络")
            self.ui.label_local_ip.hide()
            self.ui.label_local_port.hide()
            self.ui.cb_local_ip.hide()
            self.ui.edit_local_port.hide()
            self.ui.label_connect_person.show()
            self.ui.cb_connect_person.show()
     
                 
    def init_ui(self):
        self.ui.edit_target_ip.setText("127.0.0.1")
        self.ui.edit_target_port.setText("8888")
        local_ips = utiles.get_local_ip()
        self.ui.cb_local_ip.addItems(local_ips)
        self.index = 0
        self.ui.label_connect_person.hide()
        self.ui.cb_connect_person.hide()
        self.ui.btn_connect.clicked.connect(self.on_connect_clicked)
        self.ui.btn_send.clicked.connect(self.on_send_clicked)
        self.ui.cb_mode.currentIndexChanged.connect(self.on_mode_changed)
  
        
def main():
    app = QApplication(sys.argv)
    window = NetAssistWidget()
    window.show()
    sys.exit(app.exec_())
      
      
if __name__ == '__main__':
    main()
