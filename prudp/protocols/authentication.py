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
		self.methods[2] = self.login_ex
		self.methods[3] = self.request_token

	def build_ticket(self, user_pid=None, user_password=None, ticket_data=None, secure_key=None, step = 1):
		kerberos_key = user_password.encode("ascii")
		for i in range(65000 + user_pid % 1024):
			kerberos_key = hashlib.md5(kerberos_key).digest()

		unk_u32 = struct.pack("I", step)
		full_ticket = secure_key + unk_u32 + struct.pack("I", len(ticket_data)) + ticket_data

		rc = RC4(kerberos_key)
		ticket = rc.crypt(full_ticket)
		ticket_mac = hmac.HMAC(kerberos_key)
		ticket_mac.update(ticket)
		ticket += ticket_mac.digest()

		return ticket

	@incoming('string')
	@outgoing('u32', 'u32', 'u8[*]', 'string', 'list<u8>', 'string', 'string')
	def login(self, user_pid):
		user_pid_int = int(user_pid)
		password = "|+GF-i):/7Z87_:q"

		secure_key = b'\x00' * 32
		ticket_data = unhexlify('10000000dd732c4009de947224a4ae42adf9b1ca2c0000007049bd8fc0ebb192b25d7331a947b9fee49630d7139c6f975db245fb0c60aeabeb287fb5f89a6f51a02dade5')
		ticket = self.build_ticket(user_pid=user_pid_int, user_password=password, ticket_data=ticket_data, secure_key=secure_key)

		success = True
		result = 0x00010001
		secure_station_url = 'prudps:/address=192.168.254.1;port=60901;CID=1;PID=2;sid=1;stream=10;type=2'
		build = 'branch:origin/feature/45925_FixAutoReconnect build:3_10_11_2006_0'

		return (success, result, (result, user_pid_int, ticket, secure_station_url, [], '', build))

	@incoming('string', 'string', 'u32', 'Buffer')
	@outgoing('u32', 'u32', 'u8[*]', 'string', 'list<u8>', 'string', 'string')
	def login_ex(self, user_pid, *a):
		user_pid_int = int(user_pid)
		password = "|+GF-i):/7Z87_:q"

		secure_key = b'\x00' * 32
		ticket_data = unhexlify('06a5b76200e4046d8f1e52429b413ae34f1b0d7ad795b63ce4885f9e68e3b66fdee8d6d31e200b3141a743cf4c0be89b853138f0384e2ec5c56ac9d0')
		ticket = self.build_ticket(user_pid=user_pid_int, user_password=password, ticket_data=ticket_data, secure_key=secure_key)

		success = True
		result = 0x00010001
		secure_station_url = 'prudps:/address=192.168.254.1;port=60801;CID=1;PID=2;sid=1;stream=10;type=2'
		build = 'branch:amk_server_branch build:2_17_11578_0'

		return (success, result, (result, user_pid_int, ticket, secure_station_url, [], '', build))

	@incoming('u32', 'u32')
	@outgoing('u32', 'u8[*]')
	def request_token(self, user_pid, secure_server_pid):
		print("token req", user_pid, secure_server_pid)
		success = True
		result = 0x00010001
		
		password = "|+GF-i):/7Z87_:q"

		secure_key = b'\x00' * 32
		ticket_data = unhexlify('10000000c51dcdb821c418742e6200bc4bf638c02c0000009d3b93e2a51c978da884e1ae92c7ddae9ec2f148bb9d722d732c9ac3bef063ed3e0fe30d1f0f0792c9cc4410')
		ticket = self.build_ticket(user_pid=user_pid, user_password=password, ticket_data=ticket_data, secure_key=secure_key, step=2)

		return (success, result, (result, ticket))