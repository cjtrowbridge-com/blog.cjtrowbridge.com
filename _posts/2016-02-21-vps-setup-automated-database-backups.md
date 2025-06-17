---
id: 6950
title: 'VPS Setup: Automated Database Backups'
date: '2016-02-21T12:47:16-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6950'
permalink: /2016/02/21/vps-setup-automated-database-backups/
categories:
    - Projects
    - 'Tech 2U'
---

This is a subpost of the larger post [Updated Comprehensive VPS Setup Documentation](https://blog.cjtrowbridge.com/2016/02/21/updated-comprehensive-vps-setup-documentation/). Create a new directory for the backups; `mkdir /var/backups/mysql` I added the following line to /etc/crontab in order to facilitate automatic database backups; `0 22 * * * root /usr/bin/mysqldump -uroot -i[MySQL Root Password] [MySQL Database Name] | gzip > /var/backups/mysql/mysql-backup-$( date +'\%Y-\%m-\%d_\%H-\%M-\%S' ).sql.gz`