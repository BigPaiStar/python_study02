import bluetooth


# 扫描所有设备
class BluetoothDataTransfer:
    def __init__(self, target_address, target_name, port=1):
        self.target_address = target_address
        self.target_name = target_name
        self.port = port
        self.socket = None

    def connect(self):
        """
        连接蓝牙设备
        :return:
        """
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((self.target_address, self.port))
            print("Connected successfully. {} ({})".format(
                self.target_name, self.target_address
            ))
            return True
        except bluetooth.BluetoothError as e:
            self.socket = None
            print("Connection failed:", str(e))

        return False

    def disconnect(self):
        """
        断开蓝牙连接
        :return:
        """
        if self.socket is not None:
            self.socket.close()
            print("Disconnected.")

    def send_data(self, data):
        """
        发送数据
        :param data:
        :return:
        """
        if self.socket is not None:
            try:
                self.socket.send(data)
                print("Data sent:", data)
                return True
            except bluetooth.BluetoothError as e:
                print("Failed to send data:", str(e))
        else:
            print("Not connected.")
        return False

    def receive_data(self, buffer_size=1024):
        """
        接收数据
        :param buffer_size:
        :return:
        """
        if self.socket is not None:
            try:
                data = self.socket.recv(buffer_size)
                # print("Data received:", data.decode())
                return data
            except bluetooth.BluetoothError as e:
                print("Failed to receive data:", str(e))
        else:
            print("Not connected.")

    @staticmethod
    def scan_devices():
        """
        扫描所有蓝牙设备
        :return:
        """
        devices = bluetooth.discover_devices()
        print("Scanning devices...")
        device_list = []
        for addr in devices:
            name = bluetooth.lookup_name(addr)
            #print("Found device:", name, "(", addr, ")")
            device_list.append((addr, name))
        return device_list


if __name__ == '__main__':
    devices = BluetoothDataTransfer.scan_devices()
    for device in devices:
         print(device)

    # 电脑PC，通过USB  串口（STC8核心 3.0, 3.1）  蓝牙设备
    
    # 示例用法
    bd = BluetoothDataTransfer('80:99:E7:A2:0B:DD', 'WF-1000XM5', 1)  # 替换为目标设备的蓝牙地址和端口号
    if bd.connect():
        bd.send_data("Hello, Bluetooth!")  # 发送数据
        bytes_arr = bd.receive_data()  # 接收数据
        print(bytes_arr.decode("GBK"))
        bd.disconnect()
        print("断开连接")