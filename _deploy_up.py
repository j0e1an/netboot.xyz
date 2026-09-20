#!/usr/bin/env python3
import time
import paramiko

HOST = "192.168.1.50"
USER = "joe"
PW = "Aa@2886038"


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PW, timeout=30, allow_agent=False, look_for_keys=False)

    def run(cmd, timeout=600):
        print(f"\n=== {cmd[:160]} ===", flush=True)
        _, stdout, stderr = c.exec_command(cmd, timeout=timeout, get_pty=True)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
        print(out.encode("ascii", "replace").decode("ascii")[:8000], flush=True)
        if err.strip():
            print(err.encode("ascii", "replace").decode("ascii")[:2000], flush=True)
        if code != 0:
            raise SystemExit(f"failed ({code}): {cmd}")
        return out

    # Re-extract latest tar if present; otherwise just compose up
    run(
        "cd /home/joe/webapp && "
        f"echo {PW} | sudo -S docker compose -f docker-compose.server.yml up -d --force-recreate",
        timeout=300,
    )
    time.sleep(8)
    run(f"echo {PW} | sudo -S docker ps -a --filter name=netbootxyz --format 'table {{{{.Names}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}'")
    run(f"echo {PW} | sudo -S docker logs netbootxyz 2>&1 | tail -80")
    run("ls -la /home/joe/netbootxyz-data/config/menus/netboot.xyz* 2>/dev/null | head -30")
    run("grep -n 'boot_domain' /home/joe/netbootxyz-data/config/menus/boot.cfg | head -3")
    run("curl -sI http://127.0.0.1:3000/ | head -5; echo ---; curl -sI http://127.0.0.1:8080/ | head -8; echo ---; curl -sI http://127.0.0.1:8080/ipxe/windows/menu.ipxe | head -8")
    run(
        "python3 - <<'PY'\n"
        "import socket\n"
        "for host in ['127.0.0.1','192.168.1.50']:\n"
        " s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(3)\n"
        " req=b'\\x00\\x01'+b'netboot.xyz.efi'+b'\\x00octet\\x00'\n"
        " try:\n"
        "  s.sendto(req,(host,69)); d,a=s.recvfrom(516); print(host,'TFTP op',d[1],'from',a,'len',len(d))\n"
        "  if d[1]==5: print(' ',d[4:].split(b'\\x00')[0].decode())\n"
        " except Exception as e:\n"
        "  print(host,'TFTP fail',e)\n"
        " finally:\n"
        "  s.close()\n"
        "PY"
    )
    print("\nUP done", flush=True)
    c.close()


if __name__ == "__main__":
    main()
