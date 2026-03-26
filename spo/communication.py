import serial
import serial.tools.list_ports

class STM32:
    def __init__(self, port):
        self.ser = serial.Serial(port=f'{port}', baudrate=115200, timeout=1)

    def send_command(self, command):
        self.ser.write((f"{command}\n").encode('utf-8'))

    def receive_line(self) -> bytes:
        return self.ser.readline()

    def receive_data(self, size : int) -> bytes:
        return self.ser.read(size)
    
    def receive_file(self, file: str) -> bytes:
        self.send_command(f"GET {file}")

        self.receive_line()
        meta = self.receive_line().decode('utf-8')
        ind = meta.find("bytes")
        
        return self.receive_data(int(meta[11 : ind - 1]))