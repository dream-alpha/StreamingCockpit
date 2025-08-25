# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


import os
import subprocess
import sys


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


def get_mounts():
    """Return a dict {mountpoint: source} from /proc/mounts"""
    mounts = {}
    with open("/proc/mounts") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                src, tgt = parts[0], parts[1]
                mounts[tgt] = src
    return mounts


def bind_media_to_chroot(chroot_path):
    host_media = "/media"
    chroot_media = os.path.join(chroot_path, "media")

    if not os.path.exists(chroot_media):
        os.makedirs(chroot_media)

    mounts = get_mounts()

    for entry in os.listdir(host_media):
        entry_path = os.path.join(host_media, entry)
        if os.path.isdir(entry_path):
            target = os.path.join(chroot_media, entry)

            if not os.path.exists(target):
                os.makedirs(target)

            if target in mounts:
                print("Skipping %s (already mounted)" % target)
                continue

            try:
                subprocess.check_call(["mount", "--bind", entry_path, target])
                print("Bind mounted %s -> %s" % (entry_path, target))
            except subprocess.CalledProcessError as e:
                print("Failed to bind mount %s: %s" % (entry_path, e))


def unbind_media_from_chroot(chroot_path):
    chroot_media = os.path.join(chroot_path, "media")
    mounts = get_mounts()

    # Only unmount entries inside chroot/media
    for target in sorted(mounts.keys(), reverse=True):
        if target.startswith(chroot_media + "/"):
            try:
                subprocess.check_call(["umount", target])
                print("Unmounted %s" % target)
            except subprocess.CalledProcessError:
                print("Normal unmount failed, trying lazy unmount: %s" % target)
                try:
                    subprocess.check_call(["umount", "-l", target])
                    print("Lazy unmounted %s" % target)
                except subprocess.CalledProcessError as e:
                    print("Failed to lazy unmount %s: %s" % (target, e))
