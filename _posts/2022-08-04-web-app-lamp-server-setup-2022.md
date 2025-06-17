---
id: 14618
title: 'Web App LAMP Server Setup 2022'
date: '2022-08-04T19:31:51-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=14618'
permalink: /2022/08/04/web-app-lamp-server-setup-2022/
categories:
    - Projects
---

#### Install LAMP Software

sudo apt update &amp;&amp; sudo apt upgrade sudo apt install fail2ban apache2 mariadb-server php php-{cli,bcmath,bz2,curl,intl,gd,mbstring,mysql,zip} sudo mysql\_secure\_installation #### Install Certbot For SSL

To install SSL, [use Certbot](https://certbot.eff.org/). #### Install Resilio-Sync

Install Resilio Sync for Backup transportation and versioning; <https://help.resilio.com/hc/en-us/articles/206178924-Installing-Sync-package-on-Linux>#### Add Scripts For Backups And Permissions

Various scripts and files (That go in various places) <https://github.com/cjtrowbridge/vps-home>cd ~ wget https://raw.githubusercontent.com/cjtrowbridge/vps-home/master/backups.sh chmod +x backups.sh wget https://raw.githubusercontent.com/cjtrowbridge/vps-home/master/fix\_permissions.sh chmod +x fix\_permissions.sh #### Set up Daily Backups

Add this line to the end of /etc/crontab 0 0 \* \* \* root bash "/root/backups.sh" #### Set up Automatic Off-Site xfer

Create a Resilio-Sync shared folder on your NAS and then put the RW key in the cj.conf file from the repository above and put that file in /etc/resilio-sync/cj.conf cd /etc/resilio-sync/ wget https://raw.githubusercontent.com/cjtrowbridge/vps-home/master/cj.conf **Put the RW key in the cj.conf file...**rslsync --config /etc/resilio-sync/cj.conf #### Test Backups

Run the ~/backups.sh and watch the resilio dashboard on your NAS to see if traffic starts coming in. Viola! #### Database Memory and CPU Optimizations

I like to use [these optimizations](https://dba.stackexchange.com/questions/264983/mysql-server-stops-running-due-to-out-of-memory-errors) to minimize resource consumption and virtual machine costs.