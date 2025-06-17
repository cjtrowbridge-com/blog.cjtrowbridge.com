---
id: 5238
title: 'Migrating Everything to a Cloud VPS'
date: '2015-12-02T15:52:11-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=5238'
permalink: /2015/12/02/migrating-everything-to-a-cloud-vps/
categories:
    - Projects
---

Over the last six months, I undertook the project of migrating all of my web apps, sites, and other projects to a new XenHypervisor which I hosted at home for free. I always thought of this as a transitional step. It doesn't make sense to try to host these kinds of things at home. After all, I don't want to be a datacenter provider, but I wanted to understand how they work before I outsourced my infrastructure to a good provider. [![digital-ocean-logo](https://blog.cjtrowbridge.com/wp-content/uploads/2015/12/digital-ocean-logo-11-1-1.png)](https://blog.cjtrowbridge.com/wp-content/uploads/2015/12/digital-ocean-logo-11-1-1.png)After lots of research, I decided on DigitalOcean ([Referral Link](https://www.digitalocean.com/?refcode=ecb56e953504)) as the best option. It's only $5/month and I don't have to worry about infrastructure or connectivity issues.

- Setting up the VPS was easy and took just a few seconds. DigitalOcean makes it very simple to create the new machine, and they had the latest version of Debian as an option.
- Next, I setup an A-Record for ([vps1.cjtrowbridge.com](https://vps1.cjtrowbridge.com)) a new subdomain off of my main domain. This serves as a FQDN for this new VPS. (Note that this is my second VPS, I am not using a 1-based index :P )
- Referencing my previous tutorial about [Setting Up Debian as a LAMP Server](http://blog.cjtrowbridge.com/2015/10/04/setting-up-debian-as-a-lamp-server/), I configured the new machine with all the normal tools.
- I created virtual hosts for all the sites I was migrating in and copied those files and databases over to the new VPS.
- I used [this tutorial](https://wiki.apache.org/httpd/PasswordBasicAuth) to secure the root web directory for the VPS' FQDN. This directory contains all the directories for the virtual hosts and tools lime PHPMyAdmin, as well as the backups for other servers. With valid credentials, this lets you see all the tools, hosts, and backups.
- Lastly, I setup BitTorrent Sync using [this tutorial](http://forum.bittorrent.com/topic/18974-debian-and-ubuntu-server-unofficial-packages-for-bittorrent-sync/) in order to securely backup files across the internet.