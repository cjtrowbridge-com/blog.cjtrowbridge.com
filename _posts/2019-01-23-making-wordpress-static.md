---
id: 11472
title: 'Making WordPress Static'
date: '2019-01-23T13:55:53-08:00'
author: cjtrowbridge
layout: post
guid: 'https://admin.blog.cjtrowbridge.com/?p=11472'
permalink: /2019/01/23/making-wordpress-static/
categories:
    - Projects
---

Wordpress can be a nightmare. Don't get me wrong, Wordpress is great. BUT, there are often zero-day exploits, and a universe of complex security concerns which WILL come up. Combine that with the often ballooning resource requirements of templates, plugins, etc, and you get a recipe for a website that becomes a lot more complicated and expensive than it should be. The solution is actually quite simple; static. Many cache plugins exist which attempt to nudge Wordpress in that direction, but they don't really solve any of these problems. On the advice of Pieter Levels, I decided to split up my server architecture. The production sites such as blog.cjtrowbridge.com, cjtrowbridge.com, trowbridge.house, etc are all using static html running simply on apache with nothing else. Take a moment to really consider that. Apache is some of the fastest code ever written. A production server running just Apache has nearly unlimited capacity, especially when it's on an SSD in a datacenter somewhere. Most limitations and resource considerations are moot at that point, even for extremely high demand applications. A second server hosts wordpress installations for each corresponding site. These have a different url than the production sites. Whenever a change is made to a page, I simply deploy a new static version of the site onto the production server. This gives me all the benefits of wordpress with none of the security or resource concerns.

## Simply Static

Simply Static is a free Wordpress plugin. This will create a static copy of your entire wordpress site using relative paths for all links and resources. You just get an archive file which contains the whole site. You can also map the output to a directory which will automatically deploy directly to your production environment. (This would be a little more complicated.) ## Handling Bad URLs

The best solution I have found for handling bad URLs is simply to redirect any errors to the homepage via an htaccess file in the webroot. This still runs completely on apache while handling a complex task which wordpress would normally do. It might be more elegant to create a custom page for each error type. Then redirect each type of error to its own page. This sounds like a lot of unnecessary work in my case, but it would be great to include that kind of detail for a more complex or customer-facing site.