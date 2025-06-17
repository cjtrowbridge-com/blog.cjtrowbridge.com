---
id: 6946
title: 'VPS Setup: Create A Virtual Host'
date: '2016-02-21T12:35:34-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6946'
permalink: /2016/02/21/vps-setup-create-a-virtual-host/
categories:
    - Projects
    - 'Tech 2U'
---

This is a subpost of the larger post [Updated Comprehensive VPS Setup Documentation](https://blog.cjtrowbridge.com/2016/02/21/updated-comprehensive-vps-setup-documentation/). Once you have your FQDN forwarded to the VPS, create a directory for it with; `mkdir /var/www/[fqdn]/`Now we make a new virtualhost conf file with this command. Again, substitute your fqdn; `cp /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/[fqdn].conf`Then edit the file with `nano /etc/apache2/sites-available/[fqdn].conf`It needs to contain the following;

```
	ServerName [fqdn]

	ServerAdmin your_email@website.com
	DocumentRoot /var/www/[fqdn]/

	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined
```

Activate the new virtualhost with `a2ensite [fqdn]` and if you haven't already done this, deactivate the default virtualhost with `a2dissite 000-default.conf`Restart apache with `service apache2 restart` so the changes take effect. **Automated Backups**If you want to setup automated backups, create a new directory for the backups; `mkdir /var/backups/``[fqdn]` Add the following line to /etc/crontab in order to facilitate automatic daily backups; `0 22 * * * root tar -cf /var/backups/[fqdn]/www-backup-$( date +'\%Y-\%m-\%d_\%H-\%M-\%S' ).gz /var/www/[fqdn]` Or if you would prefer weekly updates every Sunday night, use this instead; ```
0 0 * * 0 root tar -cf /var/backups/[fqdn]/www-backup-$( date +'\%Y-\%m-\%d_\%H-\%M-\%S' ).gz /var/www/[fqdn]
```