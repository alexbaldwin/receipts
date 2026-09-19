# Deploy to a Raspberry Pi

Tested on a Raspberry Pi Zero 2 W, Raspberry Pi OS Lite 64-bit (Debian 13),
Python 3.13, Epson TM-T88V on the built-in USB-B port.

## Printer: enable the built-in USB port

If the printer has an interface card fitted (Ethernet or serial), it ignores
the built-in USB port until you select it. There is no DIP switch for this.
Use the FEED button:

1. Turn the printer off. Hold FEED and turn it on. Release after the self-test prints.
2. At "Mode Selection", hold FEED for more than 1 second.
3. Press FEED 3 times short, then 1 time long (Customize Value Settings).
4. Press FEED 10 times short, then 1 time long (Interface Selection).
5. Press FEED 2 times short, then 1 time long (Built-in USB).
6. Power cycle the printer.

Short is under 1 second. Long is over 1 second. Do not pick "Auto", it prefers
the interface card. Removing the card also works.

## Pi

The Zero 2 W has two micro-USB ports. Use the one marked USB, not PWR IN.
The cable must carry data. Check with `lsusb`, you should see `04b8:0202`.

```bash
rsync -az --exclude .git --exclude .venv --exclude libdither ./ USER@receipt.local:~/receipts/
ssh USER@receipt.local 'cd ~/receipts && bash deploy/install.sh'
```

Then set `THERMAL_PRINTER_CONNECTION=usb` in `/etc/receipt-printer/server.env`
and `sudo systemctl restart receipt-server`. The rest of the USB values in the
example file match the TM-T88V.

## Test

```bash
curl -X POST http://receipt.local:8080/print -H 'Content-Type: text/markdown' --data '# Hello'
curl -X POST http://receipt.local:8080/print -F file=@photo.jpg -F cut=true
```

Logs: `journalctl -u receipt-server -f`
