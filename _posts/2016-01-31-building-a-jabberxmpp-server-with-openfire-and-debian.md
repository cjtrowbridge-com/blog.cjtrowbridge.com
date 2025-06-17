---
id: 6817
title: 'Building a Jabber/XMPP Server With OpenFire and Debian'
date: '2016-01-31T10:58:04-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6817'
permalink: /2016/01/31/building-a-jabberxmpp-server-with-openfire-and-debian/
categories:
    - Projects
    - 'Tech 2U'
---

I wanted to create a new chat server for my company for two reasons. For one, we want any confidential information to stay as in-house as possible. And two, we wanted web access because lots of our employees move around between different offices and they don't want to have to install chat programs every day. We had previously been using OpenFire hosted on a local baremetal machine which did not have a CA signed cert. This meant we could not use OpenFire's web access tool in order to access the chat tool because it did not support self-signed certs. Trillian could be talked into supporting self-signed certs, but a more elegant solution was called for. I decided to create a new jabber/xmpp VPS with DigitalOcean ([Referral Link](https://www.digitalocean.com/?refcode=ecb56e953504)) and install OpenFire and SparkWeb.

1. Step one was creating a new VPS or "Droplet" with DigitalOcean ([Referral Link](https://www.digitalocean.com/?refcode=ecb56e953504)) I chose Debian x64 for the OS and used my new FQDN for the hostname.
2. I created a new DNS "A Record" with our hosting provider to forward my new FQDN to this new server's IP.
3. Install all the initial stuff. This should be self-explanatory: `apt-get -y update && apt-get -y upgrade && apt-get -y install default-jre fail2ban apache2 && apt-get -y install mysql-server && apt-get -y install php5 php-pear php5-mysql && apt-get -y install php5-mcrypt && php5enmod mcrypt && a2enmod rewrite && apt-get -y install php5-curl phpmyadmin screenfetch htop nload curl git ntp && service apache2 restart && mysql_secure_installation`
4. Navigate to the downloads page `http://www.igniterealtime.org/downloads/index.jsp` and find the path to the Debian installer file of the current version 
    1. Get the installer with `wget -O openfire_installer.deb [LINK]`, replacing \[LINK\] with the link from the page in the previous step
    2. In my case, it was `wget -O openfire_installer.deb http://www.igniterealtime.org/downloadServlet?filename=openfire/openfire_4.0.1_all.deb`
5. Install OpenFire with `dpkg --install openfire_installer.deb`
6. Block insecure access to the OpenFire admin console with `iptables -A INPUT -i eth0 -j REJECT -p tcp --dport 9090`
7. Install LetsEncrypt for free SSL: 
    1. Now that OpenFire is configured, navigate to the root user's home directory and clone letsencrypt with ``git clone https://github.com/letsencrypt/letsencrypt``
    2. Enter the directory `cd letsencrypt`
    3. And run the automatic script `./letsencrypt-auto --apache`
    4. It will ask which virtual hosts you want to install certificates for, and then it does all the work for you!
8. Navigate to https://\[FQDN\]:9091 and complete the configuration

 **UPDATE 2016-07-31**We have officially migrated to Slack as a company. This provides compliance with all the various requirements of our many managed services clients. At long last, this service has been outsourced to a competent partner, and it is one less thing we need to worry about! Nevertheless, this guide will show you how to create a simple, free alternative with Jabber/XMPP.