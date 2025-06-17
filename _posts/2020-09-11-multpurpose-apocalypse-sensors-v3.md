---
id: 13041
title: 'Multpurpose Apocalypse Sensors v3'
date: '2020-09-11T20:05:18-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=13041'
permalink: /2020/09/11/multpurpose-apocalypse-sensors-v3/
categories:
    - Featured
    - Projects
---

This is the third version of my apocalypse sensor array. The major change is a move to laser particulate matter sensors instead of infrared. ![Sensor Array](https://blog.cjtrowbridge.com/wp-content/uploads/2020/09/Sensor-Array-1-1.jpg)

## Current Hardware

- [MKR 1010](https://amzn.to/2RiGPCF): This is a really great microcontroller. It uses SAMD so it can be a little different to get things working instead of the traditional Arduino chips. Most example code needs some tweaks, but I've gotten everything working.
- Particulate Matter Sensors: 
    - [Laser Particulate Matter Sensor](https://amzn.to/3mgE3Mj): This is a great sensor. It measures particulate matter in several ranges. I am using the 0.1 micron, 2.5 micron, and 10 micron ranges for this sensor array.
    - [Infrared Particulate Matter Sensor](https://amzn.to/2ZxhjOv): This is terrible and I hate it.
- [Geiger Counter:](https://amzn.to/32nkaLV) This is self explanatory. The Geiger-Muller tube detects ionizing particles which intersect it.
- [DHT22 Sensor](https://amzn.to/2AQVKih): Gives temperature and humidity with high precision. I suspect that humidity in particular will have an impact on filter performance, or a relationship with spikes in smoke concentrations.

## Current Software

[Here is the repository](https://github.com/cjtrowbridge/Multipurpose-Apocalypse-Sensors). It contains separate files for each sensor, plus one to manage a slideshow on the LCD showing the data for all the sensors. It also includes a wifi file which serves a json object containing the current data from all the sensors. This data is updated automatically every thirty seconds. The reason for this delay is that some of the sensors do not necessarily succeed when polled and may need to be polled again several times. If we poll them when we get a web request, then it will take a long time to serve the request. My solution is to set up a series of buffer variables. On one side of that buffer, the wifi server listens and serves the values. On the other side, a loop continuously polls the sensors and updates the variables whenever possible. ## Methodology

I am tracking all the data from these sensors to look for interesting trends and data. I am also testing different methods of filtering the indoor air to make things as safe as possible inside during this latest disaster.