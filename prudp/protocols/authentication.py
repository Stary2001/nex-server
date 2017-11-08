from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify

class AuthenticationProtocol:
	def __init__(self):
		self.methods = {}
		self.methods[1] = self.login
		self.methods[3] = self.request_token

	@incoming('string')
	@outgoing('u32', 'u32', 'u8[*]', 'string', 'list<u8>', 'string', 'string')
	def login(self, device_id):
		print("LOGIN!!!!!", device_id)

		#success = False
		#result = 0x80010005
		success = True
		result = struct.unpack("<I",b'\x01\x00\x01\x00')[0]
		user_id = struct.unpack("<I", b'\x17\xde\x99n')[0]
		secure_station_url = 'prudps:/address=34.211.187.99;port=60181;CID=1;PID=2;sid=1;stream=10;type=2'
		build = 'branch:origin/feature/45925_FixAutoReconnect build:3_10_11_2006_0'
		token = b'\xf4UN{\xb0e\xad\x9b\xd5\x85N\xa7k;oh\xe8ya3\xc7\x7f\xf6\x91jE\x88\x89:\xd9\x8d3hi\xb5\x01\xb2\xd8)\x95\xbc\xba\xcd\x9c\xc9r\x89z\x8bI\x8d\x98\xf7\xa1\x1exbhR\x18\x94-\xa7\n\x0e\x06pJ*\xad\x86R\xae\xd1\x90Lz-\x90\xc0\xcc\x1d\xc7\x8c\x04)\x97o\xc3]\x11\x86D\xcd9#\xa3\n\xc6\xe5\xae\xbb%&4\xe8?\xb3'
		return (success, result, (result, user_id, token, secure_station_url, [], '', build))

	@incoming('u32', 'u32')
	@outgoing('u32', 'u8[*]')
	def request_token(self, user_pid, secure_server_pid):
		print("token req", user_pid, secure_server_pid)

		#success = False
		#result = 0x80010005
		success = True
		result = struct.unpack("<I",b'\x01\x00\x01\x00')[0]
		token = unhexlify('76 9E 82 88 70 93 8E 8C E0 0C 37 6C 11 F4 DD 3C EB 79 61 33 C7 7F F6 91 6A 45 88 89 41 2B 15 D2 22 F2 40 54 F3 D4 55 61 63 E0 5B 4E C9 72 89 7A 59 D3 FD 9C 70 BD A6 EA 17 46 75 9D 58 8A 79 06 75 78 85 90 56 D6 19 F2 AF CB EA 86 37 29 EF 34 B4 B3 E5 21 04 33 D7 8D B1 C5 34 68 E9 C3 17 6F D4 C0 63 E9 9E 46 39 2AB5119FA3'.replace(' ',''))
		return (success, result, (result, token))