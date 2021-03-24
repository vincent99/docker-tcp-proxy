#!/usr/bin/env python3

import logging
import os
import random
import sys
import subprocess, threading, signal

from dns.resolver import Resolver

logging.root.setLevel(logging.INFO)

LISTENS = os.environ.get("LISTEN", ":100").split()
NAMESERVERS = os.environ.get("NAMESERVERS", "208.67.222.222 8.8.8.8 208.67.220.220 8.8.4.4").split()
resolver = Resolver()
resolver.nameservers = NAMESERVERS
TALKS = os.environ.get("TALK", "talk:100").split()
TEMPLATE = """
backend talk_{index}
    server stupid_{index} {talk}

frontend listen_{index}
    bind {listen}
    default_backend talk_{index}
"""
config = """
global
    log stdout format raw daemon

defaults
    log global
    mode tcp
    balance leastconn
    timeout client "$TIMEOUT_CLIENT"
    timeout client-fin "$TIMEOUT_CLIENT_FIN"
    timeout connect "$TIMEOUT_CONNECT"
    timeout server "$TIMEOUT_SERVER"
    timeout server-fin "$TIMEOUT_SERVER_FIN"
    timeout tunnel "$TIMEOUT_TUNNEL"
"""

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen(self.cmd, shell=True, preexec_fn=os.setsid)
            self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            os.killpg(self.process.pid, signal.SIGTERM)
            thread.join()

if len(LISTENS) != len(TALKS):
    sys.exit("Set the same amount of servers in $LISTEN and $TALK")

if os.environ.get("PRE_RESOLVE", "0") in {"0", "1"}:
    PRE_RESOLVES = [os.environ.get("PRE_RESOLVE", "0")] * len(LISTENS)
else:
    PRE_RESOLVES = os.environ.get("PRE_RESOLVE", "0").split()

if len(LISTENS) != len(PRE_RESOLVES):
    sys.exit("Set the same amount of bools $PRE_RESOLVE as servers in "
             "$LISTEN and $TALK, or use just one to set it globally")

for index, (listen, talk, pre_resolve) in enumerate(zip(LISTENS, TALKS,
                                                        PRE_RESOLVES)):
    server, port = talk.split(":")
    ip = server

    # Resolve target if required
    if pre_resolve == "1":
        ip = random.choice([answer.address
                            for answer in resolver.query(server)])
        logging.info("Resolved %s to %s", server, ip)

    # Render template
    config += TEMPLATE.format(
        index=index,
        listen=listen,
        talk=f"{ip}:{port}",
    )

# Write template to haproxy's cfg file
with open("/usr/local/etc/haproxy/haproxy.cfg", "w") as cfg:
    cfg.write(config)

logging.info("Magic ready, executing now: %s", " ".join(sys.argv[1:]))
Command(' '.join(sys.argv[1:])).run(timeout=int(os.environ.get('PROXY_TIMEOUT', '28800')))

