---
id: 8677
title: 'Setting Up PHP Apache2 MySQL MSSQL Server on Azure'
date: '2017-06-07T17:08:17-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8677'
permalink: /2017/06/07/setting-up-php-apache2-mysql-mssql-server-on-azure/
categories:
    - Projects
    - 'Tech 2U'
---

First, update the packages;

> sudo apt-get update &amp;&amp; sudo apt-get upgrade

Set up initial applications; > sudo apt-get -y install unzip fail2ban apache2 mysql-server php5 php5-curl php-pear php5-mysql php5-mcrypt screenfetch htop nload curl git ntp freetds-common freetds-bin unixodbc php5-sybase &amp;&amp; sudo php5enmod mcrypt &amp;&amp; sudo a2enmod rewrite &amp;&amp; sudo service apache2 restart &amp;&amp; sudo mysql\_secure\_installation

## Set Up SMTP Email with Postfix

Create firewall rule to block smtp access (This is redundant because we will configure SMTP for loopback access only); > sudo iptables -A INPUT -i eth0 -j REJECT -p tcp --dport 25

Install Postfix; > sudo apt-get -y install postfix &amp;&amp; sudo apt-get -y install mailutils

Edit postfix config file; > sudo nano /etc/postfix/main.cf

Change "inet\_interfaces = all" to "inet\_interfaces = 127.0.0.1" allowing only loopback requests. This is in addition to the firewall which prevents outside access. Edit aliases list; > sudo nano /etc/aliases

Append this to the end and save; > root email@domain.com

Run this to apply the changes; > sudo newaliases &amp;&amp; sudo postfix stop &amp;&amp; sudo postfix start

Edit the default virtualhost > sudo nano /etc/apache2/sites-available/000-default.conf

Set the ServerName to the fqdn. Save and restart apache2; > sudo service apache2 restart

Edit aptitude's sources list; > sudo nano /etc/apt/sources.list

## Set Up LetsEncrypt for SSL/HTTPS

Install LetsEncrypt Certbot; > sudo apt-get install python-certbot-apache -t jessie-backports

(This may require extra steps. The Debian default aptitude sources list does not contain backports, but the default Azure list does.) Run Certbot to install HTTPS; > sudo apt-get install python-certbot-apache -t jessie-backports

Create a credential set with some high-entropy username and password combination. I like to use a 32-bit random key for both. This will only be transmitted through an SSL 1.2 connection with LetsEncrypt, so it's very safe; > sudo htpasswd -c /etc/apache2/.htpasswd \[Username\]

Edit the ssl-virtualhost and add this within the virtualhost tag; > &lt;Directory "/var/www/"&gt; AuthType Basic AuthName "Restricted Content" AuthUserFile /etc/apache2/.htpasswd Require valid-user &lt;/Directory&gt;

Add this to the end of the end of the file, outside the virtualhost tag in order to enable htaccess if you're going to need that; > &lt;Directory /var/www/&gt; Options Indexes FollowSymLinks AllowOverride All Require all granted &lt;/Directory&gt;

Restart Apache; > sudo service apache2 restart

## Set Up PHPMyAdmin

PHPMyAdmin can also be installed via aptitude, but that exposes it publically and there is some potential for exploits down the road. This way you can;t access it until you get past the virtualhost password we set up earlier. Head over to [PHPMyAdmin](https://www.phpmyadmin.net/) and clone the current version into the /var/www directory; > sudo wget https://files.phpmyadmin.net/phpMyAdmin/\[Version\]/phpMyAdmin-\[Version\]-all-languages.zip

Unzip it; > sudo unzip phpMyAdmin-\[Version\]-all-languages.zip

PHPMyAdmin It will prompt you for a blowfish secret. Navigate to its directory and copy the sample config file; > sudo cp config.sample.inc.php config.inc.php

Open the new file and look for this line... > $cfg\['blowfish\_secret'\] = '';

I wrote a tool which comes up with a perfectly sized high-entropy string to put here. [Check it out](https://password-generator.cjtrowbridge.com/). Once that is entered, navigate to the sql/ directory within the PHPMyAdmin folder and run this to set the tables up. It will prompt you for the password you set up earlier; > sudo mysql -u root -p &lt; create\_tables.sql

## I Made This Simple Stats Tool

[VPS-Home](https://github.com/cjtrowbridge/vps-home/) is a simple tool I made some time ago which shows a few important things. It shows the free space on the disk, the disk utilization for each directory within /var/www and the top running processes at the moment, along with the runtime and motd. Install it by simply downloading it into the virtualhost we made; > sudo wget https://raw.githubusercontent.com/cjtrowbridge/vps-home/master/index.php

## Connect to MSSQL

We installed FreeTDS which allows for tabular data-stream connections to Microsoft SQL Server from PHP5. Test it with this command; > tsql -H \[host/ip\] -p \[port\] -U \[username\] -P \[password\] -D \[database\]

You should see something like this; > locale is "en\_US.UTF-8" locale charset is "UTF-8" using default charset "UTF-8" Default database being set to \[database\] 1&gt;

If you see something about "Unable to connect: Adaptive Server is unavailable or does not exist" that is ok too. Edit /etc/freetds/freetds.conf and add this to the end; > \[nickname\] host = \[host/ip\] port = \[port\] tds version = 7.0

Your version may vary. For MS SQL Server 2008, this was the version I used. **Now you can use mssql\_query() in PHP5**

**to build server applications with Microsoft SQL Server!**