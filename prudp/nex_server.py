import asyncio
import struct

from prudp.server import PRUDPClient
from prudp.v0packet import PRUDPV0Packet, PRUDPV0PacketOut
from prudp.protocols import protocol_list
from rc4 import RC4

class NEXClient(PRUDPClient):
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key, upper, client_addr):
        super().__init__(rc4_key, upper, client_addr)
        self.last_call_id = 0

    def handle_packet(self, packet):
        if super().handle_packet(packet): # Is this already handled?
            return

        success = True
        result = 0

        if self.state == PRUDPClient.STATE_CONNECTED:
            if packet.op == PRUDPV0Packet.OP_DATA:
                global protocol_list

                response = None
                call_id = None

                data_len = struct.unpack("<I", packet.data[0:4])[0]
                proto_with_flag = packet.data[4]
                proto = protocol_list[proto_with_flag & ~0x80]

                if proto_with_flag & 0x80:
                    # Request.
                    call_id = struct.unpack("<I", packet.data[5:9])[0]
                    method = struct.unpack("<I", packet.data[9:13])[0]
                    arg_data = packet.data[13:data_len+13]
                    
                    print("Call: {:08x}, method: {:08x}".format(call_id, method))
                    if not proto:
                        print("Unknown protocol number {:02x}".format(proto_with_flag))
                        success = False
                        result = 0x80010002 # Core::Unknown
                    elif not method in proto.methods:
                        print("Unknown method {:08x} on protocol {:02x}!")
                        success = False
                        result = 0x80010002 # Core::Unknown
                    else:
                        success, result, response = proto.methods[method](arg_data)

                    if success:
                        repsonse_data_len = len(response) + 10
                    else:
                        repsonse_data_len = 10

                    resp_header = struct.pack("<I", repsonse_data_len)
                    resp_header += struct.pack("B", proto_with_flag & ~0x80)
                    resp_header += struct.pack("B", success)
                    if success:
                        resp_header += struct.pack("<I", call_id)
                        resp_header += struct.pack("<I", method | 0x8000)
                    else:
                        resp_header += struct.pack("<I", result)
                        resp_header += struct.pack("<I", call_id)

                    print("AAAAA responding!!!")
                    # Send a response.
                    packet_out = PRUDPV0PacketOut()
                    packet_out.source = 0xa1
                    packet_out.dest = 0xaf
                    packet_out.op = PRUDPV0Packet.OP_DATA
                    packet_out.flags = PRUDPV0Packet.FLAG_NEEDS_ACK
                    packet_out.session = packet.session
                    packet_out.seq = packet.seq
                    packet_out.fragment = 0
                    packet_out.data_len = repsonse_data_len
                    packet_out.data = resp_header
                    if success:
                        packet_out.data += response
                    self.send_packet(packet_out)

                else:
                    pass
                    # Response?

# TODO: big issue with this is stray UDP packets.
# Time out connections after <some time> of lingering in STATE_EXPECT_SYN.

class NEXProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.connections = {}

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if not addr in self.connections:
            client = NEXClient(b"CD&ML", self, addr)
            self.connections[addr] = client
        else:
            client = self.connections[addr]

        packet = client.handle_data(data)

    def sendto(self, data, addr):
        print(">>>", data)
        return self.transport.sendto(data, addr)