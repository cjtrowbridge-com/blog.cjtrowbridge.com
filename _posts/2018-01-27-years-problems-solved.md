---
id: 9603
title: 'Years of Problems Solved'
date: '2018-01-27T22:11:44-08:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=9603'
permalink: /2018/01/27/years-problems-solved/
categories:
    - Blog
    - Projects
---

> \#!/bin/bash #deletes old backups find /var/www/backups/ -mindepth 1 -mmin +$((60\*24)) -delete #creates new backups tar -czf “/var/www/backups/webs-$( date +’%Y-%m-%d\_%H-%M-%S’ ).gz” /var/www/webs /usr/bin/mysqldump -uroot -p\[mysql root password\] –all-databases | gzip &gt; “/var/www/backups/mysql-$( date +’%Y-%m-%d\_%H-%M-%S’ ).sql.gz”

This is a script I wrote years ago that shall live in infamy. It creates an automatic backup of databases and virtualhost directories. It is called by a cron job each day, and builds the new archive files, depositing them into the backups folder. The backups folder is a Bittorrent Sync repository which automatically copies the backups to other NAS servers. This script also deletes the old backups each day as you can see at the top. Because the files are deleted on this server, the remote repositories they are syncing with retain old versions. This means that all prior backups are saved on the remote NAS server, but only the most recent backups are ever stored locally. Because the files are transfered with the bittorrent protocol, they are end-to-end encrypted, and highly available across an unlimited number of nodes. So the remote NAS servers will share the backups with each other if necessary. This is a super good system which accomplishes highly available and completely free, secure offsite backups. The remote server has a highly secure virtualhost which shares the backups, so they are available to other command line scripts which can fetch them and deploy new versions of these servers in seconds. Also keep in mind this is a simplified version of the script. The actual script I use will create a separate backup file for each database and for each virtualhost. This script will create one single archive of all databases and one single archive of all virtualhosts. This is still a good system, but it is less easy to deploy one single virtualhost or database this way if a server is hosting more than one. ## The Symptom

Every once in a while after some unknown period of time, the Bittorrent Sync stops working. It says there is an unknown error, and it has to be reconfigured. Then it works fine for some unknown period of time but this ALWAYS ALWAYS happens again. It only happened on some servers, despite the same script running on all of them. (I now realize the reason.) I tried for a long time to figure it out but I chocked it up to a bug in BTSync because it is a mildly jank, gratis, closed-source, and long-discontinued product. I just kept periodically reconfiguring BTSync and everything kept working, despite this little annoyance. ## The Cause

Bittorrent Sync stores the configuration files for each repository in a hidden directory within that repository called ".sync". This works just like git does. When my script deletes old files in that directory, it also deletes the Bittorrent Sync configuration files, then BTSync crashes until it is reconfigured. ## The Fix

This is the new script which solves this problem; > \#!/bin/bash #deletes old backups find /var/www/backups/www/ -mindepth 1 -mmin +$((60\*24)) -delete find /var/www/backups/mysql/ -mindepth 1 -mmin +$((60\*24)) -delete #creates new backups tar -czf “/var/www/backups/www/webs-$( date +’%Y-%m-%d\_%H-%M-%S’ ).gz” /var/www/webs /usr/bin/mysqldump -uroot -p\[mysql root password\] –all-databases | gzip &gt; “/var/www/backups/mysql/mysql-$( date +’%Y-%m-%d\_%H-%M-%S’ ).sql.gz”

As you can see, each type of backup now goes into its own subdirectory. Backups are only deleted from the subdirectories. The config files are no longer effected when backups are deleted. WHAT A SATISFYING FIX.