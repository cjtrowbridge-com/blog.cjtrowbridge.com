---
id: 6948
title: 'VPS Setup: Install Free SSL From LetsEncrypt'
date: '2016-02-21T12:36:46-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6948'
permalink: /2016/02/21/vps-setup-install-free-ssl-from-letsencrypt/
categories:
    - Projects
    - 'Tech 2U'
---

This is a subpost of the larger post [Updated Comprehensive VPS Setup Documentation](https://blog.cjtrowbridge.com/2016/02/21/updated-comprehensive-vps-setup-documentation/). LetsEncypt allows us to setup free SSL certificates for our virtualhosts. First, make sure you are in your root home directory "/~" and then clone the LetsEncrypt git repository; `git clone https://github.com/letsencrypt/letsencrypt`Enter the directory `cd letsencrypt`And run the automatic script `./letsencrypt-auto --apache`It will ask which virtual hosts you want to install certificates for, and then it does all the work for you! When you need to renew these, check out my tutorial [Renewing Free LetsEncrypt SSL Certificates](http://blog.cjtrowbridge.com/2016/02/21/renewing-free-letsencrypt-ssl-certificates/).