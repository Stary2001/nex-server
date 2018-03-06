from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify
import hmac
import hashlib
from rc4 import RC4

class AuthenticationProtocol:
	def __init__(self):
		self.methods = {}
		self.methods[1] = self.login
		self.methods[3] = self.request_token

	@incoming('string')
	@outgoing('u32', 'u32', 'u8[*]', 'string', 'list<u8>', 'string', 'string')
	def login(self, user_pid):
		print("LOGIN!!!!!", user_pid)

		pid = int(user_pid)
		password = "|+GF-i):/7Z87_:q"
		kerberos_key = password.encode("ascii")
		for i in range(65000 + pid % 1024):
			kerberos_key = hashlib.md5(kerberos_key).digest()

		secure_key = unhexlify('4ff77ecdd82e7d21c7ff4be402bc5e77')
		unk_u32 = unhexlify('01000000')
		ticket_data = unhexlify('10000000dd732c4009de947224a4ae42adf9b1ca2c0000007049bd8fc0ebb192b25d7331a947b9fee49630d7139c6f975db245fb0c60aeabeb287fb5f89a6f51a02dade5')
		full_ticket = secure_key + unk_u32 + struct.pack("I", len(ticket_data)) + ticket_data

		rc = RC4(kerberos_key)
		ticket = rc.crypt(full_ticket)
		ticket_mac = hmac.HMAC(kerberos_key)
		ticket_mac.update(ticket)
		ticket += ticket_mac.digest()

		success = True
		result = struct.unpack("<I",b'\x01\x00\x01\x00')[0]
		user_id = struct.unpack("<I", b'\x17\xde\x99n')[0]
		secure_station_url = 'prudps:/address=62.210.129.229;port=60001;CID=1;PID=2;sid=1;stream=10;type=2'
		build = 'branch:origin/feature/45925_FixAutoReconnect build:3_10_11_2006_0'

		return (success, result, (result, user_id, ticket, secure_station_url, [], '', build))

	@incoming('u32', 'u32')
	@outgoing('u32', 'u8[*]')
	def request_token(self, user_pid, secure_server_pid):
		print("token req", user_pid, secure_server_pid)
		
		success = True
		result = struct.unpack("<I",b'\x01\x00\x01\x00')[0]
		
		return (success, result, (result, token))