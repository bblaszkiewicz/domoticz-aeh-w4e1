'''
Python module and client for Hisense AEH-W4A1 wifi module
By Davide Varricchio https://github.com/bannhead/pyaehw4a1

### Modified by x-th-unicorn for Domoticz - Python plugin ###
Changes:
 * Rewritten without using "asyncio", the Domoticz plugin system crashed after about half an hour when using the original module
 * Added the "_connect" function
 * Changed the "version" function"
 * Some other small changes
'''

import socket
import ipaddress

from .commands import ReadCommand
from .commands import UpdateCommand
from .responses import ResponsePacket
from .responses import DataPacket
from .exceptions import *

class Domoticz_AehW4a1:

    strVersion = ""

    def __init__(self, host=None):
        if host is None:
            self._host = None
        else:
            self._host = host

    def check(self):

        bData = self._send_recv_packet(bytes("AT+XMV", 'utf-8'))

        if bytes("+XMV:", 'utf-8') in bData:
            self.strVersion = bData.decode('utf-8').replace("+XMV:","")
            return True

        raise ConnectionError(f"Unknown device {self._host}")

    def version(self):
        if self.strVersion != "":
            return self.strVersion
        elif self.check():
            return self.strVersion
        else:
            return "N/A"

    def _connect(self):
        if not self._host:
            raise ConnectionError("Host required")

        try:
            ipaddress.IPv4Network(self._host)
        except ValueError:
            raise ConnectionError(f"Invalid IP address: {self._host}") from None

        try:
            objConnect = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            objConnect.connect((self._host, 8888))
            objConnect.settimeout(5)

            return objConnect

        except:
            raise ConnectionError(f"AC unavailable at {self._host}") from None

    def command(self, command):
        for name, member in ReadCommand.__members__.items():
            if command == name:
                return self._read_command(member)
        for name, member in UpdateCommand.__members__.items():
            if command == name:
                if command == "temp_to_F":
                    self._update_command(member)
                    return self.command("temp_to_F_reset_temp")
                elif command == "temp_to_C":
                    self._update_command(member)
                    return self.command("temp_to_C_reset_temp")
                else:
                    return self._update_command(member)

        raise UnkCmdError(f"Not yet implemented: {command}")

    def _update_command(self, command):
        pure_bytes = self._send_recv_packet(command.value)
        packet_type =  self._packet_type(pure_bytes)
        if self._check_response(packet_type, pure_bytes):
            return True

        raise UnkPacketError(f"Unknown packet type {packet_type}: {pure_bytes.hex()}")

    def _read_command(self, command):
        pure_bytes = self._send_recv_packet(command.value)
        packet_type = self._packet_type(pure_bytes)
        data_start_pos = self._check_response(packet_type, pure_bytes)
        if data_start_pos:
            result = self._bits_value(packet_type, pure_bytes, data_start_pos)
            return result

        raise UnkPacketError(f"Unknown packet type {packet_type}: {pure_bytes.hex()}")

    def _send_recv_packet(self, command_bytes):
        try:
            objConnect = self._connect()
            objConnect.send(command_bytes)
            bData = bytes("", 'utf-8')

            while True:
                try:
                    bReadBytes = objConnect.recv(1024)
                    if not bReadBytes or bReadBytes == bytes("\r\n", 'utf-8'):
                        break
                    bData += bReadBytes
                except socket.timeout:
                    break
            return bData

        except:
            raise ConnectionError(f"AC unavailable at {self._host}") from None
        finally:
            objConnect.close()

    def _bits_value(self, packet_type, pure_bytes, data_pos):
        result = {}
        binary_string = f"{int(pure_bytes.hex(),16):08b}"
        binary_data = binary_string[data_pos*8:-24]
        for data_packet in DataPacket:
            if packet_type in data_packet.name:
                for field in data_packet.value:
                    result[field.name] = binary_data[(field.offset - 1):
                                        (field.offset + field.length - 1)]
                return result

        raise UnkDataError(f"Unknown data type {packet_type}: {binary_data}")

    def _packet_type(self, string):
        type = int(string[13:14].hex(),16)
        sub_type = int(string[14:15].hex(),16)
        result = f"{type}_{sub_type}"
        return result

    def _check_response(self, packet_type, pure_bytes):
        for response_packet in ResponsePacket:
            if packet_type in response_packet.name:
                if response_packet.value not in pure_bytes:
                    raise WrongRespError(f"Wrong response for type {packet_type}: {pure_bytes.hex()}")
                return len(response_packet.value)
        return False
