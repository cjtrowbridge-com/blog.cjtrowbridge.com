---
id: 8684
title: 'How To Migrate Production MySQL Database Servers'
date: '2017-06-10T16:32:15-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8684'
permalink: /2017/06/10/migrating-production-database-servers/
categories:
    - Projects
    - 'Tech 2U'
---

Migrating database servers in production, whether they are large or small, is a surprisingly simple process but a delicate one. There are fewer methods available as the size goes up. This is something I have been asked about by several colleagues so I decided to document my processes and best practices.

## The File Method (BEST)

This assumes you can afford a few minutes of downtime, and that you are using Debian/Ubuntu or something like it, and MySQL on both servers. Take your database application offline, and then on the origin server run this command; > /usr/bin/mysqldump -u\[Username\] -p\[Password\] \[Database\] &gt; backup.sql

This will take a while and give you the sql file you need. I just moved the file to a directory on the origin server where I could wget it from the destination server. But you could also email it to yourself or use a flash drive or network share. Now on the destination server, create a new blank database with the same name and run this command in the same directory as that file; > mysql -u\[Username\] -p \[Database\]&lt; backup.sql

You will be prompted for the new server's password and then it will put all the content into the new database. This is not a complex process, but it is a powerful one because it works no matter how large and complex the database is. I recently used this for a database containing millions of rows in dozens of tables. ## PHPMyAdmin Method (Easiest)

If your database is just a few megabytes or less, you can use PHPMyAdmin to transfer everything to a new server. ![](https://blog.cjtrowbridge.com/wp-content/uploads/2017/06/phpmyadmin-export-1-1.png)On the origin server, navigate to the database you want to migrate, and click the "Export" tab at the top. ![](https://blog.cjtrowbridge.com/wp-content/uploads/2017/06/phpmyadmin-custom-1-1.png)Select "Custom" for the export option, and then "View Output as Text" and submit. This will take a while and give you a text box full of SQL code. This is the same code that would be in the file we generate in the "File Method" mentioned above. If the database is too large, this step could freeze or crash the browser, but for smaller databases, this should work fine. Now copy that text and navigate to the destination server's PHPMyAdmin installation. Create a database with the same name, and navigate to the SQL tab within that database. Paste the code there and click "Go." You have successfully migrated your database! ## The Replication Method (Hardest)

Digital Ocean has a [great tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-mysql-master-master-replication) on this alternative option, but it is a lot more technically complex. I would not advise this unless 100% uptime is critical. Using the file method will only give you a few minutes of downtime, and if you can't afford that you probably shouldn't need this tutorial ;P If 100% uptime is critical, use [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-mysql-master-master-replication) to set up slave replication to the new server, then switch the application load over to that server, and [disable slave replication](https://dba.stackexchange.com/questions/21119/how-do-i-completely-disable-mysql-replication). You have now migrated production servers with zero downtime! (But really, you should use the File method. It is much less complex and far easier to implement.)