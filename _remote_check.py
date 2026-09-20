#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.1.50", username="joe", password="Aa@2886038", timeout=20, allow_agent=False, look_for_keys=False)


def run(cmd, t=90):
    _, o, e = c.exec_command(cmd, timeout=t, get_pty=True)
    out = o.read().decode("utf-8", "replace")
    print(f"=== {cmd[:160]} ===")
    print(out[:10000])
    return out


run("ls -la /home/joe/netboot.xyz | head -50")
run("cat /home/joe/netboot.xyz/docker-compose.yml")
run("find /home/joe/netbootxyz-data -iname '*.efi' -o -iname '*.kpxe' -o -iname '*.ipxe' 2>/dev/null | head -100")
run("ls -laR /home/joe/netbootxyz-data/config/menus 2>/dev/null | head -150")
run("ls -la /home/joe/netbootxyz-data/config/; ls -la /home/joe/netbootxyz-data/assets | head -40")
run("docker inspect netbootxyz-webapp --format 'Image={{.Config.Image}} NetworkMode={{.HostConfig.NetworkMode}} Binds={{json .HostConfig.Binds}}'")
run("docker images | grep -i netboot; echo ---; ls /home/joe/netbootxyz-data/config/menus/remote 2>/dev/null; find /home/joe/netbootxyz-data/config/menus/remote -maxdepth 2 2>/dev/null | head -40")
run("head -80 /home/joe/netbootxyz-data/config/menus/boot.cfg; echo ---; cat /home/joe/netbootxyz-data/config/menus/windows.ipxe")
