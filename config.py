# ============================================================
#  CONFIG.PY – Konfiguration des Bodens (Abraxos)
#  Der Boden traegt die Welt; die Welt lebt im Colorverse.
#  Die Welt-Einstellungen (WORLD_SIZE, ZUSTIMMUNG_DAUER, ...)
#  kommen mit dem Welt-Samen in das initramfs - sie bleiben
#  im config.py des Colorverse zu Hause.
# ============================================================


# ------------------------------------------------------------
#  BOOT - vom Keim zum Boden (Bootstrap-Stufen)
# ------------------------------------------------------------

BOOT_ORDNER = "bootsatz"                    # hier baut der Bootsatz: kernel, initramfs, iso
BOOT_TIMEOUT = 5                            # Sekunden im GRUB-Bildschirm
BODEN_PARTUUID = None                       # z.B. "1234-ABCD" - die Welt lebt dann bestaendig auf dieser Partition, sonst im RAM

BODEN_DATEISYSTEM = "ext4"                  # der Boden, in den gepflanzt wird
BODEN_PYTHON_URL = "https://github.com/astral-sh/python-build-standalone/releases/download/20241016/cpython-3.12.7+20241016-x86_64-unknown-linux-gnu-install_only.tar.gz"
BODEN_INITRAMFS_ORDNER = "initramfs_wurzel" # Wurzel des frisch geborenen Systems


# ------------------------------------------------------------
#  WELT-SAMEN - wo der Bootsatz die Farbsprache borgt
#  (Nachbar-Klon des Colorverse; eigener Lager als Letzter)
# ------------------------------------------------------------

WELT_PFAD = ["../Colorverse", "Colorverse", "../github__smori-start-seed__Colorverse"]
