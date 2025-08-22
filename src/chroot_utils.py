import os
import subprocess


def mount_bind(source, target):
    if not os.path.exists(target):
        os.makedirs(target)
    subprocess.call(["mount", "--bind", source, target])


def mount_specials(ubuntu):
    mount_bind("/dev", "%s/dev" % ubuntu)
    mount_bind("/dev/pts", "%s/dev/pts" % ubuntu)
    mount_bind("/proc", "%s/proc" % ubuntu)
    mount_bind("/sys", "%s/sys" % ubuntu)

    # Ensure networking works inside chroot
    etc_dir = "%s/etc" % ubuntu
    if not os.path.exists(etc_dir):
        os.makedirs(etc_dir)
    subprocess.call(["cp", "/etc/resolv.conf", etc_dir + "/resolv.conf"])

    # Enable access to /etc/enigma2
    if not os.path.exists(etc_dir + "/enigma2"):
        os.makedirs(etc_dir + "/enigma2")
    mount_bind("/etc/enigma2", etc_dir + "/enigma2")


def umount_specials_lazy(ubuntu):
    # Lazy unmount (detaches immediately, cleans up later)
    for path in ["sys", "proc", "dev/pts", "dev", "etc/enigma2"]:
        target = "%s/%s" % (ubuntu, path)
        print("[+] Lazy unmounting %s" % target)
        subprocess.call(["umount", "-l", target])


def start_ubuntu_plugin(ubuntu, plugin):
    try:
        mount_specials(ubuntu)

        # Start the streaming server in a chroot environment
        server_proc = subprocess.Popen([
            "chroot", ubuntu, "/root/venv/bin/python", plugin
        ])
        return server_proc
    except Exception:
        return None


def stop_ubuntu_plugin(ubuntu, server_proc):
    try:
        server_proc.terminate()
        server_proc.wait()
        umount_specials_lazy(ubuntu)
    except Exception:
        pass
