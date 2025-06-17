---
id: 8749
title: 'How to Build a Free Linux Microsoft SQL Server'
date: '2017-07-01T17:55:03-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8749'
permalink: /2017/07/01/how-to-build-a-free-linux-microsoft-sql-server/
categories:
    - Projects
    - 'Tech 2U'
---

This covers how to create a virtual linux server running Microsoft SQL Server. First, create a virtual server with the following requirements in mind.

- Ubuntu 14.02 LTS (Server or Desktop)
- At least two CPUs
- At least 4gb RAM
- At least 10GB HDD for the operating system
- PLUS at least double the amount of space your databases will use

When you install Ubuntu, make sure to enable updates and third-party software, unless you're the real DIY-type. First, update the default installation packages; > sudo apt-get update &amp;&amp; sudo apt-get upgrade

Now we need to install a few tools before we can get started; > sudo apt-get install cifs-utils curl

## Install Microsoft SQL Server

Run these commands to install Microsoft SQL Server and its tools; > curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add - curl https://packages.microsoft.com/config/ubuntu/16.04/mssql-server.list | sudo tee /etc/apt/sources.list.d/mssql-server.list sudo apt-get update &amp;&amp; sudo apt-get install -y mssql-server sudo /opt/mssql/bin/mssql-conf setup

You will be prompted to create an SA or Server Administrator password. Use something with [high entropy](https://password-generator.cjtrowbridge.com)! Now install tools; > curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add - curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | sudo tee /etc/apt/sources.list.d/msprod.list sudo apt-get update &amp;&amp; sudo apt-get install mssql-tools unixodbc-dev echo 'export PATH="$PATH:/opt/mssql-tools/bin"' &gt;&gt; ~/.bash\_profile echo 'export PATH="$PATH:/opt/mssql-tools/bin"' &gt;&gt; ~/.bashrc source ~/.bashrc

Now, copy over your backup file and put it in /var/opt/mssql/data/ I have not gotten the cli tools to work for importing the backups. They seem to look for Windows paths. You will need to use MS SQL Studio to import the backup.