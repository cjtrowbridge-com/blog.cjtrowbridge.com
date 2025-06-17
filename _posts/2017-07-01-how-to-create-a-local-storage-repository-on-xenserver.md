---
id: 8746
title: 'How To Create a Local Storage Repository on XenServer'
date: '2017-07-01T13:24:22-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8746'
permalink: /2017/07/01/how-to-create-a-local-storage-repository-on-xenserver/
categories:
    - Projects
    - 'Tech 2U'
---

I was working with a XenServer in a complex corporate network environment, and it was not possible for this server to access any samba shares, such as my laptop. I needed to put some ISOs on it, so I decided to create a local storage repository. This way, I would be able to simply -wget an ISO from the web, and then use it locally. First, SSH into the XenServer and create a directory for the repository;

> mkdir -p /var/opt/xen/LocalRepo

Then, tell Xen to create a XenServer Storage Repository at that directory; > xe sr-create name-label=LocalRepo type=iso device-config:location=/var/opt/xen/LocalRepo device-config:legacy\_mode=true content-type=iso

Now move to the directory and then wget whatever ISOs you need... > cd /var/opt/xen/LocalRepo

> wget http://releases.ubuntu.com/16.04.2/ubuntu-16.04.2-desktop-amd64.iso

Now you're cooking with gas! PS. Make sure to check your free space and make sure your ISOs will fit. This partition is not very big by default. > df -H