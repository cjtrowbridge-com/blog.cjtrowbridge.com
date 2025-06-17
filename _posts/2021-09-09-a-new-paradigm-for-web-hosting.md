---
id: 14282
title: 'A New Paradigm For Web Hosting'
date: '2021-09-09T17:24:19-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=14282'
permalink: /2021/09/09/a-new-paradigm-for-web-hosting/
categories:
    - Our-Space
    - Projects
---

I host dozens of wordpress sites for lots of different projects I am either actively working on or worked on in the past, or where I'm just helping others have a website for projects they're working on.

## The Problems

Serving a lot of wordpress installs can take a lot of resources, but most of these sites rarely changes, particularly for my past projects. This makes it very tempting to just save the whole site as static html and serve that. The advantage there is that I don't need to run a production database for that site, I don't need to worry about constantly patching and updating the wordpress install, etc, etc. So serving static html is super ideal but also it makes it harder to do updates. I run a daily backup of all my virtualhosts, thei wwwroot directory, and their corresponding database. These all go automatically to my nas. So it's easy for me to load them into a new server if there is ever a problem. I simply run the SQL export, load the virtualhost, and unpack the wwwroot archive, and then I have a carbon copy of the wordpress install ready to go from the night before. Another problem is the fact that I've been using half a dozen vpses in order to get different ip addresses for seo. I would really like to move some of these to ipv6 so that I can get the benefits of multi-server seo without having to pay for multiple servers. Lastly, it is very important to me to move to a distributed static ipfs model, and this project is largely a first step in that direction which also solves the other problems I have mentioned. ## Past Attempts

In the past, I've tried several ways of serving static versions of the wordpress sites. One way was to move all my wordpress installs to administrative subdomains, and then use a [recursive wget](https://www.linuxjournal.com/content/downloading-entire-web-site-wget) on a cron job to save the whole website as static html and write that to a production directory where it can be served as the main site. This worked well for dramatically improving resource consumption from normal user requests, but it made the infrastructure a lot more complicated because I'm still running all those databases and I still need to patch everything constantly. It also meant that I have to recursively download the entire site every time I want to update anything. This is fine for small simple sites but my blog has tens of thousands of files, so that becomes a huge resource drain that takes a really long time on a cloud vps, whenever I want to update anything. And it's running on the same production vps which negatively impacts user requests. ## New Idea

So I came up with a new strategy. I want to build a simple vm on my laptop which I can use for updates, and then have it save the new static files locally, before pushing any updates to the production vps in the cloud. This would really shrink down my cloud resources consumption by moving most of the hard work to my development machine and freeing up lots of resources in the cloud. ## Building the Dev VM

I'm going with Debian 11 in VirtualBox on my 2020 Razer Stealth 13. This laptop has a 2TB WD Black NVMe SSD, 16GB RAM, and an 8-thread, 4-core i7 at 3.9ghz. This machine has vastly more resources that an affordable cloud vm has, so it makes a lot of sense to move the work here. These setup notes are mostly for my own future reference; #### First Set Up The Basics

After you install Debian 11, log in as root and install sudo, then run visudo and add yourself. Next log in as yourself. Install [Guest Additions](https://kifarunix.com/install-virtualbox-guest-additions-on-debian-11/). sudo systemctl enable ssh Now log in via putty or something like that. apt-get install fail2ban apache2 #### Now set up secure transport so we can install PHP.

sudo apt-get install lsb-release apt-transport-https ca-certificates sudo wget -O /etc/apt/trusted.gpg.d/php.gpg https://packages.sury.org/php/apt.gpg sudo echo "deb https://packages.sury.org/php/ $(lsb\_release -sc) main" | sudo tee /etc/apt/sources.list.d/php.list sudo apt-update #### Now [install php 8](https://kifarunix.com/install-php-8-on-debian-11/);

sudo apt-get install php8.0 php8.0-{bcmath,bz2,intl,gd,mbstring,mysql,zip,xml,curl,sqlite3} Disable deafult virtualhost and remove default webroot directory sudo a2dissite \* &amp;&amp; sudo service apache2 restart sudo rm -rf /var/www/html #### [Install LetsEncrypt for free SSL.](https://certbot.eff.org/lets-encrypt/debianbuster-apache.html)

Unfortunately they made this a lot more complicated so first you have to install their preferred package manager. sudo apt install snapd sudo snap install core; sudo snap refresh core sudo snap install --classic certbot sudo ln -s /snap/bin/certbot /usr/bin/certbot sudo certbot --apache #### Set Up MySQL Database Server

First you have to [install the repository](https://kifarunix.com/install-mysql-8-on-debian-11/); sudo wget https://repo.mysql.com//mysql-apt-config\_0.8.18-1\_all.deb sudo apt install ./mysql-apt-config\_0.8.18-1\_all.deb -y Now update the repositories and install mysql-server; sudo apt update &amp;&amp; sudo apt install mysql-server sudo mysql\_secure\_installation Configuring mysql server is a nightmare. I like to reduce the max connections to 25 so that the server doesn't consume too much resources. Edit the file /etc/mysql/my.cnf and add the following lines to the end; \[mysqld\] max\_connections = 25 ## Overview: Step One

My long-term plan is to use IPFS to distribute the files from the development server to the production server(s). But first I want to get everything working in a simpler way using BTSync. This is a very similar distribution paradigm but a lot of the hard parts of the work are abstracted away. The process is to make changes in wordpress on the development server, update the local static copy, and then BTSync will mirror those changes onto the production servers automatically in real time. ## Overview: Step Two

The goal state would be a simple system of round-robin dns which allows several cloud servers to handle serving all the static sites. Then IPFS rapidly pushes any updates from the dev server to those cloud servers. The process here is to make changes in wordpress on the development server, update the local static copy, publish the changes to IPFS, and update the DNSLink record. The production servers will listen for the updated DNSLink record, and then download the updated files automatically. Ideally this process will eventually happen over tor. Hopefully you can see where I'm going here. I am trying to incrementally move towards the ideal [our-space model](https://blog.cjtrowbridge.com/2021/05/12/ourspace-distributed-serverless-anti-hierarchical-social-media/) by taking incremental steps to change my current content distribution model to be more like our-space. This way, a future our-space app can replicate this model by simply including any content management system and then pushing the content out through ipfs over tor and updating its public address. ## Step One: BTSync Distribution

## [Install BTSync](https://github.com/tuxpoldo/btsync-deb)

This used to be less complicated but the old way doesn't work anymore. sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 992A3C9A3C3DE741 sudo echo "deb http://deb.silvenga.com/btsync any main" &gt;&gt; /etc/apt/sources.list apt-get update apt-get install btsync Not too bad, right? You will have to change the ownership of the /var/www directory to allow btsync to pull files from there; sudo chown btsync:www-data /var/www ## Install PHPMyAdmin

Navigate to your webroot cd /var/www Download pma (Get the most recent link from phpmyadmin.net) wget https://files.phpmyadmin.net/phpMyAdmin/5.1.1/phpMyAdmin-5.1.1-all-languages.zip unzip php\*.zip rm php\*.zip mv php\* pma ## Modify Virtualhost

sudo nano /etc/apache2/sites-available/000-default.conf Change the DocumentRoot to /var/www Add the following block of text at the end of the file. > &lt;Directorymatch "^/.\*/\\.git/"&gt; Order deny,allow Deny from all &lt;/Directorymatch&gt; &lt;Directory /var/www/webs/&gt; Options FollowSymLinks AllowOverride All Require all granted &lt;/Directory&gt;

Now save that file and restart apache. sudo service apache2 restart 