---
id: 5328
title: 'Moving My App To The Cloud'
date: '2015-12-13T09:56:33-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=5328'
permalink: /2015/12/13/moving-my-app-to-the-cloud/
categories:
    - Projects
    - 'Tech 2U'
---

I have spent the better part of the last three years building a scalable logistics platform which has grown to manage nearly all the daily operations of my workplace, a mobile tech support company. Some Major Features;

- Booking appointments and scheduling them for employees in different regions and markets 
    - Providing a portal for employees to see their jobs and communicate status to central dispatch
- Handling accounting 
    - Lots of custom reporting and alerts built in
- Payroll calculations 
    - Lots of different pay structures and commission rates
- Reporting on sales data 
    - Accounting and strategy development
    - Employee development
- Outreach 
    - Automatic outbound emails and calls for lots of different segmentations and purposes
    - Outbound sales for well-qualified customers
    - Follow-up surveys for quality assurance and customer satisfaction reporting
- Business Intelligence 
    - Predictive algorithms identify logistical problems before they happen and suggest fixes

This app started out as a way to make my job easier, managing daily operations and logistics. It quickly grew to take over much of our operations management, facilitating daily operations across the country and automating many previously tedious procedures and functions. As it grew, it became more mission-critical.It currently provides essential infrastructure to many employee roles and daily operations. A recent series of power outages proved that hosting it in-house was a bad idea, so I have begun to work on a solution: *migration to the cloud*. ## Let's Get Started

1. The first step was to build a VPS using my [Setting Up WordPress on a VPS](https://blog.cjtrowbridge.com/2015/12/03/setting-up-wordpress-on-a-vps/) tutorial to build the VPS, and then instead of installing Wordpress, I copied over my app's PHP files from its previous server.
2. Next, I needed a secure connection to the existing databases until they can be migrated as well. I considered using a VPN, but this would be unduly complex because of the way our corporate network is setup.SSH is a great alternative to VPN. I used SSH to create a secure tunnel from the office to the new VPS. SSH has a feature which allows you to bind a port on the local machine to a port on the remote machine. In this way, I was able to connect from the VPS to the SQL server in the office.
3. Next, I needed to rebuild many aspects of my app to use locally cached data instead of remote data. I built a new tool which continuously synchronizes a local copy of the remote database. This means that the remote database connection can fail without affecting the app. This parallels the future use-case when many companies may use the app, and all their data would need to be synchronized into the local database as well.