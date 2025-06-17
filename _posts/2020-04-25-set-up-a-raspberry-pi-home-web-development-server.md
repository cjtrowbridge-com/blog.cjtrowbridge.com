---
id: 12302
title: 'Set Up A Raspberry Pi Home Web Development Server'
date: '2020-04-25T20:30:45-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=12302'
permalink: /2020/04/25/set-up-a-raspberry-pi-home-web-development-server/
categories:
    - Projects
---

# Initial Setup

First download the latest full version of raspbian. Next, use win32diskimager to write it to your sd card. #### \[Optional\] Headless Setup

This step means we will be able to just turn on the pi and SSH into it, without hooking up a screen, keyboard, and mouse. Then create a blank file called "ssh" (no extension) in the boot directory on the SD card. Lastly, create a file called "wpa\_supplicant.conf" in the boot directory of the SD card. Paste the following into that file, substituting your own SSID and password; > country=US ctrl\_interface=DIR=/var/run/wpa\_supplicant GROUP=netdev update\_config=1 network={ ssid="SSID" psk="PASSWORD" }

## First Run

Now power up the pi, wait a few minutes, then use something like ssh (linux), putty (pc), or bonjour (mac) to SSH into the pi at hostname "raspberrypi." Run the configuration command; > sudo raspi-config

Update the password. This will be your password for all the services we're using, so make it a good one. Update locale. Update timezone. Expand the filesystem. Enable vnc. \[Optional but very helpful.\] When you're done with all this, exit the configuration tool and reboot before continuing. ## Update Everything

First, enable nonfree and contrib sources by opening this file and uncommenting the last line; > sudo nano /etc/apt/sources.list

Now update the sources and run the package updater > sudo apt-get update &amp;&amp; sudo apt-get upgrade &amp;&amp; sudo apt-get dist-upgrade

There will probably be a lot of things to upgrade the first time. Let that all go ahead. ## Okay Ready To Get Started Now

At this point, we have a blank raspberry pi fully updated and configured and ready to start using. Installing fail2ban is important for preventing bruteforce attacks, even on a local network since we're in the age of IoT attacks. > sudo apt-get install fail2ban

This installs a few tools I like to use for basic diagnostics and troubleshooting. Normally, I would also install htop, git, curl, ntp, and unzip but these come pre-installed in raspbian. > sudo apt-get install nload screenfetch mcrypt curl

Install apache2 to handle web requests > sudo apt-get install apache2

There are a lot of issues with permissions and ownership that come up with application servers like this. It can be really complicated to deal with all that, and so over the years I have developed a simple script which fixes everything that gets messed up with ownership and permission of program files and directories in this kind of situation. If you don't want to figure all that out on your own, use my script! > cd ~/ &amp;&amp; wget https://raw.githubusercontent.com/cjtrowbridge/Web-App-Server-Permissions-Fixer/master/permissions\_fixer.sh &amp;&amp; sudo chmod +x fix\_permissions.sh

Simply call the script from anywhere to fix whatever permissions and ownership issues you may be having by running the script; > sudo ~/fix\_permissions.sh

## Server Languages

Raspbian comes with lots of server languages pre-installed, such as NodeJS, Python, etc. But I also like to develop in PHP when I feel like taking a sledgehammer to the problem instead of a scalpel. At the time of writing, PHP 7.3 is the most current implementation available in the mainline raspbian repos. This command also installs many dependencies for basic functionality including support for MySQL, Postgres, and SQLite3 databases. This is probably not all absolutely necessary, but it doesn't hurt anything to include the functionality in case you want it later, especially if this is going to be a dev machine. > sudo apt-get install php7.3 php7.3-{bcmath,bz2,intl,gd,mbstring,mysql,zip,pgsql,sqlite3,curl}

If you want to add SSL for machines outside your network, [check the instructions here](https://blog.cjtrowbridge.com/2020/04/18/web-application-server-setup-2020/). If the machine is only going to be accessed locally, then normal SSL won't work since it only works for fully qualified domain names. We will instead need to create a self-signed SSL certificate. This is an easy process, but it means that you will always have to click to accept the risk of using a self-signed certificate when initially navigating to your dev server. Run this command to create the self-signed ssl certificate. > sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/apache-selfsigned.key -out /etc/ssl/certs/apache-selfsigned.crt

It will ask you a lot of questions that you don't really need to answer. Next, add these lines inside the inner tag in the default ssl virtualhost file at /etc/apache2/sites-available/default-ssl.conf > SSLEngine on SSLCertificateFile /etc/ssl/certs/apache-selfsigned.crt SSLCertificateKeyFile /etc/ssl/private/apache-selfsigned.key

Then run this command to enable ssl in apache. > sudo a2ensite default-ssl.conf &amp;&amp; sudo service apache2 restart

## Databases

#### MySQL/ MariaDB

MySQL is not officially supported for Raspbian. Instead of MySQL, let's use MariaDB which works exactly the same way and was developed as a free alternative to MySQL by the person who developed MySQL after he sold the MySQL project. 🤣 At the time of writing this, 10.3 is the current version. You can check what is the most recent version available in the package manager by typing out the command except for the version number and then hit tab to see a list of completion options. Or you can do the hard work of adding random people's repositories to get more recent versions which you will than have to figure out how to update. 🤷‍♀️ > sudo apt-get install mariadb-server-10.3

Now run the secure setup command. (I know it's weird that it says mysql) > sudo mysql\_secure\_installation

You will be prompted to create a root password. I recommend choosing all the most secure settings. Now navigate to your webroot directory and download the current version of phpmyadmin. > cd /var/www/html &amp;&amp; wget \[Whatever the current PMA URL is\]

Unzip the file and then delete it. > sudo unzip \[file\] &amp;&amp; rm \[file\]

Navigate into the setup directory and execute the setup query. > cd \[pma\]/setup &amp;&amp; sudo mysql -uroot -p &lt; create\_tables.sql

You will be prompted for that root MariaDB password. You may notice that even the commands for MariaDB are the same as MySQL. It really is directly interchangeable and substantially better plus free. Just treat it like MySQL. Next you will need to give yourself permission to log in as root. I know weird right? 🤷‍♀️ Run this command to get into MariaDB. You will be prompted for the root password. > sudo mysql -uroot -p

Now that you're in MariaDB you can run queries as root. Run this query to give yourself permission to run queries through pma and elsewhere. > GRANT ALL PRIVILEGES ON \*.\* TO 'root'@'localhost' IDENTIFIED BY '\[Your Password\]' WITH GRANT OPTION;

Now navigate to the ip for this machine in a web browser and log into the pma instance. Create a user account for pma with permissions to the database it created during the last step. OK LAST STEP I SWEAR. You should still be in your pma directory. Copy config.sample.inc.php to config.inc.php and then edit it. > sudo cp config.sample.inc.php config.inc.php &amp;&amp; sudo nano config.inc.php

You will need to give in a blowfish secret which wants something really specific. You can find a randomly generated one [here](https://cjtrowbridge.com/password-generator/). You will also need to enter the username and password you created for the pma database so that it can manage its own self. And that's it you're done setting up your MySQL/MariaDB instance! Make sure to run the permissions fixer since we are doing all this not as the www-data user and pma wants to be able to edit itself. ## SQLite3

## Congratulations!

That's all it takes to set up a working home development server on a raspberry pi.