#!/usr/bin/env python3
import os
import sys
import time
import paramiko

HOST = "192.168.1.50"
USER = "joe"
PW = "Aa@2886038"
LOCAL_TAR = r"C:\Users\joela\AppData\Local\Temp\webapp-deploy.tgz"
REMOTE_TAR = "/tmp/webapp-deploy.tgz"


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PW, timeout=30, allow_agent=False, look_for_keys=False)

    def run(cmd, timeout=3600):
        print(f"\n=== {cmd[:160]} ===", flush=True)
        _, stdout, stderr = c.exec_command(cmd, timeout=timeout, get_pty=True)
        # stream output
        while True:
            line = stdout.readline()
            if not line:
                break
            try:
                print(line, end="", flush=True)
            except UnicodeEncodeError:
                print(line.encode("ascii", "replace").decode("ascii"), end="", flush=True)
        err = stderr.read().decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
        if err.strip():
            print(err[:4000], flush=True)
        if code != 0:
            raise SystemExit(f"command failed ({code}): {cmd}")
        return code

    print("Uploading tarball...", flush=True)
    sftp = c.open_sftp()
    sftp.put(LOCAL_TAR, REMOTE_TAR)
    sftp.close()
    print("Upload done.", flush=True)

    run(f"echo {PW} | sudo -S docker stop netbootxyz-webapp netbootxyz 2>/dev/null || true")
    run(f"echo {PW} | sudo -S docker rm netbootxyz-webapp netbootxyz 2>/dev/null || true")

    run("rm -rf /home/joe/webapp.prev; "
        "if [ -d /home/joe/webapp ]; then mv /home/joe/webapp /home/joe/webapp.prev; fi; "
        f"tar -xzf {REMOTE_TAR} -C /home/joe && "
        "ls -la /home/joe/webapp | head")

    # Ensure data dirs exist / owned
    run(f"echo {PW} | sudo -S mkdir -p /home/joe/netbootxyz-data/config /home/joe/netbootxyz-data/assets")
    run(f"echo {PW} | sudo -S chown -R joe:joe /home/joe/webapp /home/joe/netbootxyz-data")

    # Build + up (long)
    run(
        "cd /home/joe/webapp && "
        f"echo {PW} | sudo -S docker compose -f docker-compose.yml -f docker-compose.server.yml build --pull=false",
        timeout=1800,
    )
    run(
        "cd /home/joe/webapp && "
        f"echo {PW} | sudo -S docker compose -f docker-compose.yml -f docker-compose.server.yml up -d --force-recreate",
        timeout=300,
    )

    time.sleep(5)
    run(f"echo {PW} | sudo -S docker ps --filter name=netbootxyz --format 'table {{{{.Names}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}'")
    run("sleep 3; ls -la /home/joe/netbootxyz-data/config/menus/netboot.xyz* 2>/dev/null | head -20")
    run("curl -sI http://127.0.0.1:3000/ | head -5; curl -sI http://127.0.0.1:8080/ | head -8")
    run(
        "python3 - <<'PY'\n"
        "import socket\n"
        "s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(3)\n"
        "req=b'\\x00\\x01'+b'netboot.xyz.efi'+b'\\x00octet\\x00'\n"
        "s.sendto(req,('127.0.0.1',69))\n"
        "try:\n"
        " d,a=s.recvfrom(516); print('TFTP',a,'op',d[1],'len',len(d))\n"
        " if d[1]==5: print(d[4:].split(b'\\x00')[0].decode())\n"
        "except Exception as e:\n"
        " print('TFTP fail',e)\n"
        "PY"
    )
    print("\nDeploy finished.", flush=True)
    c.close()


if __name__ == "__main__":
    main()
