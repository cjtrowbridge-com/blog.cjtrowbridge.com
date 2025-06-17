---
id: 8233
title: 'Implementing the Webroot SecureAnywhere Business Endpoint Protection API in PHP'
date: '2017-03-11T08:56:00-08:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8233'
permalink: /2017/03/11/implementing-webroots-api-in-php/
categories:
    - Projects
    - 'Tech 2U'
---

[![](https://blog.cjtrowbridge.com/wp-content/uploads/2017/03/webroot-1-1.jpg)](https://www.webroot.com/us/en/business/smb/endpoint-protection)At Tech 2U, we sell Webroot SecureAnywhere Business Endpoint Protection as our antivirus product. This is typically used for managed enterprise endpoints. Webroot SecureAnywhere Business Endpoint Protection is managed through a web console which must be accessed each time a new endpoint is created; dozens of times every day for us. This web console is intended to be used for companies managing dozens or maybe a hundred endpoints. We use it to manage many thousands of endpoints. This quickly led to the web console being so slow and unresponsive that it became unusable, taking minutes to load each page. I decided to implement their API in order to avoid using the web console and automate the process of creating keys. I had already built a comprehensive custom PHP/MySQL CRM to manage all operations at Tech 2U, so this new API integration would need to simply create keys whenever they are sold and show them to the person selling them. I came up with this: [PHP-WebrootAPI](https://github.com/cjtrowbridge/PHP-WebrootAPI/blob/master/WebrootAPI.php). It gives you one main function: MakeWebrootKey(); This is pretty straightforward and allows you to create keys by passing in the customer's information. The keys are then stored in a local table and accessible from the customer's profile page, or by searching. Getting this API implemented was very tricky because their documentation is terrible and they don't respond to tickets. I ended up combing through their web console's html to find many of the missing pieces. This is the only way I could find to get the GSM key IDs, Policy IDs and some of the other credentials. Once I had all of those though, implementing the rest of the API fell into place. Check it out and [email me](mailto:chris.j.trowbridge@gmail.com) if you need help or have any questions! There is a tremendous amount of customer information in this API and I can't wait to integrate it into my marketing automation platform! :D