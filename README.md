# Waveshare_UPS_Hat_B_Monitor
A customised fork of a Python code example for monitoring UPS Hat (B) from Waveshare and performing power consumption optimisation and safe shutdown.

I added an ability to not only monitor how much battery you have left, but also:
1) Making sure you have a safe shutdown.

2) Cancelling a shutdown if you plug your Pi before the scheduled power off time.

3) Stopping qbittorrent-nox whenever Pi switches to batteries if it was running (in case you use it).

4) Starting qbittorrent-nox again when Pi is charging and has 90% battery or more (again - if you have it on your Pi).



To start using it:

1) Check https://alertzy.app for details on setting up their awesome push notifications service prior to running the script.

2) Clone the repository and initially run "./ups_monitor_launcher.sh" on a Pi itself with a connected display. VNC can be used, but SSH can not. Be warned - otherwise your $DISPLAY and $XAUTHORITY won't be correctly identified by launcher shell script.
