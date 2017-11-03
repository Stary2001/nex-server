import asyncio
import struct

from prudp.v0packet import PRUDPV0Packet, PRUDPV0PacketOut
from prudp.protocols import protocol_list
from rc4 import RC4

class PRUDPClient:
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key, upper, client_addr):
        self.rc4_state_encrypt = RC4(rc4_key)
        self.rc4_state_decrypt = RC4(rc4_key)

        self.cur_seq = 0
        self.state = PRUDPClient.STATE_EXPECT_SYN
        self.last_sig = None

        self.upper = upper
        self.client_addr = client_addr

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
                self.send_packet(packet_out)
                return True
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
                self.send_packet(packet_out)
                return True
            else:
                #print("Got a non-CONNECT in EXPECT_CONNECT")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_CONNECTED:
            print("Connected:")
            print(packet)
            if packet.op == PRUDPV0Packet.OP_DATA:
                # Ack it.
                # TODO: Fragment reassembly here, if required.

                packet_out = PRUDPV0PacketOut()
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_DATA
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0
                self.send_packet(packet_out)
                return False # Please handle this further.
        print("Unhandled packet??")
        print(packet)
        return False

    def send_packet(self, packet):
        p = packet.encode(self.rc4_state_encrypt)
        print("Sending ", packet)
        self.upper.sendto(p, self.client_addr)