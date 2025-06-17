---
id: 8860
title: 'Perfect Server, Version 18'
date: '2017-08-05T00:02:00-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8860'
permalink: /2017/08/05/perfect-server-version-18/
categories:
    - Projects
---

This is the latest iteration of my perfect server. I am building this in order to consolidate and deprecate previous server inventory. Also, it includes many new best-practices which should further secure this new server. The first step is to provision a new server. I use digital ocean. I will be logged in as root for all of this since this is all stuff that needs to be done as root. If you don't want to log in as root, you can instead use sudo at the beginning of each command. Now, add some sources to the package manager. Get there with;

> nano /etc/apt/sources.list

Add these repositories; > deb http://ftp.debian.org/debian jessie-backports main deb http://packages.dotdeb.org jessie all

We also need to add the GPG keys so the new repositories will work. Run these commands; > wget https://www.dotdeb.org/dotdeb.gpg sudo apt-key add dotdeb.gpg

Update the package manager and upgrade any packages that are available; > apt-get update &amp;&amp; apt-get upgrade

Now install all the packages we will need; > apt-get -y install fail2ban apache2 php7.0 php-pear php7.0-mysql php7.0-mcrypt php7.0-mbstring libapache2-mod-php7.0 php7.0-curl screenfetch htop nload curl git unzip ntp mcrypt postfix mailutils php7.0-memcached mysql-server &amp;&amp; apt-get install python-certbot-apache -t jessie-backports &amp;&amp; a2enmod rewrite &amp;&amp; service apache2 restart &amp;&amp; mysql\_secure\_installation

You will be prompted to create a mysql password which you will then immediately be asked for when configuring mysql server securely. ## Name Thyself

Now navigate to the virtualhost directory; > cd /etc/apache2/sites-available

Remove the default ssl virtualhost. We will be creating a new one instead. > rm default-ssl.conf

Rename the default virtualhost to the fqdn of the server. Example: server3.website.com. Note that this is not the fqdn of the site(s) we are hosting on the server. > mv 000-default.conf \[fqdn\].conf

Edit the file and replace the admin email with your own. Change the DocumentRoot to /var/www instead of /var/www/html. Now add the following block within the virtualhost tag of the file and save it. > &lt;Directory "/var/www"&gt; AuthType Basic AuthName "Restricted Content" AuthUserFile /etc/apache2/.htpasswd Require valid-user &lt;/Directory&gt;

### Lock it Down

Let's create a credential set for our new virtualhost. This is sort of a catch-all for any domains we point here which are not yet set up. > htpasswd -c /etc/apache2/.htpasswd <span class="highlight">\[username\]</span>

You will be prompted for a password. This is very bruteforceable. My best practice is to use a very high entropy strings for both the username and the password. Typically at least 64 bits of random base 64 for each. ### Apply Changes

We need to tell apache that we have changed the name of the default virtualhost file. First we disable the one we changed, and then enable our new one. > a2dissite 000-default a2ensite \[fqdn\]

Now restart apache > service apache2 restart

Test our changes by navigating to the fdqn of the server. You should be prompted for a username and password. ### Administrative Tools

We will need to put some tools in here so we can administer the server. #### PHPMyAdmin

This will allow us to manage the databases we will be creating on the server. Head over to their website and get the download link for the current version. Navigate to our new secure DocumentRoot directory and download that link. > cd /var/www &amp;&amp; wget \[link\]

Now unzip it and remove the zip file we downloaded. > unzip \[file\] &amp;&amp; rm \[file\]

Now that we have a PHPMyAdmin directory in our secure virtualhost, we need to configure it. Luckily it can do that itself! Use this command and enter the mysql root password when prompted. > mysql -uroot -p &lt; /\[unzipped phpmyadmin folder\]/sql/create\_tables.sql

The last thing PHPMyAdmin needs is a secret string. Edit the config file config.sample.inc.php and save it as nano config.inc.php. Make sure to add a random string where prompted at the top of the file. #### Postfix Outbound-Mail Server

We need to edit the config files for postfix and change the interface to loopback-only like so. We already set up a firewall rule to block connections to port 25, but those rules can be changed by mistake, so this will be a good second line of defense to prevent public access to sending mail through our server, while allowing us to still use it locally. > nano /etc/postfix/main.cf

Find this line; > inet\_interfaces = all

And change to; > inet\_interfaces = 127.0.0.1

Now edit the email aliases; > nano /etc/aliases

At the end of the file, make sure there is a line that starts with root and ends with your email, like so; > root: email@domain.com

Save the file and exit. Then run newaliases to let Postfix apply the changes. Restarting Postfix is not enough because we changed the interfaces line in the config file. We need to stop and start it like so; > newaliases &amp;&amp; postfix stop &amp;&amp; postfix start

Now our sites will be able to send emails! #### VPS Home

This is something simple I built which serves as a better index page for the secure virtual host and includes several helpful tools for diagnostic purposes. To try it out, run this command from the DocumentRoot directory. > wget https://raw.githubusercontent.com/cjtrowbridge/vps-home/master/index.php

#### PHPInfo

It's helpful to be able to access details of the server's php installation from this directory. I like to create a file called phpinfo.php which contains simply > &lt;?php phpinfo();

#### Automatic Backups

Create a new file called /root/backup.sh and add the following to it. Make sure to replace the mysql password with yours. > \#!/bin/bash #deletes old backups find /var/www/backups/ -mindepth 1 -mmin +$((60\*24)) -delete #creates new backups tar -cf "/var/www/backups/webs-$( date +'%Y-%m-%d\_%H-%M-%S' ).gz" /var/www/webs /usr/bin/mysqldump -uroot -p\[mysql root password\] --all-databases | gzip &gt; "/var/www/backups/mysql-$( date +'%Y-%m-%d\_%H-%M-%S' ).sql.gz"

Now edit the crontab with nano /etc/crontab and add this line. This will automatically run that script every day at 8pm. > 0 20 \* \* \* root /root/backup.sh &gt; /dev/null 2&gt;&amp;1

Make sure to give the script permission to execute. > chmod 775 /root/backup.sh

#### Offsite Backups

Now that we have regular backups going, we need to regularly get them off the server. I like Bittorrent Sync for this. It is very fast and seamless. Run these commands to install Bittorrent Sync; > sh -c "$(curl -fsSL http://debian.yeasoft.net/add-btsync14-repository.sh)" apt-get update &amp;&amp; apt-get install btsync

I recommend selecting the user and group www-data for btsync as this will greatly simplify administration and file permissions. Then navigate the the port you set up during the installation process and create credentials. As always, be sure to use very high entropy credentials. Then create a shared folder for the backups, and copy the read-write key to your nas to securely copy the backups every day. The really great thing about this approach is that when your cron job deletes the backups every day on the server, Bittorrent Sync will archive them on your nas so that they are always available. This means that at any point, you can simply take the automatically generated gz of your webs and mysql, and recreate your entire server in minutes. ## Migrating Sites In

Move over the files for all the sites you want to host into individual directories in the /var/www/webs directory. Now navigate to your virtualhosts directory. > cd /etc/apache2/sites-available

We created a default virtualhost file for the server and named it \[fqdn\].conf. This was the fqdn of the server, but not the sites it will host. Now we want to create our first hosted site. Copy the default file we made to create a new virtualhost like so... > cp \[server fqdn\].conf \[site fqdn\].conf

You can use any naming convention you like, but managing dozens or hundreds of these will become impossible if you are not naming them clearly. Next, we need to add some new things to this hosted site fqdn. Add a new line inside the virtualhost tag like this; > ServerName \[site fqdn\]

And change the line which has DocumentRoot to point to the directory for this hosted site. For example; > DocumentRoot /var/www/webs/\[site fqdn\]

Lastly add these two blocks at the end of the file. > &lt;Directorymatch "^/.\*/\\.git/"&gt; Order deny,allow Deny from all &lt;/Directorymatch&gt; &lt;Directory /var/www/webs/\[site fqdn\]&gt; Options FollowSymLinks AllowOverride All Require all granted &lt;/Directory&gt;

The first block will prevent anyone from navigating into a git repository and accessing sensitive data like credentials or from cloning the repository. The second block will allow htaccess files or directory rewrites, and prevent directory listing. These are required changes if you want to host Wordpress sites, and best practices all around. Now we just need to enable these changes and make the site live with; > a2ensite \[site fqdn\] &amp;&amp; service apache2 restart

From this point on, this new virtualhost can be copied to create new sites, rather than recreating each one from the original virtualhost file. ## Free SSL

We already set up LetsEncrypt so now we just need to run it. Once the domains are set up and pointed to the server's ip, along with a virtualhost being configured, all it takes is running certbot which takes care of everything. > certbot