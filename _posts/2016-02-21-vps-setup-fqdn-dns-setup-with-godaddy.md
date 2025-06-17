---
id: 6940
title: 'VPS Setup: FQDN DNS Setup With GoDaddy'
date: '2016-02-21T12:24:57-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6940'
permalink: /2016/02/21/vps-setup-fqdn-dns-setup-with-godaddy/
categories:
    - Projects
    - 'Tech 2U'
---

This is a subpost of the larger post [Updated Comprehensive VPS Setup Documentation](https://blog.cjtrowbridge.com/2016/02/21/updated-comprehensive-vps-setup-documentation/). Once you have a VPS deployed and know its static IP, you can forward a FQDN to it by creating a new A Record. I use GoDaddy for my DNS registration because they are simple, reliable, and quick.

1. In order to do this with GoDaddy, log into your account
2. Next to "Domains" click on "Manage"
3. Click on the domain you want to forward. If you want to forward a subdomain, click on the domain it will be a subdomain of
4. Click over to the "DNS ZONE FILE" tab

- If you are trying to forward a subdomain 
    1. Click "Add Record"
    2. We want to create an "A Record"
    3. Use the subdomain as the hostname and then the static IP of the server as the "POINTS TO"
    4. Save changes
- If you are trying to forward a domain 
    1. Edit the record for the "@" host and point it to the static IP following the same directions as above.