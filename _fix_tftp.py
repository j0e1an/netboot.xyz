#!/usr/bin/env python3
import paramiko
import socket
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.50", username="joe", password="Aa@2886038", timeout=20, allow_agent=False, look_for_keys=False)
pw = "Aa@2886038"


def run(cmd):
    _, o, _ = c.exec_command(cmd, timeout=60, get_pty=True)
    print(o.read().decode("utf-8", "replace")[-2500:])


run(f"echo {pw} | sudo -S chown -R 1000:1000 /home/joe/netbootxyz-data/config/menus /home/joe/netbootxyz-data/assets")
run(f"echo {pw} | sudo -S ufw status || true")
run(f"echo {pw} | sudo -S docker restart netbootxyz")
time.sleep(10)
run(f"echo {pw} | sudo -S docker ps --filter name=netbootxyz --format '{{{{.Status}}}}'")
run(f"echo {pw} | sudo -S docker logs netbootxyz 2>&1 | tail -20")

chan = c.get_transport().open_session()
chan.exec_command(f"echo {pw} | sudo -S timeout 8 tcpdump -ni any udp port 69 -c 12 2>&1")
time.sleep(1.5)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(5)
req = b"\x00\x01" + b"netboot.xyz.efi" + b"\x00octet\x00"
try:
    s.sendto(req, ("192.168.1.50", 69))
    d, a = s.recvfrom(516)
    print("CLIENT ok", a, "op", d[1], "len", len(d))
except Exception as e:
    print("CLIENT", e)
finally:
    s.close()
time.sleep(5)
print("TCPDUMP:\n", chan.recv(65535).decode("utf-8", "replace"))
c.close()
