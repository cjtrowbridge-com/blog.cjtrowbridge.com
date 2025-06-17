---
id: 7908
title: 'Installing PHP 7 on a Debian Server'
date: '2016-12-20T16:14:14-08:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=7908'
permalink: /2016/12/20/installing-php-7-on-a-debian-server/
categories:
    - Blog
---

PHP 7 has reached the level of maturity where I want to start moving my development and production environments over to it. Setup is a little more complicated than with previous versions, so the purpose of this post is to journal for myself on how I did it, as well as to help others who may need help doing this. I am using Digital Ocean ([Referral Link](https://m.do.co/c/ecb56e953504)) to host this VPS. First, I create a new Debian server and update their default apt sources...

```
nano /etc/apt/sources.list
```

Make sure all of these are there; ```
deb http://httpredir.debian.org/debian jessie main contrib non-free
deb-src http://httpredir.debian.org/debian jessie main contrib non-free

deb http://httpredir.debian.org/debian jessie-updates main contrib non-free
deb-src http://httpredir.debian.org/debian jessie-updates main contrib non-free

deb http://security.debian.org/ jessie/updates main contrib non-free
deb-src http://security.debian.org/ jessie/updates main contrib non-free

deb http://packages.dotdeb.org jessie all

deb http://ftp.debian.org/debian jessie-backports main
```

Add the key for DotDeb so we can install their packages... ```
wget https://www.dotdeb.org/dotdeb.gpg && apt-key add dotdeb.gpg
```

Next, update the package manager and upgrade any installed packages; ```
apt-get update && apt-get upgrade
```

Now let's block smtp so people can't use our server to send emails... ```
iptables -A INPUT -i eth0 -j REJECT -p tcp --dport 25
```

Now let's install all the packages we will need; ```
apt-get -y install fail2ban apache2 && apt-get install php7.0 php-pear php7.0-mysql php7.0-mcrypt php7.0-mbstring libapache2-mod-php7.0 php7.0-curl screenfetch htop nload curl git ntp mcrypt postfix mailutils php7.0-memcached mysql-server && apt-get install python-certbot-apache -t jessie-backports && a2enmod rewrite && service apache2 restart && mysql_secure_installation
```

## PHPMyAdmin

I like to use PHPMyAdmin to administer my databases. At the time of this post, this is still a little jank to install from the package manager, and I could not get it working that way. The version it installs is trying to run in PHP5. My recommendation is to setup a secure Apache Virtualhost with a high-entropy password and download the PMA directory into there. This will not receive important security updates because it is not installed through the package manager, but it will be protected from access by the secure Virtualhost. I hesitate to give [instruction](https://www.digitalocean.com/community/tutorials/how-to-set-up-password-authentication-with-apache-on-ubuntu-16-04) on how to do this, because it is not an ideal solution, and once the setup process is more streamlined with PHP 7, I will certainly go back to installing it through the package manager. ## Setup Postfix Mail Server

Now edit the config files and change the interface to loopback-only like so. We already set up a firewall rule to block connections to port 25, but those rules can be changed by mistake, so this will be a good second line of defense to prevent public access to sending mail through our server, while allowing us to still use it locally. ```
nano /etc/postfix/main.cf
```

Find this line; ```
inet_interfaces = all
```

And change to; ```
inet_interfaces = 127.0.0.1
```

Now edit the email aliases; ```
nano /etc/aliases
```

At the end of the file, make sure there is a line that starts with root and ends with your email, like so; ```
root: email@domain.com
```

Save the file and exit. Then run newaliases to let Postfix apply the changes. ```
newaliases
```

Restarting Postfix is not enough because we changed the interfaces line in the config file. We need to stop and start it like so; ```
postfix stop
postfix start
```

## Creating a VirtualHost

First, we need to forward an A-Record from our DNS provider over to the public IP of our new server. Then, create a directory for our new FQDN. ```
mkdir /var/www/[fqdn]/
```

Create a new VirtualHost for our new FQDN. ```
cp /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/[fqdn].conf
```

Edit the virtual host and make sure it has all of this; ```
nano /etc/apache2/sites-available/[fqdn].conf
```

```
ServerName [fqdn]

ServerAdmin your_email@website.com
DocumentRoot /var/www/[fqdn]/

ErrorLog ${APACHE_LOG_DIR}/error.log
CustomLog ${APACHE_LOG_DIR}/access.log combined
```

## Using LetsEncrypt for Free SSL

We already added the repository we need, and we installed the Certbot to take care of our certificates, so now let's run Certbot to setup SSL. ```
certbot --apache
```

## Automated Backups

Create a directory in which to generate the backups. ```
mkdir /var/backups/[fqdn]
```

Add the following to crontab; ```
nano /etc/crontab
```

```
0 22 * * * root tar -cf /var/backups/[fqdn]/www-backup-$( date +'\%Y-\%m-\%d_\%H-\%M-\%S' ).gz /var/www/[fqdn]
find "/var/www/backups/[fqdn]" -type f -name "*.gz" -mtime +6 -delete
```

This will create a new backup of the document root each night, and delete any backups older than a week. These should automatically be moved to another device each day. I am partial to using BitTorrent Sync to do this, but there are any number of good solutions to this problem. Finding the best solution depends on your setup.