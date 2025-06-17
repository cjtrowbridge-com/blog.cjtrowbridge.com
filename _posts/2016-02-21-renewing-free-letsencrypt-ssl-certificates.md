---
id: 6911
title: 'Renewing Free LetsEncrypt SSL Certificates'
date: '2016-02-21T13:13:12-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=6911'
permalink: /2016/02/21/renewing-free-letsencrypt-ssl-certificates/
categories:
    - Projects
---

A few days ago, I received an email from LetsEncrypt letting me know that it was time to renew my free SSL certificates. I tried re-running the tool in order to renew the certificates which seemed to work, but then I received this email;

> | **staging-expiry@letsencrypt.org** &lt;staging-expiry@letsencrypt.org&gt; | Sat, Feb 20, 2016 at 10:15 PM |
> |---|--:|
> | <div>To: chris.j.trowbridge@gmail.com</div> |
> | \| <div>Hello, [ Note: This message is from the Let's Encrypt staging environment. It likely is not relevant to any live web site. ] You issued a testing cert (not a live one) from Let's Encrypt staging environment. This mail takes the place of what would normally be a renewal reminder, but instead is demonstrating delivery of renewal notices. Have a nice day! Details: DNS Names: [blog.cjtrowbridge.com](http://blog.cjtrowbridge.com/)[cjtrowbridge.com](http://cjtrowbridge.com/)[j-ha.us](http://j-ha.us/)[opennewsaggregator.us](http://opennewsaggregator.us/)Expiration Date: 02 Mar 16 03:36 +0000) Days to Expiration: 9 For any questions or support, please visit [https://community.letsencrypt.<wbr></wbr>org/](https://community.letsencrypt.org/). Unfortunately, we can't provide support by email. If you are receiving this email in error, unsubscribe at [REMOVED]. (HTTP link, we know. We're working on it!) Regards, The Let's Encrypt Team </div> \| |
> |---|

It seems my attempt to use the same tool to renew was not the correct way to go about it. I went looking for tutorials online and eventually found the command `letsencrypt-auto renew`. It seems too easy! It took just a few seconds to renew all the certs that were going to expire. [Official Documentation](https://letsencrypt.org/howitworks/) suggests using the following script to automate this process; `#!/bin/shif ! /path/to/letsencrypt-auto renew > /var/log/letsencrypt/renew.log 2>&1 ; then    echo Automated renewal failed:    cat /var/log/letsencrypt/renew.log    exit 1fiapachectl graceful`I created this bash script and added it to the crontab with `0 0 * * 0       root    bash /root/letsencrypt/maybe_renew.sh`Now it should be checking automatically on a weekly basis!