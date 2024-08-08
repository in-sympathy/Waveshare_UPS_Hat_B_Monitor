# Waveshare_UPS_Hat_B_Monitor
A customised fork of a Python code example for monitoring UPS Hat (B) from Waveshare and performing power consumption optimisation and safe shutdown.

I added an ability to not only monitor how much battery you have left, but also:
1) make sure you have a safe shutdown 

2) cancel a shutdown if you plug your Pi before the scheduled power off time

3) stop qbittorrent-nox whenever Pi switches to batteries

4) start qbittorrent-nox again when Pi is charging and has 90% battery or more


A few things to remember:

1) Check https://alertzy.app for details on setting up their awesome push notifications service prior to running the script

2) Initial run of this script should only happen on a Pi itself with a connected display. VNC can be used, but SSH can not. Be warned!
