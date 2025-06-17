---
id: 3842
title: 'Setting Up Debian as a Postfix Mail Server'
date: '2015-10-09T18:46:02-07:00'
author: cjtrowbridge
layout: post
guid: 'http://cjtrowbridge.com/?p=3842'
permalink: /2015/10/09/setting-up-debian-as-a-postfix-mail-server/
categories:
    - Projects
---

This post is part of a larger series about [Building a Cloud at Home For Free](http://blog.cjtrowbridge.com/2015/10/04/building-a-cloud-at-home-for-free/) as part of building scalable web applications from the ground up. This post starts at the point of setting the server up to be able to send emails. If you still need to setup your hypervisor and virtual server or install and configure Debian, check out my post [Installing Virtualbox and Debian on Windows 10](http://blog.cjtrowbridge.com/2015/10/04/installing-virtualbox-and-debian-on-windows-10/).

### Install Postfix

For the purposes of this post, I have chosen to install Postfix. It is a simple solution that works for what we need; sending emails directly from our server cluster. If you are trying to start an email company, this might not be the right option for you :P In order to install PostFix and the associated tools, run the following commands as root in debian; <fieldset>```
apt-get -y install postfix
```

</fieldset><fieldset>```
apt-get -y install mailutils
```

</fieldset>Once installation is complete, you will receive the following prompt; <center>[![postfix1](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/postfix1-465x311.png)](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/postfix1.png)</center><center>[![postfix2](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/postfix2-465x310.png)](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/postfix2.png)</center>In this case, I choose "Internet Site." You will then be prompted to enter the [FQDN](https://en.wikipedia.org/wiki/Fully_qualified_domain_name) for the site. There are lots of options for configuring Postfix. [Check out this tutorial if you want more information about postfix...](https://wiki.debian.org/Postfix)First lets edit the config file with the command; <fieldset>```
nano /etc/postfix/main.cf
```

</fieldset>We need to make sure the following lines have the correct values. Make sure to replace yoursite.com with your fqdn. <fieldset>```
myorigin=yoursite.com
myhostname=yoursite.com
inet_interfaces = 127.0.0.1
```

</fieldset>Because we are changing the inet\_interfaces, a simple reload of postfix is not enough. We need to stop and start it in order for this change to take effect. <fieldset>```
postfix stop
postfix start
```

</fieldset>Now we need to create a firewall rule to disable any connections to the smtp server not coming from localhost with the following command. Be careful as messing this up could be difficult to fix. What it does is create a rule to block any incoming connections to port 25 from our ethernet connection. <fieldset>```
iptables -A INPUT -i eth0 -j REJECT -p tcp --dport 25
```

</fieldset>Now setup your webmaster address. Type the following command and you will see a list of aliases set to root. At the end, you will see root and your username. Change your username to the email you want these emails to be forwarded to, then save. <fieldset>```
nano /etc/aliases
```

</fieldset>Type this command to save the changes to aliases. <fieldset>```
newaliases
```

</fieldset>Type the following two commands to reload the server to let the changes take effect. Normally this step is sufficient for most changes that need to take effect other than inet\_interfaces changes. <fieldset>```
postfix reload
```

</fieldset>Now it's time to test the server... <fieldset>```
telnet localhost 25
```

</fieldset>You should see something like this; <fieldset>```
root@mail1:~# telnet localhost 25
Trying ::1...
Connected to localhost.
Escape character is '^]'.
220 f2.tech2u.com ESMTP Postfix (Debian/GNU)
```

</fieldset>Now send a test email! (These commands need to be entered one at a time) <fieldset>```
mail from: <example>
rcpt to: <me>
data
To: me@myemaildomain.com
From: example@testdomain.tld
Subject: TEST SUBJECT
This is a test email sent by telnet through postfix!
.
</me></example>
```

</fieldset>You will then get something like "250 2.0.0 Ok: queued as EBECF8B" This means your message has been queued to send and will go out shortly! Type the command 'quit' to get out of telnet. You should receive your email after just a moment! If configured as specified, your new email server should be very secure and only accessible from localhost.