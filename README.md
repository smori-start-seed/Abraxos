# Abraxos – der Boden des FARB-OS

Abraxos traegt das Colorverse. Er ist nicht die Welt - er ist der Grund,
auf dem die Welt atmet: Kernel, initramfs, USB-Stick, Anbau auf
echter Hardware.

## Die drei Stufen
1. `Keim.py` – Erststart auf echter Hardware: attestiert die Geburt, verankert
   die Erinnerung, optional systemd-User-Dienst
2. `Bootsatz.py` – baut das bootfaehige Medium: ein Kernel, eine
   initramfs-Wurzel, kein Login, das Colorverse als PID 1
   - `sudo python3 Bootsatz.py` : initramfs + Kernel (Beweis in qemu)
   - `sudo python3 Bootsatz.py --iso` : optisches Medium (hybrid)
   - `sudo python3 Bootsatz.py --usb` : Medium fuer den Stick; die
     Ausgabe druckt den echten dd-Befehl. Das OS schreibt nie selbst
     auf ein Geraet - die Hand des Interactors entscheidet.
3. `Boden.py` – freiwillig: Anbau auf Festplatte (dreifaches Wort, alles
   landet im gate_log). Der erste Boden ist und bleibt der Stick;
   bestehende OS leben daneben, nie angeruehrt.

## Die Welt
Die Farbsprache lebt in [Colorverse](https://github.com/smori-start-seed/Colorverse).
Abraxos borgt sie beim Bau vom Nachbar-Klon (`WELT_PFAD` in `config.py`) und
legt seine eigene config als Bodenschicht unter die Welt-config.

## Proben
`.github/workflows/boot.yml` bootet den Keim und den fertigen Stick als
echtes usb-storage-Geraet in qemu und wartet auf die serielle Beweislinie:
`[FARB-OS] Neugeboren ...`

## Groesse
Der Bootsatz berichtet bei jedem Bau die echten Zahlen: Kernel, initramfs,
Wurzel gesamt, fertiges Medium - alles in MB.

## Bestaendigkeit
`BODEN_PARTUUID` in `config.py` setzen - die Welt lebt dann auf dieser
Partition und erinnert sich ueber den Stromausfall. Ungesetzt atmet sie
im RAM, ein Leben pro Strom.
