import asyncio
import struct

from prudp.v0packet import PRUDPV0Packet, PRUDPV0PacketOut
from prudp.protocols import protocol_list
from rc4 import RC4
from binascii  import hexlify
from prudp.protocols import incoming
from prudp.protocols.types import Type
from prudp.protocols.types.kerberos import KerberosContainer

class PRUDPClient:
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key, server, client_addr):
        self.key = rc4_key
        self.rc4_state_encrypt = RC4(rc4_key, reset=False)
        self.rc4_state_decrypt = RC4(rc4_key, reset=False)

        self.cur_seq = 0
        self.state = PRUDPClient.STATE_EXPECT_SYN
        self.last_sig = None

        self.server = server
        self.client_addr = client_addr

        self.client_signature = None
        self.server_signature = b'\xaa\xbb\xcc\xdd'

    def decode_packet(self, data):
        return PRUDPV0Packet.decode(data, self.rc4_state_decrypt)

    def handle_data(self, data):
        return self.handle_packet(self.decode_packet(data))

    def handle_packet(self, packet):
        if self.state == PRUDPClient.STATE_EXPECT_SYN:
            if packet.op == PRUDPV0Packet.OP_SYN: # SYN
                self.state = PRUDPClient.STATE_EXPECT_CONNECT

                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_SYN
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.data_size = 0
                p = packet_out.encode(self.rc4_state_encrypt)
                self.send_packet(packet_out)
                return True
            else:
                #print("Got a non-SYN in EXPECT_SYN")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_EXPECT_CONNECT:
            if packet.op == PRUDPV0Packet.OP_CONNECT:
                self.client_signature = packet.conn_sig
                self.state = PRUDPClient.STATE_CONNECTED

                check = 0
                # TODO: eww, hack
                if packet.data != b'':
                    @incoming('u8[*]', 'u8[*]')
                    def parse_connect(fself, a, b):
                        nonlocal check
                        k2, k2_len = KerberosContainer(key=self.key).unpack(b)

                        pid = k2[0:4]
                        cid = k2[4:8]
                        check = struct.unpack("<I", k2[8:12])[0]

                    parse_connect(None, packet.data)

                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_CONNECT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                if packet.data != b'':
                    check_buffer = Type.get_type('u8[*]').pack(struct.pack("<I", check + 1))
                    packet_out.data = check_buffer
                    packet_out.data_size = len(check_buffer)
                else:
                    packet_out.data_size = 0
                packet_out.sig = packet.conn_sig
                packet_out.conn_sig = self.server_signature

                self.send_packet(packet_out)
                return True
            else:
                #print("Got a non-CONNECT in EXPECT_CONNECT")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_CONNECTED:
            if packet.op == PRUDPV0Packet.OP_DATA and packet.flags & PRUDPV0Packet.FLAG_ACK == 0:
                # Ack it.
                # TODO: Fragment reassembly here, if required.

                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_DATA
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0
                packet_out.data_size = 0

                self.send_packet(packet_out)
                return False # Please handle this further.
            elif packet.op == PRUDPV0Packet.OP_HEARTBEAT:
                # Ack it.
                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_HEARTBEAT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0
                packet_out.data_size = 0
                self.send_packet(packet_out)
                return True
            elif packet.op == PRUDPV0Packet.OP_DISCONNECT:
                del self.server.connections[self.client_addr]

                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_DISCONNECT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0
                packet_out.data_size = 0

                self.send_packet(packet_out)
                return True
            elif packet.flags & PRUDPV0Packet.FLAG_ACK != 0:
                # idk it's an ack
                return True

        print("Unhandled packet??")
        print(packet)
        return False

    def send_packet(self, packet):
        p = packet.encode(self.rc4_state_encrypt)
        #print("Sending ", packet)
        self.server.sendto(p, self.client_addr)