# Waveshare_UPS_Hat_B_Monitor
A customised fork of a Python code example for monitoring UPS Hat (B) from @waveshare and performing power consumption optimisation and safe shutdown.

My version of the code allows to not only monitor how much battery you have left, but also:
1) Makes sure you have a safe shutdown when the need be.

2) Cancels a shutdown if you plug your Pi before the scheduled power off time.

3) Stops qbittorrent-nox whenever Pi switches to batteries if it was running to save power (in case you use it).

4) Starts qbittorrent-nox again when Pi is charging and has 80% battery or more (again - if you have it on your Pi).



To start using it:

1) Check https://alertzy.app for details on setting up their awesome push notifications service prior to running the script.

2) Clone the repository and initially run "./ups_monitor_launcher.sh" on a Pi itself with a connected display. VNC can be used, but SSH can not. Be warned - otherwise your $DISPLAY and $XAUTHORITY won't be correctly identified by launcher shell script.
