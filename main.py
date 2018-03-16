import asyncio
from prudp import NEXAuthProtocol, NEXSecureProtocol

loop = asyncio.get_event_loop()
friends_auth_listener = loop.create_datagram_endpoint(lambda: NEXAuthProtocol(access_key=b'ridfebb9', secure_port=60901), local_addr=('0.0.0.0', 60900))
friends_secure_listener = loop.create_datagram_endpoint(lambda: NEXSecureProtocol(access_key=b'ridfebb9', secure_key=b'\x00' * 16), local_addr=('0.0.0.0', 60901))

mk7_auth_listener = loop.create_datagram_endpoint(lambda: NEXAuthProtocol(access_key=b'6181dff1', secure_port=60801), local_addr=('0.0.0.0', 60800))
mk7_secure_listener = loop.create_datagram_endpoint(lambda: NEXSecureProtocol(access_key=b'6181dff1', secure_key=b'\x00' * 32), local_addr=('0.0.0.0', 60801))

asyncio.ensure_future(friends_auth_listener)
asyncio.ensure_future(friends_secure_listener)
asyncio.ensure_future(mk7_auth_listener)
asyncio.ensure_future(mk7_secure_listener)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass