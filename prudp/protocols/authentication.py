from prudp.protocols import incoming,outgoing
import struct

class AuthenticationProtocol:
	def __init__(self):
		self.methods = {}
		self.methods[1] = self.login
		self.methods[3] = self.request_token

	@incoming('string')
	@outgoing('u32', 'u32', 'u8[*]', 'string', 'u8[]', 'string')
	def login(self, device_id):
		print("LOGIN!!!!!", device_id)

		#success = False
		#result = 0x80010005
		success = True
		result = struct.unpack("<I",b'\x01\x00\x01\x00')[0]
		user_id = struct.unpack("<I", b'\x17\xde\x99n')[0]
		conn_string = 'prudps:/address=34.211.187.99;port=60181;CID=1;PID=2;sid=1;stream=10;type=2'
		build = 'branch:origin/feature/45925_FixAutoReconnect build:3_10_11_2006_0'
		token = b'\xf4UN{\xb0e\xad\x9b\xd5\x85N\xa7k;oh\xe8ya3\xc7\x7f\xf6\x91jE\x88\x89:\xd9\x8d3hi\xb5\x01\xb2\xd8)\x95\xbc\xba\xcd\x9c\xc9r\x89z\x8bI\x8d\x98\xf7\xa1\x1exbhR\x18\x94-\xa7\n\x0e\x06pJ*\xad\x86R\xae\xd1\x90Lz-\x90\xc0\xcc\x1d\xc7\x8c\x04)\x97o\xc3]\x11\x86D\xcd9#\xa3\n\xc6\xe5\xae\xbb%&4\xe8?\xb3'
		return (success, result, (result, user_id, token, conn_string, b'\x00\x00\x00\x00\x01\x00\x00', build))

	@incoming('u32', 'u32')
	@outgoing('u32', 'u8[*]')
	def request_token(self, user_pid, secure_server_pid):
		print("token req", user_pid, secure_server_pid)

		#success = False
		#result = 0x80010005
		success = True
		result = struct.unpack("<I",b'\x01\x00\x01\x00')[0]
		token = b'\xf4UN{\xb0e\xad\x9b\xd5\x85N\xa7k;oh\xe8ya3\xc7\x7f\xf6\x91jE\x88\x89:\xd9\x8d3hi\xb5\x01\xb2\xd8)\x95\xbc\xba\xcd\x9c\xc9r\x89z\x8bI\x8d\x98\xf7\xa1\x1exbhR\x18\x94-\xa7\n\x0e\x06pJ*\xad\x86R\xae\xd1\x90Lz-\x90\xc0\xcc\x1d\xc7\x8c\x04)\x97o\xc3]\x11\x86D\xcd9#\xa3\n\xc6\xe5\xae\xbb%&4\xe8?\xb3'
		return (success, result, (result, token))