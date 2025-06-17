---
id: 7932
title: 'Raspberry Pi 3 NAS: Debian, Apache, Samba, BitTorrent Sync, BitTorrent [In-Progress]'
date: '2017-01-29T18:06:23-08:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=7932'
permalink: /2017/01/29/raspberry-pi-3-nas-debian-apache-samba-bittorrent-sync-bittorrent-in-progress/
categories:
    - Projects
---

NAS stands for Network Accessible Storage, but in this post we are taking it to the next level! ![](https://blog.cjtrowbridge.com/wp-content/uploads/2016/12/raspberry-pi-3-1-1.jpg)I will show you how to build a Raspberry Pi 3 NAS with a few extra features:

- Using Debian as the OS will be easy to secure and light on resources, but also Debian runs on anything, so almost all of these steps will work on other hardware as well. If you do not want to use a Pi, skip to the "Setting up Networking" step.
- Apache will **share files over the web**, and secure them with a password.
- Samba **shares files over the local network**.
- BitTorrent Sync automatically backs up of all my devices in real time.
- BitTorrent will allow me to remotely download files to my NAS and then access them. This means I can download large or slow files from my phone, or while my laptop is off.

## The Hardware

Debian famously runs on anything, so probably any hardware will work, but I wanted to do this with a Raspberry Pi 3 so I picked one up along with a few accessories; - [Raspberry Pi 3 Model B](https://www.amazon.com/gp/product/B01CD5VC92/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B01CD5VC92&linkCode=as2&tag=cj0e0-20&linkId=e8f9e6b80e109d8018089d52e3cd2182)![](//ir-na.amazon-adsystem.com/e/ir?t=cj0e0-20&l=am2&o=1&a=B01CD5VC92) ($39 on Amazon)
- [Clear acrylic case](https://www.amazon.com/gp/product/B01CDVSBPO/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B01CDVSBPO&linkCode=as2&tag=cj0e0-20&linkId=f267ba49f31fcf01c1e2f4acbaa4b309)![](//ir-na.amazon-adsystem.com/e/ir?t=cj0e0-20&l=am2&o=1&a=B01CDVSBPO) This is probably unnecessary, but it seemed like a good precaution to protect the Pi and the surfaces it sits on. ($6.95 on Amazon)
- [Touchscreen for the Pi](https://www.amazon.com/gp/product/B01CNJVG8K/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B01CNJVG8K&linkCode=as2&tag=cj0e0-20&linkId=7e8cbc138b008c2e799bdf33d127d79f)![](//ir-na.amazon-adsystem.com/e/ir?t=cj0e0-20&l=am2&o=1&a=B01CNJVG8K) ($21.99 on Amazon) This was kind of a nightmare to set up. I would skip this unless you really want it.

**I already had these other three items, but here they are if you want the same ones!**- [2TB WD USB Drive](https://www.amazon.com/gp/product/B00D0L5BH8/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B00D0L5BH8&linkCode=as2&tag=cj0e0-20&linkId=c7ad6fb021f828b9cfb170130b208e4f)![](//ir-na.amazon-adsystem.com/e/ir?t=cj0e0-20&l=am2&o=1&a=B00D0L5BH8) ($74 on Amazon.)
- [2A USB Charger](https://www.amazon.com/gp/product/B01LCDJ7LG/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B01LCDJ7LG&linkCode=as2&tag=cj0e0-20&linkId=4b216b254f009924f27e4104540e0ce3)![](//ir-na.amazon-adsystem.com/e/ir?t=cj0e0-20&l=am2&o=1&a=B01LCDJ7LG) We will need the extra amps to power both the pi and the hdd. ($10.99 on Amazon)
- [16GB MicroSD Card](https://www.amazon.com/gp/product/B010Q57SEE/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B010Q57SEE&linkCode=as2&tag=cj0e0-20&linkId=b95e803798afbd5a0d0accc110c1972f)![](//ir-na.amazon-adsystem.com/e/ir?t=cj0e0-20&l=am2&o=1&a=B010Q57SEE) ($6.99 on Amazon)

## Installing the OS

Debian runs on anything, but it needs to know how. The Raspberry Pi uses a lot of unusual hardware which is not supported by mainstream Debian, so Raspberry Pi have come out with several customized versions which have support for all their hardware. I decided to use the most lightweight version they offer, Raspbian Jessie Lite. Ideally, I would like to star with just pure Debian, but that would involve building a kernel and that doesn't sound like fun. Head over to the [official site](https://www.raspberrypi.org/downloads/raspbian/) or [click here](magnet:?xt=urn:btih:ec72242b6fb3e082172759157096a9223e7c278d&dn=2016-11-25-raspbian-jessie-lite.zip&tr=http%3a%2f%2ftracker.raspberrypi.org%3a6969%2fannounce) to get the torrent for Raspbian Jessie. Now head over to Sourceforge and download [Win32DiskImager](https://sourceforge.net/projects/win32diskimager/). Use that to write the image from the torrent onto the SD card. ## If You Decided To Get That Touchscreen...

Like I said, setting it up is a nightmare. I got the "Kuman 3.5 Inch 480x320 TFT Touch Screen" and eventually figured out how to set it up by reading through dozens of angry Amazon comments until I pieced this together. Open the sd card you wrote the image to. Edit the file "/boot/cmdline.txt" and change its contents to... (All one line) ```
dwc_otg.lpm_enable=0 console=tty1 console=ttyAMA0,115200 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait fbcon=map:10 fbcon=font:ProFont6x11 logo.nologo
```

Now, edit "/boot/config.txt" and add onto the end... ```
dtparam=audio=on
dtparam=spi=on
dtoverlay=ads7846,penirq=25,penirq_pull=2,xohms=150,swapxy=1,xmin=300,ymin=700,xmax=3800,ymax=3400,pmax=255
dtoverlay=waveshare35a
```

Go to [this GitHub](https://github.com/swkim01/waveshare-dtoverlays) and download the file "waveshare35a.dtb." Rename it to "waveshare35a.dtbo" and put it in the directory "/boot/overlays" That's all it takes! ;P ## Setting Up Networking

Now you will need to eject the sd card and boot up the pi with the screen attached, as well as a usb keyboard. **The default username is pi, and the default password is raspberry.**In order to connect the Pi to Wifi, type "sudo nano /etc/wpa\_supplicant/wpa\_supplicant.conf" and add the following... ```
network={
  ssid="YOUR SSID"
  psk="YOUR PSK"
}
```

Save that and exit. Now lets set a static IP. Select an IP outside the range of your router's DHCP and then type "sudo nano /etc/network/interfaces". Find the line that says "iface wlan0 inet manual" and replace it like this... ```
iface wlan0 inet static
        address 192.168.1.200
        netmask 255.255.255.0
        gateway 192.168.1.1
```

Leave everything before and after that line we replaced, but all all this stuff in place of that line. Last but not least, run "sudo raspi-config". Under boot options, set Desktop/CLI to "console autologin" Under advanced options, enable ssh server. Now exit raspi-config and reboot with "sudo reboot." You can disconnect the keyboard. We will no longer need it. This is a good time to move the Pi to its eventual destination if you would like. ## Remote Access

Install Putty or another SSH client and use it to connect to the static IP you just set up. In order to use SSL, we will need to add another repository to the package manager. Type "sudo nano /etc/apt/sources.list" and add... ```
deb http://ftp.debian.org/debian jessie-backports main
```

Now we need to make sure everything is up to date with "sudo apt-get update &amp;&amp; sudo apt-get upgrade" Now let's install all the things we will need: ```
sudo apt-get install fail2ban apache2 screenfetch htop nload python-certbot-apache -t jessie-backports && sudo a2enmod rewrite && sudo service apache2 restart
```

This will install the following: - **Fail2Ban:** Prevents bruteforce ssh attacks.
- **Apache2:** Shares files over the web, securely.
- **Screenfetch:** Let's us share sweet screenshots.
- **Htop:** Shows resource usage in case there is a problem.
- **Nload:** Shows a graphical representation of real-time network usage. Good ambient display.
- **Certbot:** Gives us free SSL through LetsEncrypt.

## Set Up The Web Server

Change directory to the new webroot with "cd /var/www" and remove the default files with "rmdir html --ignore-fail-on-non-empty" Edit the default VirtualHost configuration file, "sudo nano /etc/apache2/sites-available/000-default.conf". Change the line "DocumentRoot /var/www/html" to "DocumentRoot /var/www" and save the file. 