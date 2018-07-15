import asyncio
import struct
import hashlib
import random
from binascii import hexlify

from prudp.server import PRUDPV0Transport
from prudp.protocols import protocol_list
from prudp.events import Scheduler, Event
from rc4 import RC4

from nintendo.nex.streams import StreamOut

import traceback

def build_nex_request(protocol, method, call_id, data):
    req_header = struct.pack("<I", len(data) + 9)
    req_header += struct.pack("B", protocol | 0x80)
    req_header += struct.pack("<I", call_id)
    req_header += struct.pack("<I", method)
    return req_header + data

class NEXClient:
    def __init__(self, server):
        self.server = server
        self.transport = None
        self.user = None
        self.last_call_id = 0
        self.cached_protos = {}

    def handle_nex_payload(self, data):
        success = True
        result = 0

        if self.transport.connected:
            global protocol_list

            response = None
            call_id = None

            data_len = struct.unpack("<I", data[0:4])[0]
            proto_with_flag = data[4]
            proto_id = proto_with_flag & ~0x80
            proto = None
            if proto_id in protocol_list:
                if proto_id in self.cached_protos:
                    proto = self.cached_protos[proto_id]
                else:
                    proto = protocol_list[proto_id](self)
                    self.cached_protos[proto_id] = proto

            if proto_with_flag & 0x80:
                # Request.
                call_id = struct.unpack("<I", data[5:9])[0]
                method = struct.unpack("<I", data[9:13])[0]
                arg_data = data[13:data_len+13]

                print("Call: {:08x}, method: {:08x}, proto {:x}".format(call_id, method, proto_id))
                if not proto:
                    print("Unknown protocol number {:02x} (call {:x})".format(proto_id, call_id))
                    success = False
                    result = 0x80010002 # Core::Unknown
                elif not method in proto.methods:
                    print("Unknown method {:08x} on protocol {:02x} call {:x}!".format(method, proto_id, call_id))
                    success = False
                    result = 0x80010002 # Core::Unknown
                else:
                    try:
                        success, result, response = proto.methods[method](arg_data)
                    except Exception as e:
                        print("Got exception!")
                        traceback.print_exc()

                        success = False
                        result = 0x80010005 # Core::Exception
                        response = b''

                if success:
                    if response == None:
                        response = b''
                    response_data_len = len(response) + 10
                else:
                    response_data_len = 10

                resp_header = struct.pack("<I", response_data_len)
                resp_header += struct.pack("B", proto_with_flag & ~0x80)
                resp_header += struct.pack("B", success)
                if success:
                    resp_header += struct.pack("<I", call_id)
                    resp_header += struct.pack("<I", method | 0x8000)
                else:
                    resp_header += struct.pack("<I", result)
                    resp_header += struct.pack("<I", call_id)

                print("Response: result {}, success {}".format(result,success))
                # Send a response.
                data = resp_header
                if success:
                   data += response
                self.transport.send_data(data)
                return True
            else:
                pass
                # Response?

    def send_notification(self, notif_type, pid, payload):
        #todo: pack Data properly!
        stream = StreamOut()
        stream.u32(notif_type)
        stream.u32(pid)
        payload_stream = StreamOut()
        payload.streamin(payload_stream)
        stream.string(payload.get_name())
        stream.u32(len(payload_stream.data) + 4)
        stream.buffer(payload_stream.data)

        packet = build_nex_request(0x64, 0x01, random.randint(0, 0xffffffff), stream.data)
        self.transport.send_data(packet)

def disconnect_all(ev, server):
    for ip in server.connections:
        server.connections[ip].disconnect()

def stop_all(ev, server):
    server.scheduler.stop()
    server.transport.close()

class NEXServerBase(asyncio.DatagramProtocol):
    def __init__(self, access_key, sig_version, server_ip=None, secure_port=None, secure_key=None, secure_key_length=None):
        super().__init__()
        self.access_key = access_key
        self.secure_key = secure_key
        self.secure_port = secure_port
        if self.secure_key:
            self.secure_key_length = len(self.secure_key)
        else:
            self.secure_key_length = secure_key_length

        self.sig_version = sig_version
        self.server_ip = server_ip

        self.connections = {}
        self.scheduler = Scheduler()
        self.scheduler.go_task = asyncio.ensure_future(self.scheduler.go())

        self.data_sig_key = hashlib.md5(self.access_key).digest()
        self.checksum_base = sum(self.access_key)

    def schedule_stop(self):
        if len(self.connections) > 0:
            disconnect_1_event = Event(disconnect_all, 0.5, params=(self,))
            disconnect_2_event = Event(disconnect_all, 1, params=(self,))
            disconnect_3_event = Event(disconnect_all, 1.5, params=(self,))
            stop_scheduler_and_server = Event(stop_all, 2, params=(self,))
            self.scheduler.add(disconnect_1_event)
            self.scheduler.add(disconnect_2_event)
            self.scheduler.add(disconnect_3_event)
            self.scheduler.add(stop_scheduler_and_server)
        else:
            stop_scheduler_and_server = Event(stop_all, 0, params=(self,))
            self.scheduler.add(stop_scheduler_and_server)

    def connection_made(self, transport):
        self.transport = transport

    def sendto(self, data, addr):
        return self.transport.sendto(data, addr)

class NEXAuthServer(NEXServerBase):
    def __init__(self, access_key, secure_port, secure_key_length, server_ip, sig_version):
        super().__init__(access_key=access_key, secure_port=secure_port, secure_key_length=secure_key_length, server_ip=server_ip, sig_version=sig_version)

    def datagram_received(self, data, addr):
        if not addr in self.connections:
            client = NEXClient(self)
            if data[0:2] == b'\xaf\xa1':
                transport = PRUDPV0Transport(b"CD&ML", self, client, addr)
            else:
                raise NotImplementedError("Invalid packet / not PRUDP v0!")
            client.transport = transport
            self.connections[addr] = client
        else:
            client = self.connections[addr]
            transport = client.transport

        packet = transport.handle_data(data)

class NEXSecureServer(NEXServerBase):
    def __init__(self, access_key=None, secure_key=None, server_ip=None, sig_version=None):
        super().__init__(access_key=access_key, secure_key=secure_key, server_ip=server_ip, sig_version=sig_version)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if not addr in self.connections:
            client = NEXClient(self)
            if data[0:2] == b'\xaf\xa1':
                transport = PRUDPV0Transport(self.secure_key, self, client, addr)
            else:
                raise NotImplementedError("Invalid packet / not PRUDP v0!")
            client.transport = transport
            self.connections[addr] = client
        else:
            client = self.connections[addr]
            transport = client.transport

        packet = transport.handle_data(data)

    def sendto(self, data, addr):
        return self.transport.sendto(data, addr)