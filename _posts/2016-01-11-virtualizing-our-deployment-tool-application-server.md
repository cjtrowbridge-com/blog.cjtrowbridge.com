---
id: 6744
title: 'Virtualizing An Application Server'
date: '2016-01-11T13:49:49-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6744'
permalink: /2016/01/11/virtualizing-our-deployment-tool-application-server/
categories:
    - Projects
    - 'Tech 2U'
---

Another department at Tech 2U performs diagnostics on lots of computers. They use a proprietary tool that they built which deploys diagnostic tools on customers' computers during tech support services. This tool was built years ago by someone who no longer works here. He used a baremetal Apache server to host the tools. This server crashed, crippling the tool and everyone who relied on it. I decided to move the tools to a new cloud VPS. I created a new Droplet on Digital Ocean ([Referral Code](https://www.digitalocean.com/?refcode=ecb56e953504)) for $5/month. I chose Debian 8 amd64 for the OS and set a hostname of the new fqdn. Once I created the droplet, I pulled its IP and created a new DNS A-Record on our main domain account to forward that hostname to the new VPS. Now the VPS was finished building so I ran `apt-get -y update && apt-get -y upgrade` to update any packages that have changed since Digital Ocean built their image for this type of server. `apt-get -y install fail2ban apache2 && apt-get -y install && a2enmod rewrite && service apache2 restart && apt-get -y install screenfetch htop nload curl git ntp`Now I make a new folder for the virtualhost with `mkdir /var/www/[fqdn]`Now we make a new virtualhost conf file with this command. Again, substitute your fqdn; `cp /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/[fqdn].conf`Then edit the file with `nano /etc/apache2/sites-available/[fqdn].conf`It needs to contain the following;

```
	ServerName [fqdn]

	ServerAdmin your_email@website.com
	DocumentRoot /var/www/[fqdn]/

	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined
```

I also created another virtualhost to server the /var/www directory. This virtualhost will be secured with a directory password and contain some diagnostic and performance monitoring tools. Now I disable the default VirtualHost with `a2dissite 000-default`Then enable my new virtualhosts with `a2ensite [fqdn]`And restart Apache with `service apache2 restart`**BitTorrent Sync**If you're not already familiar with BitTorrent Sync, it is a free, secure option for synchronizing directory structures in real time. I use it to synchronize the app between different web servers. Any changes are immediately propagated everywhere. This is also the vehicle for delivering updates to the server from the people who manage it. This command will download the script to install version 1.4 of BitTorrent sync. Note that this is not the most recent version, as the new version is very limited in features and requires much more resources to run. `sh -c "$(curl -fsSL http://debian.yeasoft.net/add-btsync14-repository.sh)"`Then, run this command to install BitTorrent Sync `apt-get update && apt-get install btsync`Now we need to clean up any permissions and ownership issues with the following commands; `chmod 775 /var/www/ -Rchown www-data:www-data /var/www/ -Rchown www-data:btsync /var/www/f2.tech2u.com -R`Then we configure btsync to synchronize the app's folder, and it does the work of importing the app. Now I simply add the old BitTorrent key to the correct directory and then all the files copy over! Eureka! ![screenfetch](https://blog.cjtrowbridge.com/wp-content/uploads/2016/01/screenfetch-1-1.png)