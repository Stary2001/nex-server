import struct
from rc4 import RC4
import hashlib
import hmac
from .. import Type

class KerberosContainer():
	def __init__(self, user_pid=None, user_password=None, key=None):
		if key:
			self.key = key
		else:
			self.user_pid = user_pid
			self.user_password = user_password

			key = user_password.encode("ascii")
			for i in range(65000 + user_pid % 1024):
				key = hashlib.md5(key).digest()
			self.key = key

	def unpack(self, data):
		ticket = data[:-0x10]
		mac = data[-0x10:]

		ticket_mac = hmac.HMAC(self.key)
		ticket_mac.update(ticket)
		if ticket_mac.digest() != mac:
			raise ValueError("Kerberos MAC is invalid!")

		rc = RC4(self.key)
		dec_ticket = rc.crypt(ticket)
		return dec_ticket, len(data)

	def pack(self, data):
		rc = RC4(key)
		ticket = rc.crypt(full_ticket)
		ticket_mac = hmac.HMAC(key)
		ticket_mac.update(ticket)
		ticket += ticket_mac.digest()

		return ticket

class KerberosTicket:
	def pack():
		unk_u32 = struct.pack("I", step)
		full_ticket = secure_key + unk_u32 + struct.pack("I", len(ticket_data)) + ticket_data
