import os
import subprocess


def mount_bind(source, target):
    if not os.path.exists(target):
        os.makedirs(target)
    subprocess.call(["mount", "--bind", source, target])


def mount_specials(root):
    mount_bind("/dev", "%s/dev" % root)
    mount_bind("/dev/pts", "%s/dev/pts" % root)
    mount_bind("/proc", "%s/proc" % root)
    mount_bind("/sys", "%s/sys" % root)

    # Ensure networking works inside chroot
    etc_dir = "%s/etc" % root
    if not os.path.exists(etc_dir):
        os.makedirs(etc_dir)
    subprocess.call(["cp", "/etc/resolv.conf", "%s/etc/resolv.conf" % root])


def umount_specials_lazy(root):
    # Lazy unmount (detaches immediately, cleans up later)
    for path in ["sys", "proc", "dev/pts", "dev"]:
        target = "%s/%s" % (root, path)
        print("[+] Lazy unmounting %s" % target)
        subprocess.call(["umount", "-l", target])
