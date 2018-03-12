from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify

class SecureConnectionProtocol:
	def __init__(self):
		self.methods = {}
		self.methods[0x01] = self.register


	@incoming("list<string>")
	@outgoing("u32", "u32", "string")
	def register(self, client_urls):
		success = True
		result = 0x00010001
		pid_conn_id = 0
		print(client_urls)
		url = ""
		return (success, result, (result, pid_conn_id, url))