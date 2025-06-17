---
id: 8943
title: 'Startup 9: What are you wearing today?'
date: '2018-01-12T14:29:56-08:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=8943'
permalink: /2018/01/12/startup-9-wearing-today/
categories:
    - 'The Levels Challenge: Build 12 Startups in 12 Months'
---

Like many people, I am a student. I attend over a dozen classes at two different colleges. I also attend regular social events and networking meetups. I often wonder as I am dressing, is this the same thing I wore last time I went to the place I'm heading now? It sounds silly, but it's something I always ask myself because I want to make the right impression. This is further complicated by the fact that I am something of a minimalist, so I keep less than ten shirts at any given time and only a few pair of pants/ shorts. I was talking one day to my mom about this anxiety I feel, and she emphatically agreed. I decided to make a simple app to keep track of what I wear each day so that I can look back and see what I wore last time I was at a particular class or event and know not to wear the same thing again. It's schmuck insurance. [Wearing.Today](https://wearing.today) is the result!

## MVP

The minimum viable product version of this app is not social; each user's profile is private. Users can post pictures from a simple single-page app which also lets them edit each post's blurb, or delete their posts. ## Paradigm Shift

This app is written completely in the functional paradigm. I wrote it as a single page html/js application which is built to be hosted on S3 and take advantage of Lambda for the functions. I did not actually deploy it there because I Don't already have accounts with those services, and they don't support my primary language, PHP. The point was not to actually do those things, but to rapidly write a simple, complete app in that paradigm and get a sense of the workflow and how to construct the API.