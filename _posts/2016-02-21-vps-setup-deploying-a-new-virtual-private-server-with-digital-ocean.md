---
id: 6936
title: 'VPS Setup: Deploying A New Virtual Private Server With Digital Ocean'
date: '2016-02-21T12:15:47-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6936'
permalink: /2016/02/21/vps-setup-deploying-a-new-virtual-private-server-with-digital-ocean/
categories:
    - Projects
    - 'Tech 2U'
---

This is a subpost of the larger post [Updated Comprehensive VPS Setup Documentation](https://blog.cjtrowbridge.com/2016/02/21/updated-comprehensive-vps-setup-documentation/). I like Digital Ocean ([Referral Link](https://m.do.co/c/ecb56e953504)) for my VPS host. The first step in creating a new VPS is to select a Linux distribution. I always use the most current version of Debian. At the time of this post, that is version 8.3 x64. Decide on an [FQDN](https://en.wikipedia.org/wiki/Fully_qualified_domain_name) and use it as the hostname and hit deploy! It should take about a minute and then you will receive an email with the temporary root password. Use [putty](http://www.putty.org/) to log in, and you will be prompted to change it. Make sure to choose a root passsword with a [high level of entropy](https://xkcd.com/936/).