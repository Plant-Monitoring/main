import serial
import serial.tools.list_ports
from typing import Optional
import struct

class STM32:
    """
    Interface for communicating with an STM32 device over serial.
    """

    CRC16_POLY = 0xA001 
    """CRC-16/Modbus polynomial in reflected form."""

    def __init__(self, port):
        """
        Initialize serial connection to STM32 device.
        
        Args:
            port: Serial port name (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            
        Raises:
            serial.SerialException: If the port cannot be opened
        """
        self.ser = serial.Serial(port=f'{port}', baudrate=115200, timeout=1)

    def send_command(self, command):
        """
        Send a text command to the STM32 device.
        
        Commands are sent as UTF-8 encoded strings with a newline terminator.
        
        Args:
            command: Command string to send (without newline)
        """
        self.ser.write((f"{command}\n").encode('utf-8'))

    def receive_line(self) -> bytes:
        """
        Read a single line from the serial port.
        
        Returns:
            Bytes object containing the line (including newline if present)
        """
        return self.ser.readline()

    def receive_data(self, size : int) -> bytes:
        """
        Read exactly `size` bytes from the serial port.
        
        Args:
            size: Number of bytes to read
            
        Returns:
            Bytes object containing the received data
        """
        return self.ser.read(size)
    
    def receive_file(self, file: str) -> bytes:
        """
        Request and receive a file from the STM32 device.
        
        Sends a GET command and parses the response metadata to determine
        the file size, then reads the raw file data.
        
        Args:
            file: Name of the file to request
            
        Returns:
            Raw bytes of the file (including packet framing)
            
        Raises:
            ValueError: If the response metadata format is unexpected
        """
        self.send_command(f"GET {file}")

        self.receive_line()
        meta = self.receive_line().decode('utf-8')
        ind = meta.find("bytes")
        
        return self.receive_data(int(meta[11 : ind - 1]))
    
    def save_file_locally(self, file: str):
        """
        Using receive_file to load the desired file, then saves it locally
        
        Args:
            file: Name of the file to request
        """
        data = self.receive_file(file)

        with open(f"{file}", 'wb') as local:
            local.write(data)

    @staticmethod
    def unstuff(data : bytes) -> bytes:
        """
        Remove byte stuffing from raw data.
        
        Decodes escaped sequences:\n
        - 0xFE 0x00 → 0xFE\n
        - 0xFE 0x01 → 0xFF\n
        - 0xFE 0xE4 → 0x1A (Ctrl+Z)\n
        
        Args:
            data: Stuffed bytes to decode
            
        Returns:
            Unstuffed bytes
        """
        retData = b''
        i = 0
        while i < len(data):
            if data[i : i + 1] == b'\xfe' and i + 1 < len(data):
                retData += bytes([data[i] ^ data[i + 1]])
                i += 2
            else:
                retData += data[i : i + 1]
                i += 1

        return retData
    
    @staticmethod
    def crc16_update(crc, data):
        """
        Update CRC with one byte.
        
        Internal method used by crc16_compute. Implements the
        CRC-16/Modbus algorithm.
        
        Args:\n
            crc: Current CRC value (0-0xFFFF)\n
            data: Byte to process (0-0xFF)\n
            
        Returns:
            Updated CRC value (0-0xFFFF)
        """
        crc ^= data
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ STM32.CRC16_POLY
            else:
                crc = crc >> 1
        return crc & 0xFFFF

    @staticmethod
    def crc16_compute(data) -> int:
        """
        Compute CRC-16/Modbus over the given data.
        
        Algorithm:\n
        - Polynomial: 0xA001\n
        - Initial value: 0xFFFF\n
        - Byte order: Little-endian\n
        
        Args:
            data: Bytes to compute CRC over
            
        Returns:
            16-bit CRC value (0-0xFFFF)
        """
        crc = 0xFFFF
        for i in data:
            crc = STM32.crc16_update(crc, i)
        return crc & 0xFFFF
    
    @staticmethod
    def parse_packet(data: bytes) -> Optional[bytes]:
        """
        Parse a single packet from raw data.
        
        Extracts timestamp, chunks, and validates CRC. The packet must start
        with sync marker 0xFFFF.
        
        Packet structure (after unstuffing):\n
        - Timestamp: uint32_t (4 bytes, little-endian)\n  
        - Packet Size: uint16_t (2 bytes, little-endian) = unstuffed size - 2  \n
        - Chunks: Variable (see parse_chunks) \n
        - CRC16: uint16_t (2 bytes, little-endian)  \n
        
        Args:
            data: Raw bytes starting with sync marker
            
        Returns:
            Dictionary with keys 'timestamp' (int) and 'chunks' (dict of chunk_id -> samples)
            Returns None if packet is invalid or CRC mismatch
        """
        if data[: 2] != b'\xff\xff':
            return None
                
        unstuffed = STM32.unstuff(data[3:])
        packetNum = data[2]
        timeStamp = int.from_bytes(unstuffed[0 : 4], byteorder='little')

        packetSizeEnc = int.from_bytes(unstuffed[4 : 6], byteorder='little')
        packetSize = packetSizeEnc + 1

        crcReceived = int.from_bytes(unstuffed[-2 : ], byteorder='little')
        crcComputed = STM32.crc16_compute(unstuffed[:-2])

        if crcComputed != crcReceived :
            #print("GLUPSI")
            return None
        
        chunksData = unstuffed[6 : -2]
        chunks = {}
        pos = 0
        while pos < len(chunksData):
            chunkId = chunksData[pos]
            chunkSizeEnc = int.from_bytes(chunksData[pos + 1 : pos + 3], byteorder='little')
            chunkSize = chunkSizeEnc + 1
            res = chunksData[pos + 3]
            chunk = chunksData[pos + 4 : pos + 4 + chunkSize]
            
            samples = []
            for i in range(0, chunkSize, 6):
                x, y, z = struct.unpack('<hhh', chunk[i:i+6])
                samples.append((x, y, z))
            
            chunks[chunkId] = samples
            pos += 4 + chunkSize


        return {'timestamp': timeStamp, 'chunks': chunks}
    
    @staticmethod
    def parse_data(data):
        """
        Parse multiple concatenated packets from a data stream.
        
        Scans for sync markers (0xFFFF) and extracts packets sequentially.
        
        Args:
            data: Raw bytes containing one or more packets
            
        Returns:
            List of parsed packet dictionaries (None for invalid packets)
        """
        markers = []
        data = data.rstrip(b'\x1a')

        for i in range(len(data)):
            if data[i : i + 2] == b'\xff\xff':
                markers.append(i)

        parsedData = []
        for i in range(len(markers)):
            if i == len(markers) - 1:
                parsedData.append(STM32.parse_packet(data[markers[i] :]))
            else:
                parsedData.append(STM32.parse_packet(data[markers[i] : markers[i + 1]]))
        
        return parsedData