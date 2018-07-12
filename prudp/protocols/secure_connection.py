from prudp.protocols import incoming,outgoing
from nintendo.nex.streams import StreamIn
import struct
from binascii import unhexlify
import persistence
import base64

def nintendo_base64_encode(data):
	return base64.b64encode(data).decode('ascii').replace('+', '.').replace('/', '-').replace('=', '*')

def nintendo_base64_decode(s):
	return base64.b64decode(s.replace('.', '+').replace('-', '/').replace('*', '='))

class SecureConnectionProtocol:
	def __init__(self, client):
		self.client = client
		self.server = client.server

		self.methods = {}
		self.methods[0x01] = self.register
		self.methods[0x04] = self.register_ex

	@incoming("list<string>")
	@outgoing("u32", "u32", "string")
	def register(self, client_urls):
		success = True
		result = 0x00010001
		pid_conn_id = 0
		print(client_urls)
		url = ""
		return (success, result, (result, pid_conn_id, url))

	# TODO: pretty sure this isn't how you are supposed to handle a Data<>!
	@incoming("list<string>", "string", "u32", "Buffer")
	@outgoing("u32", "u32", "string")
	def register_ex(self, client_urls, dataholder_name, d_len, buff):
		success = True
		result = 0x00010001
		pid_conn_id = 0
		print(client_urls)
		print(dataholder_name)
		print(d_len)
		s = StreamIn(buff)
		s.u32()
		s.u32()
		s.u32()
		token = s.string()
		token = nintendo_base64_decode(token)
		token_stream = StreamIn(token)
		pid = int(token_stream.string())
		print(pid)
		self.client.user = persistence.User.get(pid)
		url = ""
		return (success, result, (result, pid_conn_id, url))