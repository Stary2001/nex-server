import asyncio
from prudp import NEXAuthProtocol, NEXSecureProtocol

loop = asyncio.get_event_loop()
auth_listener = loop.create_datagram_endpoint(NEXAuthProtocol, local_addr=('0.0.0.0', 60900))
secure_listener = loop.create_datagram_endpoint(lambda: NEXSecureProtocol(secure_key=b'\x00' * 16), local_addr=('0.0.0.0', 60901))
asyncio.ensure_future(auth_listener)
asyncio.ensure_future(secure_listener)
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass