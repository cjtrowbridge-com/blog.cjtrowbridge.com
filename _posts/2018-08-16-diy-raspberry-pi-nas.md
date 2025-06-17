---
id: 10725
title: 'DIY: Raspberry Pi NAS'
date: '2018-08-16T22:56:38-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=10725'
permalink: /2018/08/16/diy-raspberry-pi-nas/
categories:
    - Blog
    - Projects
---

In this tutorial, I will demonstrate how to configure a Raspberry Pi NAS. [Network Attached Storage](https://en.wikipedia.org/wiki/Network-attached_storage) (Also known as Network Accessible Storage or a NAS) essentially creates a shared folder on your local network which lets all your computers and devices access the files stored there. You will need a Raspberry Pi. I am using a [Raspberry Pi Zero W](https://amzn.to/2nHBndJ) with the [iUniker case](https://amzn.to/2vPMsOu), but this tutorial should work for any Raspberry Pi, including the [Raspberry Pi 3B](https://amzn.to/2PfMGGD) and the case is only for aesthetic purposes. You will also need a Micro SD card for the operating system. I am using a [Sandisk 16gb Micro SD Card](https://amzn.to/2wcQBeJ). Lastly, you will need some kind of storage such as a USB external hard drive. I am using a [WD Ultra 2Tb](https://amzn.to/2PcVX2a). During the setup process, you will also need an HDMI cord as well as a USB mouse and keyboard. The Raspberry Pi Zero W that I bought came with an adapter from Mini-HDMI to regular HDMI, but I picked up a Mini-HDMI to standard HDMI cord to use instead which you will see in the photos. Either way works the same. If you are using the Raspberry Pi Zero W like me, you will need a usb hub as there are not enough ports to plug all these things in at the same time. The Raspberry Pi Zero W kit that I bought also came with a USB-OTG cable to adapt USB-A cords to the micro-USB ports on the Raspberry Pi Zero W.

# Create The Boot Drive

The first step is to download [Raspbian](https://www.raspberrypi.org/downloads/raspbian/) from the Raspberry Pi website. ![](https://blog.cjtrowbridge.com/wp-content/uploads/2018/08/raspbian-download-1-1.png)In order to write the image file to the Micro SD card, we need to use a free tool called [Win32 Disk Imager](https://sourceforge.net/projects/win32diskimager/). Simply open it, select the Raspbian image file, select the Micro SD card, click write, and you're done. ![](https://blog.cjtrowbridge.com/wp-content/uploads/2018/08/win32-disk-imager-raspbian-1-1.png)Make sure to eject the card properly before removing it from your computer since everything on it is sensitive and important. ## Hook Everything Up

Now it's time to insert the card into the Raspberry Pi. Next, connect the mouse, keyboard, and monitor. Then, connect the USB hard drive, and lastly connect the power. Once it's all connected, it should look something like this... ![](https://blog.cjtrowbridge.com/wp-content/uploads/2018/08/raspberry-pi-zero-nas-set-up-1-1.jpg)## Software Configuration

The Pi will boot up and ask you to configure a password and connect to wifi. Next, click on the menu in the top corner and find the configuration app under preferences. Click over to the interfaces tab and enable SSH and VNC. This will allow you to remote in later if you need to and avoid hooking the Pi back up to a mouse, keyboard, and screen. You should probably set a static IP for your Pi, so that it isn't moving around on the network and confusing the other devices. This step is optional but recommended. It will be different with every router. There are two ways to do this. You can configure a static IP on the Pi which has become a complex process, or you can configure it on your router. I would recommend searching online for a guide for your specific router. Again, this step is optional. This next part is done in the command line interface. You can do this via SSH from another machine with a free tool like Putty, or you can do it by logging into the Pi and clicking the terminal button at the top. This is probably the simpler method. Start with this command to make sure everything is up to date. It could take quite some time depending on how recently the Raspbian image we used was updated on the website. > apt-get update &amp;&amp; apt-get upgrade &amp;&amp; apt-get dist upgrade

We will need to install a few packages in order to set the Pi up as a NAS as well as for security, debugging, and monitoring purposes; > apt-get install fail2ban nload screenfetch samba samba-common-bin

Now edit the Samba configuration file; > sudo nano /etc/samba/smb.conf

Find the line that says ";wins support = no" and change it to "wins support = yes" Then find the line that says workgroup and change it to your workgroup name. Press CTRL+X to exit and then Y to save. ## Set Up Sharing

First we need to find the path of our USB drive. This part is simple. Just type; > df -h

You will see something like this... ![](https://blog.cjtrowbridge.com/wp-content/uploads/2018/08/df-h-1-1.png)In my case, the bottom line shows the path "/media/pi/CJ-2TB." This is the name of the USB drive I plugged into the Pi. You can see there are 203 free gigabytes. This is definitely the correct drive. Go back to the samba configuration file; > sudo nano /etc/samba/smb.conf

Paste the following at the end. Change the path and title to match your shared drive. Press CTRL+X to exit and then Y to save, just like before. > \[CJ-2TB\] comment=Raspberry Pi Share path=/media/pi/CJ-2TB browseable=Yes writeable=Yes only guest=no create mask=0777 directory mask=0777 public=no

Now we just need to create a user account for this shared folder. This can be anything, but it simplifies things to use the same username as the login... > sudo smbpasswd -a pi

You will be prompted to create a password. This can be the same or different from your main password. ## That's It!

Congratulations, you have a Raspberry Pi NAS!