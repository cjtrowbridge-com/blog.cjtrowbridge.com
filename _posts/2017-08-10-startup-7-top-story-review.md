---
id: 8616
title: 'Startup 7: Top Story Review'
date: '2017-08-10T06:37:35-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8616'
permalink: /2017/08/10/startup-7-top-story-review/
categories:
    - Blog
    - 'The Levels Challenge: Build 12 Startups in 12 Months'
---

***This is part of a series on [Building 12 Startups in 12 Months](https://blog.cjtrowbridge.com/category/the-levels-challenge-build-12-startups-in-12-months/).***

***This is number seven: [TopStoryReview.com](https://topstoryreview.com)!***

## Black-Box News is Bad

If you look at the news on Google or Facebook , you will see a few stories which some mysterious algorithm has selected for you. Are these an accurate reflection of current events? No. These stories are often selected to confirm your biases based on your activity and search history. You are seeing the echo-chamber your digital context has created for you, because that is how these companies maximize for your attention in order capture your attention. Facebook and Google use black-box algorithms to pick what you see. This means that not only is there no explanation of how or why your stories were picked, but there is no way even for the engineers to reverse-engineer the algorithm and see how or why it picked the stories it did. It is very common to see stories featured as trending on Facebook which are false, or shared through other services. This effect has led to people doing horrible things based on false information presented as news by algorithms, like [shooting up a pizza place](https://www.washingtonpost.com/news/local/wp/2016/12/04/d-c-police-respond-to-report-of-a-man-with-a-gun-at-comet-ping-pong-restaurant/) or [threatening and harassing the families of murdered children](https://www.theguardian.com/us-news/2017/jun/09/sandy-hook-conspiracy-theorist-death-threats-prison). This is a problem for democracy and a problem for all of humanity. There has been much speculation that this has been a major contributing factor in the recent rise of populism in America and the results of the recent presidential election. Everyone should have access to concise, accurate snapshots of current events. My frustration with the lack of quality and lack of transparency in news aggregation services today led me to create an open-source alternative which omits biases and individual context. ## But How?

This project expands on an experiment I started in high-school. I was trying to aggregate various high quality news sources and then determine what major themes were trending, and present that information in a useful way. Back then, I started with fetching the "Top-Stories" or "Breaking News" RSS feeds from a few dozen newspapers around the US, and combining them all into a MySQL table and then doing word counts to determine which words stood out, and classifying those in order to build a list of general topics, then I displayed the most recent or most reputable source's story for each of the topics. There are several big innovations I have come up with over the years which I can now incorporate into this idea in order to maximize value. **The final product will be simple homepages for lots of topics with a few bullet-points, imparting a concise and accurate representation of the current state of events.**## My Open Algorithm

1. Pull in thousands of rss feeds from an [open list](https://api.topstoryreview.com/sources) of high-quality news sources all over the world.
2. Analyze the stories to find trending topics using my open [condensr ](https://condensr.io/)algorithm.
3. Get all the stories relating to each topic.
4. Condense all of the stories on each topic down to just one sentence.

Step 4 expands on the work of groups like [SMMRY](http://smmry.com/) and Reddit's [autotldr bot](https://www.reddit.com/user/autotldr). My new Condense algorithm can summarize thousands of pages of text into just a sentence or two. This is obviously not perfect, but it is surprisingly good, and there is always room to improve later. ## Structure

The basic structure of the site will be a home page which combines all topics, and then lots of individual pages for each category. The home page and each topic page has a bullet-point list of a few trending stories with one sentence summaries. These bullet-point summaries will eventually link to a story page with a longer summary along with links to recent reporting from various sources. The algorithm runs every hour, and maintains an archive of all the pages, so you can also look back at what was happening at any certain time. In effect, I am building a massive pipeline that takes in much of the world's reporting and produces high quality condensed content which is much easier to absorb. ## The Codebase

Here is the [link to the codebase](https://github.com/cjtrowbridge/TopStoryReview). It's all there and basically you can just fork it and change anything you want. I think there is a lot of opportunity for this project to expand in interesting new directions. ## Making Money

There will be an enormous amount of content created hourly, and that means lots of organic traffic. SEO and social integration will be critical. I will eventually include ads to monetize the content.