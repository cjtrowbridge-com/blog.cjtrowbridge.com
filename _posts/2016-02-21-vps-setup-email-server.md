---
id: 6944
title: 'VPS Setup: Email Server'
date: '2016-02-21T12:33:43-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6944'
permalink: /2016/02/21/vps-setup-email-server/
categories:
    - Projects
    - 'Tech 2U'
---

This is a subpost of the larger post [Updated Comprehensive VPS Setup Documentation](https://blog.cjtrowbridge.com/2016/02/21/updated-comprehensive-vps-setup-documentation/). Many of my apps send lots of emails, so I usually need to setup a local outbound email server. Secure the port with `iptables -A INPUT -i eth0 -j REJECT -p tcp --dport 25`Install postfix for the server `apt-get -y install postfix && apt-get -y install mailutils`Now edit the config files and change the interface to loopback-only like so; `nano /etc/postfix/main.cf`Find this line; `inet_interfaces =`And change to; `inet_interfaces = 127.0.0.1`Now edit the email aliases; `nano /etc/aliases`At the end of the file, make sure there is a line that starts with root and ends with your email, like so; `root email@domain.com`Save the file and exit. Then run `newaliases` to let Postfix apply the changes. Restarting Postfix is not enough because we changed the interfaces line in the config file. We need to stop and start it like so; `postfix stop``postfix start`