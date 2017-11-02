import asyncio
import struct

from prudp.v0packet import PRUDPV0Packet, PRUDPV0PacketOut
from prudp.protocols import protocol_list
from rc4 import RC4

class PRUDPClient:
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key):
        self.rc4_state_encrypt = RC4(rc4_key)
        self.rc4_state_decrypt = RC4(rc4_key)

        self.cur_seq = 0
        self.state = PRUDPClient.STATE_EXPECT_SYN
        self.last_sig = None
        self.last_call_id = 0

    def decode_packet(self, data):
        return PRUDPV0Packet.decode(data, self.rc4_state_decrypt)

    def handle_data(self, data):
        return self.handle_packet(self.decode_packet(data))

    def handle_packet(self, packet):
        if self.state == PRUDPClient.STATE_EXPECT_SYN:
            if packet.op == PRUDPV0Packet.OP_SYN: # SYN
                print("Got SYN!")
                print(packet)
                self.state = PRUDPClient.STATE_EXPECT_CONNECT

                packet_out = PRUDPV0PacketOut()
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_SYN
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.data_size = 0

                p = packet_out.encode(self.rc4_state_encrypt)
                print("Sending", packet_out)
                return p
            else:
                #print("Got a non-SYN in EXPECT_SYN")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_EXPECT_CONNECT:
            if packet.op == PRUDPV0Packet.OP_CONNECT:
                print("Got CONNECT!")
                print(packet)
                self.state = PRUDPClient.STATE_CONNECTED

                packet_out = PRUDPV0PacketOut()
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_CONNECT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.data_size = 0
                packet_out.sig = packet.conn_sig

                p = packet_out.encode(self.rc4_state_encrypt)
                print("Sending", packet_out)
                return p
            else:
                #print("Got a non-CONNECT in EXPECT_CONNECT")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_CONNECTED:
            print("Connected:")
            print(packet)
            if packet.op == PRUDPV0Packet.OP_DATA:
                global protocol_list

                data_len = struct.unpack("<I", packet.data[0:4])[0]
                proto_with_flag = packet.data[4]
                proto = protocol_list[proto_with_flag & ~0x80]
                if not proto: # TODO disconnect
                    print("Unknown protocol number {:02x}".format(proto_with_flag))
                    return

                if proto_with_flag & 0x80:
                    # Request.
                    call = struct.unpack("<I", packet.data[5:9])[0]
                    method = struct.unpack("<I", packet.data[9:13])[0]
                    args = packet.data[13:data_len+13]
                    if not method in proto.methods:
                        print("Unknown method {:08x} on protocol {:02x}!")
                        return
                    # TODO: unpack args..
                    response = proto.methods[method](args)
                else:
                    # Response.
                    pass
                # Ack it.
                packet_out = PRUDPV0PacketOut()
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_DATA
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0

                p = packet_out.encode(self.rc4_state_encrypt)
                print("Sending", packet_out)
                return p

# TODO: big issue with this is stray UDP packets.
# Time out connections after <some time> of lingering in STATE_EXPECT_SYN.

class PRUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.connections = {}

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        #print(data,addr)
        if not addr in self.connections:
            client = PRUDPClient(b"CD&ML")
            self.connections[addr] = client
        else:
            client = self.connections[addr]

        packet = client.handle_data(data)
        if packet != None:
            print("Sending data", packet)
            self.transport.sendto(packet, addr)