---
id: 12293
title: 'Web Application Server Setup 2020'
date: '2020-04-18T18:29:40-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=12293'
permalink: /2020/04/18/web-application-server-setup-2020/
categories:
    - Projects
---

After apportioning the server, and creating a DNS entry with your registrar for the FQDN, connect via SSH. Now update the server

```
apt-get update && apt-get upgrade
```

First let's install fail2ban to prevent repeated login attempts ```
apt-get install fail2ban
```

## Install Apache 2, PHP 7.4, and SSL

Next install Apache ```
apt-get install apache2
```

Get ready to install php 7.4 by enabling encrypted transport, adding the repository, adding the key, and then updating the lists. ```
apt-get install lsb-release apt-transport-https ca-certificates
wget -O /etc/apt/trusted.gpg.d/php.gpg https://packages.sury.org/php/apt.gpg
echo "deb https://packages.sury.org/php/ $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/php.list
apt-get update
```

Now install PHP 7.4 plus the common modules ```
apt-get install php7.4 php7.4-{bcmath,bz2,curl,intl,gd,mbstring,mysql,zip}
```

Disable the default virtualhosts and delete the junk in the default webroot ```
a2dissite * && service apache2 restart
rm -rf /var/www/html
```

Create new virtualhosts and then enable them. Make sure to ```
cd /etc/apache2/sites-available && cp 000-default.conf [FQDN].conf
[update virtualhost with your fqdn if you're going to be hosting multiple sites on this server]
a2ensite [FQDN].conf
service apache2 restart
```

Install certbot for free SSL from LetsEncrypt ```
apt-get install certbot python-certbot-apache man-db
```

Install some various helpful utilities ```
apt-get install nload curl htop git unzip ntp mcrypt
```

Activate SSL for your FQDN ```
certbot –authenticator webroot –installer apache
```

## Set Up MySQL Database Server

Get ready to install MySQL Server by configuring the package tool ```
cd /tmp
wget https://dev.mysql.com/get/mysql-apt-config_0.8.13-1_all.deb
dpkg -i mysql-apt-config*
```

Now install MySQL Server ```
apt update
apt install mysql-server
```

Run the MySQL Secure Installation tool to lock down your server ```
mysql_secure_installation
```

One last thing. The default configuration of MySQL is really not ideal and it is not a smart application which learns how to manage its resources. It needs to be told what to do. It's been said that the default configuration really doesn't work for anyone. In particular, MySQL creates threads for all its potential connections, and all of those threads have the same set resource usage. If your server can handle five connections then it has five threads, and so on. Well the default settings have 151 threads, and all of them are trying to use 1.3gb. This is terrible; MySQL simply hogs all available resources until other services start to crash and the server doesn't work. I decided to set it to 25 threads rather than tweak the resource limits of each thread. The resource limits are very complicated and granular and the implications of changing these things is a whole field in itself. There are people who spend their entire lives and careers trying to understand the implications of mysql resource limit variables. I am by no means an expert. I fully expect to have to make tweaks and changes as future problems come up. With all those caveats in mind, here is what I did... Edit the file /etc/mysql/my.cnf Add the following lines at the end ```
[mysqld]
max_connections = 25
```

Suddenly my resource usage goes from maxing out the vps to just a few hundred megabytes, with no noticeable change in performance. Depending on your application this could be different. I encourage you to research further before changing these variables, and before leaving them at defaults.