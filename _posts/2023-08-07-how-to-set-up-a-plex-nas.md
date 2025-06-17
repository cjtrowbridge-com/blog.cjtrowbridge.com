---
id: 14832
title: 'How To Set Up A Plex NAS'
date: '2023-08-07T12:26:47-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=14832'
permalink: /2023/08/07/how-to-set-up-a-plex-nas/
categories:
    - Featured
---

Plex is a service that lets you play your own media files on your smart tv, laptop, cell phone etc. with a free app that works just like the apps for Netflix, JBO, etc. The best way to do this is by setting up a NAS or Network Accessible Storage. This is just a big shared folder on your home network where you can put all your media files and then Plex shares them with all your devices and even with your friends and family at their homes if you want.

## Hardware List

- I'm going to show you how to do this with Synology. [Here is a link to the cheapest one they sell that supports Plex](https://amzn.to/3YsbMWX). This is what I have used for years, and it works great. I actually have two of them mirrored just to make sure nothing can ever get lost.
- You're going to need a hard drive. [I recommend WD Red](https://amzn.to/3DSnh01). These disks are designed for this specific purpose, and they work great. They are also extremely reliable and long-lasting. [These are the specific ones I use in both of my mirrored NASes.](https://amzn.to/3DSnh01) And you can also get [cheaper alternatives](https://amzn.to/3OKma9c) but just be aware that the performance is not going to be as good and there is always the risk of failure.

## Setup

- Setting it up is super easy. Just insert the drive into the nas and turn it on.
- Go to <https://finds.synology.com/> and it will redirect you to the local IP of your NAS. 
    - I highly recommend updating your router's settings to give the nas a static ip so you can always find it easily.
- It will guide you through setting up the software and formatting the drive.
- Next go into the package manager and click on settings. At the bottom under trust level, change the settings to allow community packages.![Trust Level](https://blog.cjtrowbridge.com/wp-content/uploads/2023/08/trust-level-1-1.jpg)
- Next, go to the package sources tab and add this one... <http://packages.synocommunity.com/>![Package Sources](https://blog.cjtrowbridge.com/wp-content/uploads/2023/08/package-sources-1-1.jpg)
- Now you can install Plex from the package manager.
- Then go into Plex and open the settings menu.
- Under Manage, click on Libraries.
- Add a library for each type of content and point it to the folder where you are storing that specific type of content.
- It will analyze the content and make it available to any devices on your network that are using the Plex app. Install it on your smart TV, cell phone, Steam Deck, laptop, etc and enjoy!

## Other Things To Keep In Mind

- You need to use a good VPN to download files anonymously online. I have tested all the different options and [PIA is the best one](https://www.privateinternetaccess.com/pages/buy-a-vpn/1218buyavpn?invite=U2FsdGVkX186HQf9oL4874AcUyIDEX0qObfUsv5E1v0%2CRagS2uHNEaLV1tf2IeqxPFWUeHs). It's fast, it's cheap, it works on up to five devices at once, and it keeps you safe. [Use this link to try it free for 30 days](https://www.privateinternetaccess.com/pages/buy-a-vpn/1218buyavpn?invite=U2FsdGVkX186HQf9oL4874AcUyIDEX0qObfUsv5E1v0%2CRagS2uHNEaLV1tf2IeqxPFWUeHs).