---
id: 3708
title: 'Building a Cloud For Free'
date: '2015-10-04T12:20:14-07:00'
author: cjtrowbridge
layout: post
guid: 'http://cjtrowbridge.com/?p=3708'
permalink: /2015/10/04/building-a-cloud-for-free/
image: /wp-content/uploads/2015/10/9465333342_7dfc53074d_b_fullwidth-1.jpg
categories:
    - Projects
---

This post explains how I am building my own cloud at home. One of my biggest goals is to do this for free, or for as close to free as possible.

#### What will it do?

- Serve as a complete virtualized development environment for custom dynamic web applications
- Multimedia server including secure torrent downloader
- Use lots of different kinds of technology to make the learning experience as broad as possible
- Scale to incorporate more physical machines in the future and more apps as I develop them

[![9465333342_7dfc53074d_b_fullwidth](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/9465333342_7dfc53074d_b_fullwidth-465x349.jpg)](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/9465333342_7dfc53074d_b_fullwidth.jpg) Lets get started... #### Getting On The Web

I connected this system to a .com domain using Asus' free DDNS service which is included with my [free Asus AC68U router](http://blog.cjtrowbridge.com/2015/10/12/how-i-got-a-free-180-asus-rt-ac68u-router/). I set up a new DNS A-Record on a free subdomain of my website which forwards traffic to my new cloud via DDNS. #### Building The First Server

The first step was to setup a clean install of Debian Linux on a virtual server. This process is covered in detail in another post [here](http://blog.cjtrowbridge.com/2015/10/04/installing-virtualbox-and-debian-on-windows-10/). After VirtualBox was setup and Debian was installed, I configured it as the first LAMP server in my cloud. When I taught myself to do this, the learning process was very confusing and complicated. I have done my best to explain all the details and the steps that other tutorials have left out in my post [Setting up Debian as a LAMP Server](http://blog.cjtrowbridge.com/2015/10/04/setting-up-a-debian-lamp-server/)Once the LAMP is setup, it needs to be able to send emails. Click [here](http://blog.cjtrowbridge.com/2015/10/09/setting-up-a-debian-postfix-mail-server/) to see how I got Postfix setup to handle outbound mail for this first server. #### Going Forward

Next, it's time to build a dedicated database server. Once the database server is setup, it is time to build the nginx server which will eventually manage load-balancing and enable the system to scale up in the future and handle a larger number of simultaneous requests. The NAS will securely serve files over the web as well as receiving real-time backups from the erst of the cloud as well as all my personal devices. The server also has functions built in to allow file management from the web and even starting downloads remotely. Arduino will let me incorporate some home automation features as well as monitoring power usage by my cloud. I will be continuously developing this system and adding features all the time, so check back and make sure to leave feedback!