---
id: 6935
title: 'VPS Setup: Recommended Initial Installations'
date: '2016-02-21T12:29:51-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6935'
permalink: /2016/02/21/vps-setup-recommended-initial-installations/
categories:
    - Projects
    - 'Tech 2U'
---

This is a subpost of the larger post [Updated Comprehensive VPS Setup Documentation](https://blog.cjtrowbridge.com/2016/02/21/updated-comprehensive-vps-setup-documentation/). When initially setting up a VPS, I generally install the programs listed below. Before installing anything, it is important to first update and upgrade all packages already installed on the server with `apt-get update && apt-get upgrade`

1. First, install Fail2Ban in order to prevent bruteforcing of SSH passwords
2. Install Apache2
3. Install MySQL Server
4. Install PHP and its dependencies for MySQL and PHPMyAdmin
5. Performance Tools 
    1. Screenfetch lets you see system information
    2. Htop lets you see details about resource usage
    3. Nload lets you see details about network utilization
6. NTP makes sure the time is kept up to date
7. Git tracks changes in files and is required for LetsEncrypt

This command will do all of these things without prompting in between; `apt-get -y install fail2ban apache2 && apt-get -y install mysql-server && apt-get -y install php5 php-pear php5-mysql && apt-get -y install php5-mcrypt && php5enmod mcrypt && a2enmod rewrite && apt-get -y install php5-curl && service apache2 restart && mysql_secure_installation && apt-get -y install phpmyadmin && apt-get -y install screenfetch htop nload curl git ntp`You will be prompted to create a MySQL root password. PHPMyAdmin setup will ask you for this password, as will the MySQL Secure Installation tool.