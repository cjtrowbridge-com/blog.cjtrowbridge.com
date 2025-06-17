---
id: 12850
title: 'OAuth Password Redirects'
date: '2018-04-16T16:26:17-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=12850'
permalink: /2018/04/16/oauth-password-redirects/
categories:
    - Ideas
---

It's frustrating and insecure to use htpasswords to secure a web server. Even if you use very long passwords, it would still technically be possible to bruteforce even with something like fail2ban given sufficient client IP addresses. Unfortunately for some applications like Wordpress, PHPMyAdmin or many other legacy applications, there just isn't a better alternative like OAuth which is easy to integrate or even possible to completely integrate. This gave me the idea to create a tool which automatically cycles to a new password every so often just like a Ubikey. This would be trivially easy since all you have to do is run the htpasswd command to set a new extremely secure password on a regular interval. Then it becomes impossible to bruteforce the password quickly enough to avoid the change. Next you have a secure application server somewhere running the latest OAuth libraries. That server authenticates the user with OAuth and even a second factor, then redirects or links to the remote htpasswd secured site... https://username1:pass1@site.com/wp-admin https://username2:pass2@site.com/phpmyadmin If you're using https then the url in the redirect is strongly encrypted. DNS will still leak the destination domain unless you're using secure DNS, but either way the username and password will be very safe.