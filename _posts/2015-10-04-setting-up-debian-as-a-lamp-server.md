---
id: 3715
title: 'Setting up Debian as a LAMP Server'
date: '2015-10-04T17:39:09-07:00'
author: cjtrowbridge
layout: post
guid: 'http://cjtrowbridge.com/?p=3715'
permalink: /2015/10/04/setting-up-debian-as-a-lamp-server/
categories:
    - Projects
---

This post is part of a larger series about [Building a Cloud at Home For Free](http://blog.cjtrowbridge.com/2015/10/04/building-a-cloud-at-home-for-free/) as part of building scalable web applications from the ground up. This post starts at the point of setting up our LAMP stack on the a new Debian server. If you still need to setup your hypervisor, virtual server and install Debian, then check out my post [Installing Virtualbox and Debian on Windows 10](http://blog.cjtrowbridge.com/2015/10/04/installing-virtualbox-and-debian-on-windows-10/).

## Setting Up Debian as a LAMP Server

The first step to setting up the server is to log into the machine as root using the password you setup for your root account. ### Setup a Static IP

Use the text editor nano to edit the network configuration file by typing the following command; <fieldset>```
nano /etc/network/interfaces
```

</fieldset>You will find something like this; <fieldset>```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
allow-hotplug eth0
iface eth0 inet dhcp
```

</fieldset>Comment out the old settings for the primary network interfaces and add the new lines shown below. You will need to select an IP and use the correct gateway for your network; <fieldset>```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
#allow-hotplug eth0
#iface eth0 inet dhcp

auto eth0
iface eth0 inet static
	address 8.0.0.11
	netmask 255.255.255.0
	gateway 8.0.0.1
```

</fieldset>Hold down control+x and then press enter to save your changes. Type the command "reboot" into the console to restart the server and apply the changes. ### Enable SSH

Type the following command to get to the config file for SSHD, the service which allows you to remote into the terminal and access <fieldset>```
nano /etc/ssh/sshd_config
```

</fieldset>Find the line that says PermitRootLogin with-password and change it to; <fieldset>```
PermitRootLogin yes
```

</fieldset>Save your changes. Enabling root remotely is potentially a security concern as someone could brute-force the password and have root access. So we need to install fail2ban to prevent this. If too many failed attempts are made, the remote user will be banned from attempting to log into the server. <fieldset>```
apt-get -y install fail2ban
```

</fieldset>This is a good time to reboot; then you can use putty to connect securely to the server! At this point, I switch to putty instead of using the virtual machine, as it is much easier to do the rest of this process with the ability to copy and paste commands. This is not possible when using the console directly, outside of putty. Putty is free software available through ninite or from [putty's website](http://putty.org). ### Set APT To Online-Only

We need to set the package manager to use the online-repositories only, so it won't be constantly asking us to insert the CD. Type out <fieldset>```
nano /etc/apt/sources.list
```

</fieldset>Find the line that starts with "deb cdrom"... Add a "#" at the beginning to comment it out, and then Ctrl+X to save! Simple as that. ### Install Apache2 With SSL

If you do not want to buy an SSL certificate, you can create your own, but it will prompt visitors that your certificate is invalid every 24 hours when they look at your page. Depending on what you are doing, either option might be appropriate, but in the spirit of doing this for free, I am demonstrating the free self-signed certificate process option. Logged in as root, run the command; <fieldset>```
apt-get -y update && apt-get -y upgrade
```

</fieldset>This will update all your installed packages and get you ready to run this command to install Apache2; <fieldset>```
apt-get -y install apache2
```

</fieldset>Now enable SSL by executing the following series of commands; <fieldset>```
a2enmod ssl
a2enmod rewrite
apt-get -y install mysql-server
a2ensite default-ssl
service apache2 reload
mkdir /etc/apache2/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/apache2/ssl/apache.key -out /etc/apache2/ssl/apache.crt
```

</fieldset>SSL will ask you several questions as shown below. The most important one is the [FQDN](https://en.wikipedia.org/wiki/Fully_qualified_domain_name) which should be the domain name if you are using one or else the hostname or ip if you are not using a public domain. <fieldsdet>```
Country Name (2 letter code) [AU]:US
State or Province Name (full name) [Some-State]:California
Locality Name (eg, city) []:Sacramento
Organization Name (eg, company) [Internet Widgits Pty Ltd]:CJTrowbridge
Organizational Unit Name (eg, section) []:Projects
Common Name (e.g. server FQDN or YOUR name) []:projects.cjtrowbridge.com
Email Address []:cj@cjtrowbridge.com
```

Now run this command to set the correct permissions for your new self-signed certificate; <fieldset>```
chmod 600 /etc/apache2/ssl/*
```

</fieldset>Now you need to edit the configuration file for both SSL and non-SSL connections in Apache by running the following commands; You will need to pick a document root. The typical default is /var/www/html but i prefer /var/www for simplicity's sake. Just make sure it matches in both of the following files... Most likely this will already be basically setup correctly. You will need to set the correct paths to the certificate files you created above, change 'example.com' to your FQDN, set the correct email address, and make sure these other lines are written somewhere in the file and not commented out with a hashtag before them. <fieldset>```
nano /etc/apache2/sites-enabled/default-ssl.conf
```

</fieldset><fieldset>```
<IfModule mod_ssl.c>
    <VirtualHost _default_:443>
        ServerAdmin webmaster@localhost
        ServerName example.com:443
        DocumentRoot /var/www

        SSLEngine on
        SSLCertificateFile /etc/apache2/ssl/apache.crt
        SSLCertificateKeyFile /etc/apache2/ssl/apache.key

    </VirtualHost>
</IfModule>
```

</fieldset><fieldset>```
nano /etc/apache2/sites-enabled/000-default.conf
```

</fieldset><fieldset>```
<VirtualHost *:80>
        ServerAdmin webmaster@localhost
        ServerName example.com:443
        DocumentRoot /var/www
</VirtualHost>
```

</fieldset>Run the following command to restart apache now that these changes have been saved; <fieldset>```
service apache2 reload
```

</fieldset>Test the SSL by typing in your hostname or ip to a browser like 'https://8.0.0.11' You should see a warning about an invalid certificate. Select the option to proceed anyway, or in chrome type out the word 'danger' and it will bypass this screen for 24 hours. These warnings can be very obnoxious, and it is a tempting buy at around $50/year for a valid SSL certificate, but the 24 hour setting can also be changed in chrome in order to avoid paying for a certificate while also avoiding the warnings. :\] ### Install MySQL

For the purposes of this project, I will creating a separate, dedicated MySQL server. BUT, installing MySQL on this server fulfills some dependencies for PHP and Apache that can cause issues with connecting to databases, so we install it anyway by running the following command; <fieldset>```
apt-get -y install mysql-server
```

</fieldset>You will be prompted to create a root MySQL password. Make it a strong one! After installation is done, execute the following command to run the secure installation. It will give you lots of suggestions for securing your installation. <fieldset>```
mysql_secure_installation
```

</fieldset>### Install PHP

Now we install PHP, the real heart and soul behind the web applications we will be building on this server. Type the following commands; <fieldset>```
apt-get -y install php5 php-pear php5-mysql
```

</fieldset>Install mcrypt to enable php to use cryptography. <fieldset>```
apt-get install php5-mcrypt
php5enmod mcrypt
```

</fieldset>cURL is required by things like wordpress, and generally good to have, so let's install that too; <fieldset>```
apt-get install php5-curl
```

</fieldset>Finally restart apache to let all the changes take effect; <fieldset>```
service apache2 restart
```

</fieldset>### Test Your Server!

Let's create a phpinfo file. Run the following command; <fieldset>```
nano /var/www/info.php
```

</fieldset>Note that depending on the path you used in setting up your SSL configuration file, the file might need to be in /var/www/html instead of /var/www/ Put the following code into the file and save it. <fieldset>```
<?php phpinfo(); ?>
```

</fieldset>The moment of truth... Now navigate to https://hostname/info.php If it works, you will get a certificate error and then a page like this telling you all about your php server :D <center>[![phpinfo](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/phpinfo-465x261.png)](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/phpinfo.png)</center>Now you're ready to move on to [Setting Up Debian as a Postfix Mail Server](http://blog.cjtrowbridge.com/2015/10/09/setting-up-debian-as-a-postfix-mail-server/)</fieldsdet>