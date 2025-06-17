---
id: 10252
title: 'Startup 11: PHP TTS Webhooks'
date: '2018-05-15T17:32:32-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=10252'
permalink: /2018/05/15/startup-11-php-tts/
categories:
    - 'The Levels Challenge: Build 12 Startups in 12 Months'
---

# Smart Homes Are Pretty Great

I have very much jumped on the bandwagon with smart home products. I have smart lights, a smart fan, a virtual assistant in every room; mine is a very smart house. I have also gotten very into [IFTTT](https://ifttt.com) and related functional services which integrate with these smart devices to make them even smarter and more interconnected. Example; my lights turn red at sunset automatically each day. This is actually a very exciting and new possibility which confers enormous [health benefits](https://www.healthline.com/nutrition/block-blue-light-to-sleep-better). With cheap commodity products and running no servers or custom hardware or software, I can easily create triggers in [IFTTT](https://ifttt.com) which pull the sunset time from weather services automatically, and then toggle my lights to red exactly at sunset each day. (Hopefully it goes without saying that sunset is at a different time each day.) Imagine trying to do this a decade ago. It would have been ridiculously complex. Just look at my Arduino [smart plug project](https://blog.cjtrowbridge.com/2017/09/06/i-made-six-smart-sockets-for-less-than-the-price-of-one-gfci-is-always-on-as-circuit-breakerarduino-ethernet-diy-maker-hacker-iot-smarthome-smartsocket/) for example, where I do it from relative scratch. # A Problem

There is one thing that still is not possible with any of the popular virtual assistants and smart home devices such as Google Home or Amazon Echo. I can talk to Google Home or Amazon Echo all day, and they are happy to acknowledge me and do whatever I ask of them. But there is absolutely no way to make them reach out to me in response to some external trigger. Example; my [Ring Doorbell](https://download.ring.com/ZH36WPgORM) detects motion in the front yard, and I have my phone on silent. I will not know until I next check my phone that motion was detected. There is absolutely no built-in way to make my army of virtual assistants notify me of something like this. I could buy [Ring's](https://download.ring.com/ZH36WPgORM) official plug-in chime (which I did) but this should not be necessary when I already have little computers in every room which should be able to just talk to me. Thinking about this problem gave me lots of other interesting ideas about things I would like to be notified about. For example problems at work, time-sensitive emails from teachers, or any number of potentially important issues. # A Solution

I have a whole box of [Raspberry Pi's](https://amzn.to/2rRmCqu) from old projects. With one simple command, I can make them say anything I want. I just need to install Say; ```
sudo apt-get install say
```

Then I created a [simple PHP script](https://github.com/cjtrowbridge/PHP-TTS-Webhooks/) which accepts webhooks and calls the say command. This is a little complicated to set up, but I have included all the directions on the [Github page](https://github.com/cjtrowbridge/PHP-TTS-Webhooks/). There is also a beta feature which saves the speech as an mp3 file, then casts it to the virtual assistants around the house. This means I can use IFTTT or other functional-paradigm cloud services to trigger my virtual assistants to speak to me based on external commands. It does mean I have to run a single piece of hardware; the Raspberry Pi. But I had to struggle to remember where I even plugged it in. It's hard to notice. There are all kinds of exciting directions this project can go in the future. There is no reason it shouldn't be able to cast tv shows or movies from my NAS for example. The potential of this product is very exciting. I look forward to future versions, and I think this is one of the few cases where the product will outlive my [Levels Challenge](https://blog.cjtrowbridge.com/2017/05/02/the-levels-challenge-start-12-startups-in-12-months/).