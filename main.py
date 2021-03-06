#!/usr/bin/env python3

import asyncio
from prudp import NEXAuthServer, NEXSecureServer
import sys

ip = sys.argv[1]

loop = asyncio.get_event_loop()
friends_auth_listener = loop.create_datagram_endpoint(lambda: NEXAuthServer(access_key=b'ridfebb9', server_ip=ip, secure_port=60901, secure_key_length=16, sig_version=1), local_addr=('0.0.0.0', 60900))
friends_secure_listener = loop.create_datagram_endpoint(lambda: NEXSecureServer(access_key=b'ridfebb9', server_ip=ip, secure_key=b'\x00' * 16, sig_version=1), local_addr=('0.0.0.0', 60901))

mk7_auth_listener = loop.create_datagram_endpoint(lambda: NEXAuthServer(access_key=b'6181dff1', server_ip=ip, secure_port=60801, secure_key_length=32, sig_version=0), local_addr=('0.0.0.0', 60800))
mk7_secure_listener = loop.create_datagram_endpoint(lambda: NEXSecureServer(access_key=b'6181dff1', server_ip=ip, secure_key=b'\x00' * 32, sig_version=0), local_addr=('0.0.0.0', 60801))

servers = {}
servers['friends'] = asyncio.ensure_future(friends_auth_listener)
servers['friends-secure'] = asyncio.ensure_future(friends_secure_listener)
servers['mk7'] = asyncio.ensure_future(mk7_auth_listener)
servers['mk7-secure'] = asyncio.ensure_future(mk7_secure_listener)

for s in servers:
	loop.run_until_complete(servers[s])

really_ctrlc = False
try:
    loop.run_forever()
except KeyboardInterrupt:
    try:
        print("\nGot ctrlc! Quitting.")
        final_tasks = []
        for s in servers:
            transport, server = servers[s].result()
            server.schedule_stop()
            final_tasks.append(server.scheduler.go_task)
        loop.run_until_complete(asyncio.gather(*final_tasks))
    except KeyboardInterrupt:
        #print(loop)
        #print(asyncio.Task.all_tasks())
        print("\nREALLY got ctrlc! Quitting.")