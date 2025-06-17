---
id: 12446
title: 'Covid19 Progress'
date: '2020-06-04T15:51:11-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=12446'
permalink: /2020/06/04/covid19-progress/
categories:
    - 'Content Business'
    - Projects
---

I saw an opportunity around the lack of clarity and accessibility for coronavirus statistics. I also saw a lot of misleading claims made by people with an agenda. I wanted to bring clarity to the data and make it easy to understand and compare. And so, [Covid19 Progress](https://cjtrowbridge.com/covid19-progress/) was born! [![covid19-progress](https://blog.cjtrowbridge.com/wp-content/uploads/2020/06/covid19-progress-1-1.jpg)](https://cjtrowbridge.com/covid19-progress/)This simple site allows anyone to log on and compare numbers between any country, and even between states. Rather than giving a total number infected or dead, it reports these things in terms of a percentage of the population. Also interesting is the graphs of change in growth over time. This is part of what inspired the next project, [Corona Country](https://blog.cjtrowbridge.com/2020/06/04/corona-country/). Some of the results are very surprising. For example, while the united states has far more cases than any other country, it is closer to the middle of the pack in terms of percentage of the population infected. Likewise, some states are doing a much better job than others, and this is much easier to see with the tools on this site.

## Tech Stack

The back-end is based on my earlier [Draupnr](https://blog.cjtrowbridge.com/2017/06/21/startup-3-draupnr-io/) project. Once a day, the updated information is fetched from Johns Hopkins, then it gets parsed into data for each separate state and country. The data is filled into a template and comes out in two forms; [chart.js](https://www.chartjs.org/) on top and [tablesorter](https://mottie.github.io/tablesorter/docs/) on the bottom. Producing static html files like this means it's very easy to handle virtually unlimited traffic because the server is not doing any compute during the requests. This is something [Pieter Levels](https://levels.io/) talks about a lot as an important design goal people should keep in mind.