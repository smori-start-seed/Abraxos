# Bootsatz.py – Das bootfahige Medium (Abraxos, Stufe 2)
# Ein Kernel, eine initramfs-Wurzel, kein Login, keine Shell:
# das Colorverse atmet als PID 1 - die Farbsprache ist die erste Sprache.
# Der erste Boden ist der USB-Stick: das Medium lebt daneben, bestaehige
# OS auf der Festplatte werden nie angeruehrt; Anpflanzen (Stufe 3,
# Boden.py) bleibt freiwillig. Die Farbsprache borgt es vom Colorverse-
# Nachbar-Klon; die Systemwerkzeuge vom Host (Kernel, cpio, gzip,
# grub-mkrescue).
import os
import glob
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from config import *

PYTHON_TAR = "cpython_install_only.tar.gz"


# ============================================================
#  KLEINE WERKZEUGE
# ============================================================

def _grund(pfad):
    gesamt = 0
    for wurzel, _, dateien in os.walk(pfad):
        for name in dateien:
            gesamt += os.path.getsize(os.path.join(wurzel, name))
    return gesamt


def _mb(zahl):
    return f"{zahl / 1048576:.1f} MB"


def _lauf(befehl, cwd=None):
    ergebnis = subprocess.run(befehl, cwd=cwd, capture_output=True, text=True)
    if ergebnis.returncode != 0:
        raise RuntimeError(f"{befehl[0]} fiel aus: {ergebnis.stderr.strip()[:400]}")
    return ergebnis.stdout


def _brauche(werkzeug, hinweis):
    if shutil.which(werkzeug) is None:
        raise RuntimeError(f"{werkzeug} fehlt - {hinweis}")


def kerne():
    gefundene = []
    for muster in ("/boot/vmlinuz-*", "/lib/modules/*/vmlinuz*"):
        gefundene = gefundene + [p for p in glob.glob(muster) if os.access(p, os.R_OK)]
    return sorted(gefundene, reverse=True)


def _module_saehen(wurzel, kernel):
    kver = os.path.basename(kernel)
    if not kver.startswith("vmlinuz-"):
        return 0
    kver = kver[len("vmlinuz-"):]
    quelle_basis = os.path.join("/lib/modules", kver)
    if not os.path.isdir(quelle_basis):
        return 0
    ziel_basis = os.path.join(wurzel, "lib", "modules", kver)
    kopie = 0
    for name in ("ext4", "jbd2", "crc32c_generic", "usb_storage", "uas",
                 "sd_mod", "scsi_mod", "virtio", "virtio_pci", "virtio_blk"):
        gefunden = glob.glob(os.path.join(quelle_basis, "kernel", "**", name + ".ko*"), recursive=True)
        if gefunden:
            ziel = os.path.join(ziel_basis, os.path.relpath(gefunden[0], quelle_basis))
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            shutil.copy2(gefunden[0], ziel)
            kopie += 1
    for treffen in ("modules.builtin", "modules.order", "modules.builtin.modinfo"):
        quelle = os.path.join(quelle_basis, treffen)
        if os.path.exists(quelle):
            shutil.copy2(quelle, os.path.join(ziel_basis, treffen))
    if kopie and shutil.which("depmod"):
        try:
            _lauf(["depmod", "-b", wurzel, kver])
        except RuntimeError:
            pass
    return kopie


def _python_saehen(wurzel):
    ort = os.path.join(wurzel, "farb-os", "python")
    if os.path.exists(os.path.join(ort, "bin", "python3")):
        return ort
    tar_pfad = os.path.join(BOOT_ORDNER, PYTHON_TAR)
    if not os.path.exists(tar_pfad):
        os.makedirs(BOOT_ORDNER, exist_ok=True)
        print(f"[BOOTSATZ] hole Python von {BODEN_PYTHON_URL}")
        urllib.request.urlretrieve(BODEN_PYTHON_URL, tar_pfad)
    with tarfile.open(tar_pfad) as tar:
        try:
            tar.extractall(wurzel, filter="data")
        except TypeError:
            tar.extractall(wurzel)
    shutil.move(os.path.join(wurzel, "python"), ort)
    return ort


INIT_SKRIPT = """#!/bin/sh
mount -t proc none /proc 2>/dev/null
mount -t sysfs none /sys 2>/dev/null
mount -t devtmpfs none /dev 2>/dev/null
mkdir -p /run /farb-os/home
mount -t tmpfs none /run 2>/dev/null
[ -d /lib/modules ] && for m in ext4 usb_storage uas virtio_pci virtio_blk; do modprobe $m 2>/dev/null; done
BODEN=$(cat /proc/cmdline | tr ' ' '\\n' | grep '^boden=PARTUUID=' | cut -d= -f3)
if [ -n "$BODEN" ]; then
  sleep 3
  mount -t auto /dev/disk/by-partuuid/$BODEN /farb-os/home 2>/dev/null
  grep -q ' /farb-os/home ' /proc/mounts || for geraet in /dev/vda1 /dev/sda1 /dev/vdb1 /dev/sdb1 /dev/vda /dev/sda; do
    [ -b "$geraet" ] && mount -t auto "$geraet" /farb-os/home 2>/dev/null && break
  done
fi
grep -q ' /farb-os/home ' /proc/mounts || mount -t tmpfs none /farb-os/home 2>/dev/null
echo "[INIT] BODEN: $(grep -m1 ' /farb-os/home ' /proc/mounts | cut -d' ' -f1)${BODEN:+ (Wunsch: $BODEN)}"
[ -e /farb-os/python/bin/python3 ] && echo [INIT] BIN_OK || echo [INIT] BIN_FEHLT
[ -e /lib64/ld-linux-x86-64.so.2 ] && echo [INIT] LDR_OK || echo [INIT] LDR_FEHLT
[ -e /farb-os/os/farb_os.py ] && echo [INIT] WELT_OK || echo [INIT] WELT_FEHLT
cd /farb-os/home
/farb-os/python/bin/python3 -u /farb-os/os/farb_os.py
echo "[INIT] Die Welt hat geatmet - Framework geht behutsam"
sync
poweroff -f
"""


GRUB_CFG = """set timeout={timeout}
serial --unit=0 --speed=115200
terminal_input serial console
terminal_output serial console
menuentry "FARB-OS" {{
    linux /boot/vmlinuz console=tty0 console=ttyS0,115200{boden}
    initrd /boot/initramfs.img
}}
"""


def grub_boden():
    if not BODEN_PARTUUID:
        return ""
    return " boden=PARTUUID=" + str(BODEN_PARTUUID)


# ============================================================
#  GLIBC-KRAM - Python braucht seinen Unterbau
# ============================================================

def _kram_kopieren(wurzel, programm):
    bericht = _lauf(["ldd", programm])
    zu_kopieren = []
    for loader in ("/lib64/ld-linux-x86-64.so.2", "/lib/ld-linux-x86-64.so.2"):
        if os.path.exists(loader):
            zu_kopieren.append(loader)
    for zeile in bericht.splitlines():
        teile = zeile.strip().split()
        if "=>" in teile and os.path.exists(teile[2]):
            zu_kopieren.append(teile[2])
        elif zeile.strip().startswith("/") and os.path.exists(zeile.strip().split()[0]):
            zu_kopieren.append(zeile.strip().split()[0])
    for quelle in set(zu_kopieren):
        ziel = os.path.join(wurzel, quelle.lstrip("/"))
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy2(quelle, ziel)
        os.chmod(ziel, 0o755)
    return len(set(zu_kopieren))


# ============================================================
#  INITRAMFS MIT DER WELT IM BAUCH
# ============================================================

def _welt_ort():
    """Die Welt wird geborgt - vom Nachbar-Klon (Colorverse) oder vom eigenen Lager."""
    orte = [os.path.abspath(p) for p in WELT_PFAD] + [os.path.dirname(os.path.abspath(__file__))]
    for ort in orte:
        if os.path.exists(os.path.join(ort, "farb_os.py")):
            return ort
    raise RuntimeError("die Farbsprache fehlt - Colorverse neben den Boden legen (WELT_PFAD in config.py)")


def baue_initramfs(ordner=BOOT_ORDNER):
    _brauche("cpio", "auf Debian/Ubuntu: sudo apt install cpio")
    _brauche("gzip", "grundlegend - sollte nie fehlen")
    kernel = kerne()
    if not kernel:
        raise RuntimeError("kein lesbarer Kernel in /boot - der Keim borgt ihn vom Host")
    kernel = kernel[0]

    wurzel = os.path.join(ordner, BODEN_INITRAMFS_ORDNER)
    if os.path.exists(wurzel):
        shutil.rmtree(wurzel)
    for pfad in ("bin", "dev", "proc", "sys", "run", "farb-os/home", "farb-os/os"):
        os.makedirs(os.path.join(wurzel, pfad), exist_ok=True)

    _brauche("busybox", "auf Debian/Ubuntu: sudo apt install busybox-static")
    busybox = shutil.which("busybox") or shutil.which("busybox.static")
    shutil.copy(busybox, os.path.join(wurzel, "bin", "busybox"))
    os.chmod(os.path.join(wurzel, "bin", "busybox"), 0o755)
    for werkzeug in ("sh", "mount", "mkdir", "cat", "sleep", "sync", "tr", "grep", "cut", "modprobe"):
        os.symlink("busybox", os.path.join(wurzel, "bin", werkzeug))

    module = _module_saehen(wurzel, kernel)
    print(f"[BOOTSATZ] Module gesaet: {module}")

    python_bin = _python_saehen(wurzel)
    kram = _kram_kopieren(wurzel, python_bin + "/bin/python3")
    print(f"[BOOTSATZ] Python gesaet: {python_bin} | Bibliotheken: {kram}")

    probe = subprocess.run([python_bin + "/bin/python3", "--version"], capture_output=True, text=True)
    if probe.returncode != 0:
        raise RuntimeError(f"das gesaete Python spricht nicht: {probe.stderr.strip()[:200]}")
    print("[BOOTSATZ] Probe:", probe.stdout.strip() or probe.stderr.strip())

    welt = _welt_ort()
    print(f"[BOOTSATZ] Welt aus {welt}")
    for datei in os.listdir(welt):
        if datei.endswith(".py"):
            shutil.copy(os.path.join(welt, datei), os.path.join(wurzel, "farb-os", "os", datei))

    eigenes = os.path.dirname(os.path.abspath(__file__))
    for werkzeug in ("Keim.py", "Boden.py", "Bootsatz.py"):
        if os.path.exists(os.path.join(eigenes, werkzeug)):
            shutil.copy(os.path.join(eigenes, werkzeug), os.path.join(wurzel, "farb-os", "os", werkzeug))
    boden_config = os.path.join(eigenes, "config.py")
    if os.path.exists(boden_config):
        mit_welt = os.path.join(wurzel, "farb-os", "os", "config.py")
        with open(mit_welt, "a") as f:
            f.write("\n\n# ---- Bodenschicht (Abraxos) ----\n")
            with open(boden_config) as quelle:
                f.write(quelle.read())

    with open(os.path.join(wurzel, "init"), "w") as f:
        f.write(INIT_SKRIPT)
    os.chmod(os.path.join(wurzel, "init"), 0o755)

    cpio_pfad = os.path.join(ordner, "initramfs.img")
    kernel_kopie = os.path.join(ordner, "vmlinuz")
    shutil.copy(kernel, kernel_kopie)
    os.chmod(kernel_kopie, 0o644)
    listing = _lauf(["find", "."], cwd=wurzel)
    with open(cpio_pfad, "wb") as aus:
        hinaus = subprocess.run(["cpio", "-o", "-H", "newc"], cwd=wurzel,
                                input=listing.encode(), stdout=aus)
        if hinaus.returncode != 0:
            raise RuntimeError("cpio fiel aus")
    _lauf(["gzip", "-f", cpio_pfad])
    print(f"[BOOTSATZ] Kernel: {_mb(os.path.getsize(kernel_kopie))} | initramfs: {_mb(os.path.getsize(cpio_pfad + '.gz'))} | Wurzel gesamt: {_mb(_grund(wurzel))}")

    for pfad in ("./farb-os/python/bin/python3", "./lib64/ld-linux-x86-64.so.2", "./init", "./bin/busybox", "./farb-os/os/farb_os.py"):
        if not os.path.exists(os.path.join(wurzel, pfad)):
            raise RuntimeError(f"{pfad} fehlt in der initramfs-Wurzel")

    return kernel, cpio_pfad + ".gz"


# ============================================================
#  ISO - das Medium, das man vor Staub ansteckt
# ============================================================

def baue_iso(ordner=BOOT_ORDNER):
    _brauche("grub-mkrescue", "auf Debian/Ubuntu: sudo apt install xorriso grub-pc-bin")
    kernel, initramfs = baue_initramfs(ordner)

    iso_wurzel = os.path.join(ordner, "iso_wurzel")
    if os.path.exists(iso_wurzel):
        shutil.rmtree(iso_wurzel)
    os.makedirs(os.path.join(iso_wurzel, "boot", "grub"), exist_ok=True)
    shutil.copy(kernel, os.path.join(iso_wurzel, "boot", "vmlinuz"))
    shutil.copy(initramfs, os.path.join(iso_wurzel, "boot", "initramfs.img"))
    with open(os.path.join(iso_wurzel, "boot", "grub", "grub.cfg"), "w") as f:
        f.write(GRUB_CFG.format(timeout=BOOT_TIMEOUT, boden=grub_boden()))

    iso_pfad = os.path.join(ordner, "bootsatz.iso")
    _lauf(["grub-mkrescue", "-o", iso_pfad, iso_wurzel])
    print(f"[BOOTSATZ] Medium fertig: {iso_pfad} - {_mb(os.path.getsize(iso_pfad))}")
    return iso_pfad


if __name__ == "__main__":
    try:
        if "--iso" in sys.argv or "--usb" in sys.argv:
            iso = baue_iso()
            if "--usb" in sys.argv:
                print("[BOOTSATZ] Der Stick atmet mit diesem Befehl (Geraet pruefen, kein automatisches Schreiben):")
                print(f"  sudo dd if={iso} of=/dev/sdX bs=4M oflag=direct,sync status=progress && sync")
                print("[BOOTSATZ] Der Stick lebt daneben - Festplatten werden nie angeruehrt.")
                print("[BOOTSATZ] Bestaendigkeit (optional): BODEN_PARTUUID in config.py setzen.")
        else:
            kernel, initramfs = baue_initramfs()
            print(f"[BOOTSATZ] Kernel: {kernel}")
            print(f"[BOOTSATZ] Initramfs: {initramfs}")
    except RuntimeError as weh:
        print(f"[BOOTSATZ] Verweigert: {weh}")
        sys.exit(1)
