---
id: 8534
title: 'Startup 1: Securities Science'
date: '2017-05-18T15:45:24-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8534'
permalink: /2017/05/18/startup-1-securities-science/
categories:
    - 'The Levels Challenge: Build 12 Startups in 12 Months'
---

***This is part of a series on [Building 12 Startups in 12 Months](https://blog.cjtrowbridge.com/category/the-levels-challenge-build-12-startups-in-12-months/).***

***This is number one: [Securities.Science](https://securities.science)!***

## What Inspired This Project?

My first startup in the series is [Securities.Science](https://securities.science). It lets users run queries against historic stock trading data in order to test theories and strategies. All data is public and everyone can see the work that others are doing. This started with my coworker Luke Leggio and I trying to collaborate on developing strategies for trading leveraged commodity ETFs on RobinHood. I was very frustrated with the few tools and communities that exist for this purpose. I had tried [Openfolio](https://openfolio.com/) which has since pivoted to a totally different kind of product. At the time, they let you share your trading activity and results with others and compare to how their strategies worked out for them. The problem was that it was terribly buggy and often reported things incorrectly. I wrote to their support people several times, even offering to do the work of fixing their products for them because the problems were so obvious. (Numbers being negative instead of positive when pulled from certain APIs, etc.) Some features like search and viewing the top performers didn't work at all. They had no interest in making their product work, so I decided to make my own as an alternative. Securities.Science automatically pulls data from various public APIs and allow users to write SQL queries that implement securities trading strategies. Their queries will pair with simple visualization tools in order to show how each strategy works over time. ## First Steps

The site is now live, and the source code is all available on Github. Anyone can sign up for free and start running queries against historic datasets. I have included lots of different tickers including all of the leveraged commodity ETFs which I follow, along with all the top stocks millennials like [according to Business Insider](http://www.businessinsider.com/the-top-stocks-millennials-are-buying-robinhood-data-2017-4). Adding more is trivially easy, but I didn't want to just add thousands of tickers because of the maintenance overhead. And because most of them are not particularly interesting. I wrote this as a plugin for [Astria](https://astria.io), a simple web application framework I have been developing for almost a decade. The code is very simple and hopefully distilled to the minimum necessary to explain the content. [Check it out!](https://github.com/cjtrowbridge/securities.science)## Next Steps

There are a few next steps that jump out at me if this finds adoption. **Expanded Datasets**The page describing available data encourages the user to reach out to me if they want to see any additional data sources. Eventually, users should be able to add data sources for whatever they want with simple tools. **Content Development**Scraping and collating data is one thing, but presenting it in a format which brings in organic traffic is a separate art. Other news and data sources relating to each stock could be integrated so that users can focus on particular industries, commodities, or ETFs and get more information than just trading data. **Execution Integration**There are lots of great APIs which would allow integration with stock brokerages so that users can set up triggers for buying and selling based on their models in the app. It would be fun to add that later. **Machine Learning and Other Advanced Analytics**The first version of the product only features SQL queries for strategy development. This enables lots of interesting and basic strategies to be implemented and tested, but adding machine learning and other advanced analytics features would be another order of magnitude in capability for users. 