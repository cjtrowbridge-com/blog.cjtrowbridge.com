---
id: 4298
title: 'Building the Web Application Framework Stack'
date: '2015-11-05T15:52:06-08:00'
author: cjtrowbridge
layout: post
guid: 'http://blog.cjtrowbridge.com/?p=4298'
permalink: /2015/11/05/building-the-web-application-framework-stack/
categories:
    - Projects
---

This post begins at the point of having installed Debian, Apache, MySQL, and PHP and being ready to start developing web applications. Now I need to install the technologies that facilitate some of the higher level features I will be using.

### Installing and Configuring Git

First step is to install Git. This will help keep track of versioning and changes as the work progresses. `apt-get -y install git`I followed these steps to configure my local git account; <codegit chris.j.trowbridge="" config="" git="" trowbridge="" user.email="" user.name="">Then I setup the repository for this project by navigating to the correct directory, in this case... `cd /var/www/projects`And running the command; `git init`I am greeted with the message "Initialized empty Git repository in /var/www/projects/.git/" ### Installing Node.Js

The first step is to get the install file; `curl --silent --location https://deb.nodesource.com/setup_0.12 | bash -`Then run the install; `apt-get install nodejs`### Installing Bower

Bower is a package manager for web application frameworks that helps keep all our frameworks up to date, along with their dependencies. I installed it with this command; `npm install -g bower`In order to configure bower, the following commands need to be run as a user instead of root, so I used `su cj` to switch to my user account. And then I installed some frameworks; `bower install jquerybower install jquery-uibower install bootstrapbower install angularbower install material-design-iconsbower install polymer`If you encounter permissions errors at this step, you may need to use something like `chown -R cj:cj /var/www` to give yourself ownership of the directories. I created new virtual hosts for a number of different websites I am hosting on this server, including this blog. As such, they were owned by the root account that created them, and bower was not able to access them from the user account until I made my user account the owner. Now all I need to do in order to keep every part of the server and all my frameworks up to date is periodically run; `apt-get update && apt-get -y upgrade && npm update && bower --allow-root update`</codegit>