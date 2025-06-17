---
id: 8030
title: 'Building a Debian Application Server with PHP 7 + MySQL 5.7 + MS SQL'
date: '2017-01-29T11:01:39-08:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8030'
permalink: /2017/01/29/building-a-debian-server-php-7-mysql-5-7-ms-sql/
categories:
    - Projects
    - 'Tech 2U'
---

One of the applications I am building integrates with a legacy software platform including MS SQL Server. In past versions of PHP, there was a simple and free tool called FreeTDS which enabled PHP to connect to MS SQL Server, but this has been deprecated as of PHP 7. In order to get all the new features, performance increases, and security improvements that come with PHP 7, we need to find an alternative to FreeTDS. Oddly enough, Microsoft has released an official replacement! :D First, I created a droplet with Digital Ocean ([Referral Link](https://m.do.co/c/ecb56e953504)) and give it 1GB RAM. Now, the default apt list needs to be expanded;

```
nano /etc/apt/sources.list
```

Add these sources... ```
deb http://httpredir.debian.org/debian jessie main contrib non-free
deb-src http://httpredir.debian.org/debian jessie main contrib non-free

deb http://httpredir.debian.org/debian jessie-updates main contrib non-free
deb-src http://httpredir.debian.org/debian jessie-updates main contrib non-free

deb http://ftp.debian.org/debian jessie-backports main

deb http://repo.mysql.com/apt/debian/ jessie mysql-apt-config
deb http://repo.mysql.com/apt/debian/ jessie mysql-5.7
deb http://repo.mysql.com/apt/debian/ jessie mysql-tools
deb-src http://repo.mysql.com/apt/debian/ jessie mysql-5.7

deb http://packages.dotdeb.org jessie all
deb-src http://packages.dotdeb.org jessie all
```

Now lets install the GPG key for DotDeb and MySQL so we can install their packages... ```
wget https://www.dotdeb.org/dotdeb.gpg && apt-key add dotdeb.gpg &&
gpg --keyserver pgpkeys.mit.edu --recv-key  8C718D3B5072E1F5 &&
gpg -a --export 8C718D3B5072E1F5 | apt-key add -
```

Update our sources and run any available upgrades; ```
apt-get update && apt-get upgrade
```

Add a firewall rule to prevent unwanted sending of outbound mail. ```
iptables -A INPUT -i eth0 -j REJECT -p tcp --dport 25
```

Now run this command to install PHP7 and MySQL 5.7; ```
apt-get -y install fail2ban apache2 && apt-get install php7.0 php7.0-fpm php-pear php7.0-dev php7.0-mysql mcrypt php7.0-mcrypt php-mbstring php7.0-mbstring libapache2-mod-php7.0 php7.0-curl php7.0-xml screenfetch htop nload curl git unzip ntp mcrypt postfix mailutils php7.0-memcached mysql-server apt-transport-https && apt-get install python-certbot-apache -t jessie-backports && a2enmod rewrite && service apache2 restart && mysql_secure_installation
```

You will be prompted to create a new root password for the mysql installation, and then give that password to mysql\_secure\_installation so it can run. ## Setup Postfix Mail Server

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

Save the file and exit. Then run newaliases to let Postfix apply the changes. Restarting Postfix is not enough because we changed the interfaces line in the config file. We need to stop and start it like so; ```
newaliases && postfix stop && postfix start
```

## Creating Two VirtualHosts

First, we need to forward an A-Record from our DNS provider over to the public IP of our new server. We will need to do the following steps twice: once for the fqdn of the machine, and once for the fqdn of the application we are serving. I like to set the machine's virtualhost to use /var/www and then put the other virtualhosts in directories inside there, to make them easy to access. First disable the default VirtualHost. ```
a2dissite 000-default.conf
```

Create a directory for our new FQDN. ```
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

Now enable the virtualhost and restart apache. ```
a2ensite [fqdn] && service apache2 restart
```

## Securing the Machine's FQDN VirtualHost

Create a password file for the VirtualHost. Pick a high entropy username and password. ```
htpasswd -c /etc/apache2/.htpasswd [username]
```

Now add this to the VirtualHost for the machine's FQDN. ```
<Directory "/var/www/">
      <span class="highlight">AuthType Basic</span>
      <span class="highlight">AuthName "Restricted Content"</span>
      <span class="highlight">AuthUserFile /etc/apache2/.htpasswd</span>
      <span class="highlight">Require valid-user</span>
  </Directory>
```

Restart Apache to make the changes take effect. ```
service apache2 restart
```

## PHPMyAdmin

Navigate to the machine's webroot. ```
cd /var/www/[FQDN]
```

Download PHPMyAdmimn. ```
wget https://files.phpmyadmin.net/phpMyAdmin/[version]/phpMyAdmin-[version]-all-languages.zip
```

Unzip it into a new directory in the current directory. ```
unzip phpMyAdmin-[version]-all-languages.zip -d .
```

## Troubleshooting

For basic troubleshooting and performance monitoring, I wrote a simple tool to see the output of a few simple cli tools. It also includes a directory listing. So it's essentially just a better index file for the vps. Try it out if you like. ```
wget https://raw.githubusercontent.com/cjtrowbridge/vps-home/master/index.php
```

## Using LetsEncrypt for Free SSL

We already added the repository we need, and we installed the Certbot to take care of our certificates, so now let's run Certbot to setup SSL for our VirtualHosts. ```
certbot --apache
```

## Installing MS SQL For PHP

First install the tools. ```
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install msodbcsql mssql-tools unixodbc-dev
```

Then install the drivers ```
pecl install sqlsrv
pecl install pdo_sqlsrv
```

Add the newly installed tools into the PHP configuration file. ```
echo "extension=/usr/lib/php/20151012/sqlsrv.so" >> /etc/php/7.0/apache2/php.ini
echo "extension=/usr/lib/php/20151012/pdo_sqlsrv.so" >> /etc/php/7.0/apache2/php.ini
echo "extension=/usr/lib/php/20151012/sqlsrv.so" >> /etc/php/7.0/cli/php.ini
echo "extension=/usr/lib/php/20151012/pdo_sqlsrv.so" >> /etc/php/7.0/cli/php.ini
```

Restart Apache and you're ready to go! ```
service apache2 restart
```