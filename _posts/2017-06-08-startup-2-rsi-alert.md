---
id: 8630
title: 'Startup 2: RSI Alert'
date: '2017-06-08T11:25:46-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8630'
permalink: /2017/06/08/startup-2-rsi-alert/
categories:
    - Projects
    - 'The Levels Challenge: Build 12 Startups in 12 Months'
---

***This is part of a series on [Building 12 Startups in 12 Months](https://blog.cjtrowbridge.com/category/the-levels-challenge-build-12-startups-in-12-months/).***

***This is product number two: [RSIAlert.com](https://rsialert.com/)!***

# What Inspired This Project?

I follow a few dozen stocks and do some day trading in my spare time. Working on a previous project [Securities.Science](https://blog.cjtrowbridge.com/2017/05/18/startup-1-securities-science/), I did some research into strategies using RSI to decide when to buy and sell stocks. I got some feedback from the first users of that project about how they would like to be able to receive email alerts at certain indicator points. For example, [one simulation](https://securities.science/run-query/1/buy+at+open+on+days+where+rsi+%26lt%3B+30%2C+sell+at+close.) on [Securities.Science](https://blog.cjtrowbridge.com/2017/05/18/startup-1-securities-science/) explored trading based on the RSI-14, or the RSI for the previous 14 trading days. Whenever the RSI-14 of a stock is below 30, the simulation buys, and then sells at close on the same day. Run against the previous year's data, this simulation indicated a 136% return. This number could easily be improved upon by selling at a better point than close, but that's another story. Initially, I explored trying to add email alerts to queries inside [Securities.Science](https://blog.cjtrowbridge.com/2017/05/18/startup-1-securities-science/), but it really isn't set up to work that way. Users construct arbitrary datasets which would be difficult to integrate into a mail trigger system, and there is obviously potential risk of abuse with automated outbound emails. I decided to build a new product which focuses on only this one type of automated email. This product is very simple compared to the other ones I am considering for this challenge. It just shows a list of a few high-return securities and their RSI-14 as of the previous close. Users can sign up to receive email alerts each day letting them know when the RSI-14 of any of the securities is below 30. ## What Exactly is RSI?

<div id="explanation">*From [Investopedia](http://www.investopedia.com/terms/r/rsi.asp):*"The relative strength index (RSI) is a momentum indicator developed by noted technical analyst Welles Wilder, that compares the magnitude of recent gains and losses over a specified time period to measure speed and change of price movements of a security. It is primarily used to attempt to identify overbought or oversold conditions in the trading of an asset... The RSI provides a relative evaluation of the strength of a security's recent price performance, thus making it a momentum indicator. RSI values range from 0 to 100. The default time frame for comparing up periods to down periods is 14, as in 14 trading days... Traditional interpretation and usage of the RSI is that RSI values of 70 or above indicate that a security is becoming overbought or overvalued, and therefore may be primed for a trend reversal or corrective pullback in price. On the other side of RSI values, an RSI reading of 30 or below is commonly interpreted as indicating an oversold or undervalued condition that may signal a trend change or corrective price reversal to the upside." </div>## Straightforward Monetization

Monetization will be very straightforward; ads on the site and maybe in emails. This project also has the potential to expand into other verticals for various other things people may want automated emails about. ## Lack of Similar Products Means Competitive Advantage

As far as I am aware, there is no other product which does what this does, or I would be using that myself rather than building this. A few companies have put together similar models for other topics, like Medium which offers a daily email containing some stories they have picked for you to read. I was also partially inspired by [IFTTT](https://ifttt.com/discover) which allows you to set up automated emails for lots of different things, but it all requires domain expertise and setting it up involves some degree of technical complexity. This product and any future expansion is designed to be idiot-proof, with a broad market in mind. ## Future Features

One obvious next step would be to integrate this with my upcoming current-events project; automatically including relevant news content related to these data would be valuable data for users to analyze along with the RSI-14 data.