---
id: 7060
title: 'Automatic Emails For Full Drives In Debian'
date: '2016-03-26T11:36:47-07:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=7060'
permalink: /2016/03/26/automatic-emails-for-full-drives-in-debian/
categories:
    - Blog
---

I have a VPS which I use for storing backups and running some of my projects. This VPS recently filled up, leading to lots of problems. I went looking for a solution which would email automatically whenever a drive starts getting full. I found a bash script online which I modified a bit; I added the hostname to the email is sends and set a lower threshold than the original script. Here is what I ended up with in ~/send\_email\_if\_drive\_full.sh `#!/bin/bashCURRENT=$(df / | grep / | awk '{ print $5}' | sed 's/%//g')THRESHOLD=75`if \[ "$CURRENT" -gt "$THRESHOLD" \] ; then mail -s 'Disk Space Alert' chris.j.trowbridge@gmail.com &lt;&lt; EOF vps1.cjtrowbridge.com Your root partition remaining free space is critically low. Used: $CURRENT% EOF fi Then I added this to the crontab; `0 0 * * 0       root    bash /root/send_email_if_drive_full.sh`