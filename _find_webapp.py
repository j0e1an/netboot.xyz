#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.50", username="joe", password="Aa@2886038", timeout=20, allow_agent=False, look_for_keys=False)


def run(cmd):
    _, o, _ = c.exec_command(cmd, timeout=60)
    print(o.read().decode("utf-8", "replace")[:8000])


run(
    "find /home/joe /opt /var/tmp /tmp -maxdepth 5 \\( -name 'windows-catalog*' -o -name '*webapp*' -o -iname 'Dockerfile' \\) 2>/dev/null | head -80"
)
run(
    "docker history netbootxyz-webapp:local --format '{{.CreatedBy}}' | head -30"
)
run(
    "find /var/lib/docker -name '*windows*' 2>/dev/null | head -20; ls /home/joe/.cursor 2>/dev/null; ls /home/joe/src 2>/dev/null; ls /home/joe/git 2>/dev/null"
)
