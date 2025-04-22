import time


class ChatRoom:

    """
    ip,port,name
    """
    def __init__(self, chat_room, ip_port):
        self.broadcaster_ip_port = ip_port
        self.ip: str = chat_room.get("ip").strip()
        self.port = chat_room.get("port")

        name = chat_room.get("name").strip()
        if name == "":
            name = f"匿名聊天室 {self.ip}:{self.port}"
        elif len(name)  > 12:
            name = f"{name[:12]}..."
        self.name: str = name

        self.update_time = time.time()

    def key(self):
        return f"{self.ip}:{self.port}"

    # def __repr__(self):
    #     return f"{self.name} ({self.ip}:{self.port})"

    def __str__(self):
        return f"{self.name}【来自{self.broadcaster_ip_port[0]}】\t({self.ip}:{self.port})"