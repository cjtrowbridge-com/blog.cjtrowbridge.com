---
id: 8718
title: 'Startup 3: Draupnr'
date: '2017-06-21T00:32:08-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8718'
permalink: /2017/06/21/startup-3-draupnr-io/
categories:
    - 'The Levels Challenge: Build 12 Startups in 12 Months'
---

***This is part of a series on [Building 12 Startups in 12 Months](https://blog.cjtrowbridge.com/category/the-levels-challenge-build-12-startups-in-12-months/).***

***This is product number three: [Draupnr](https://draupnr.io/)!***

Serving a folder full of html files will always be orders of magnitude faster than any dynamic, scripted site. It also requires orders of magnitude less in resources and thereby cost. Also, this paradigm allows better integration with serverless deployment and better integration with functional paradigm compute services especially. This will come up again in later projects. But, it is hard to modify content on large sites with hundreds of pages, when the pages are all static. Nonetheless, we go to incredible lengths to simulate the speed of static pages through elaborate caching schemes. There are entire industries built on the idea of serving static versions of dynamic sites. I have been experimenting recently with the ability to automatically, periodically fetch some data sources and then insert things into templates and generate static html files based on the data. The performance boost versus a dynamic PHP site is enormous, and the important parts can still be dynamic using JavaScript, ajax, or even PHP (ie. Facebook integration, etc.). ## The Name

There is an old Norse story about a gold ring owned by Odin. Every ninth day, draupnir dripped eight copies of itself. When I was thinking about what I want this project to do, the ring from this story jumped out as the perfect name for this project. ![](https://blog.cjtrowbridge.com/wp-content/uploads/2017/06/Draupnir-1-1.jpg)## How It Works

Periodically, the system tries to fetch various data sources and perform some work on them, then it injects the results into a series of templates and outputs that as a series of static html files. This happens automatically on a set schedule, or whenever the admin wants to make a change to the site. This means the site is effectively just a set of static files but with all the benefits of a dynamic application. Obviously this does not work for every type of application. But it is perfect as a cms for a blog or some other type of data-driven content which updates infrequently enough as to gain the benefits of this approach. This idea was inspired in large part on my previous work on [RSIAlert.com](https://rsialert.com) and by [Ev Bogue's ](http://evbogue.com/)work on [metalsmith](http://evbogue.com/metalwork/). The product is available for free on [Github](https://github.com/cjtrowbridge/Draupnr) and there is a live example at [Draupnr.io](https://draupnr.io/) which automatically creates a static html page each day with a random design quote fetched from a public API.