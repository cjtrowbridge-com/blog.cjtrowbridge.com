---
id: 4281
title: 'Building a XenServer at Home with a Local Repository'
date: '2015-11-05T07:19:40-08:00'
author: cjtrowbridge
layout: post
guid: 'http://cjtrowbridge.com/?p=4281'
permalink: /2015/11/05/building-a-xenserver-at-home-with-a-local-repository/
categories:
    - Projects
---

I have gone over the process of setting up a XenServer before, but this time there is one major difference. It will be using a local repository instead of using a NAS as an ISO repository. This was a little tricky but not too bad. Once I had XenServer installed and configured, I opened an SSH session on the server. I used the following commands to create a local repository; `<pre>mkdir -p /var/opt/xen/ISO_Storexe sr-create name-label=LocalISO type=iso device-config:location=/var/opt/xen/ISO_Store device-config:legacy_mode=true content-type=iso</pre>`Now when I open XenCenter, there was a local repository attached to the server. I renamed the repository form within XenCenter to be more clear.

<center>![local_repository](http://blog.cjtrowbridge.com/wp-content/uploads/2015/11/local_repository.png)</center>Now I can use wget to download files to the repository like so; `<pre>cd /var/opt/xen/ISO_Storewget http://cdimage.debian.org/debian-cd/8.2.0/amd64/iso-cd/debian-8.2.0-amd64-CD-1.iso</pre>` Now I can create a new vm and use this local ISO! Once the download is complete, the file will be visible in the list; ![debian_local](http://blog.cjtrowbridge.com/wp-content/uploads/2015/11/debian_local.png)