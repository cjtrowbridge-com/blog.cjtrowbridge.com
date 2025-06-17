---
id: 14209
title: 'round robin ipfs over http'
date: '2021-07-07T07:52:02-07:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=14209'
permalink: /2021/07/07/round-robin-ipfs-over-http/
categories:
    - Ideas
---

a web gateway protocol that automatically fetches the DNSLink for any c-name pointed at the server and then locally replicates that site and serves it when requested these could easily be round robined by adding redundant c-names to different gateways for your domain. The protocol could be limited to file types like html, css, js, jpeg, gif, png, etc. And it could have limited file sizes so that people are really using it just for their personal sites and profiles without trying to host apps on it or something like that. Larger files like mp4, mkv, etc could simply link to a public ipfs gateway instead of hosting locally. This is a good early-stage strategy for our-space which would make it fast and easy to access profiles without needing lots of bandwidth.