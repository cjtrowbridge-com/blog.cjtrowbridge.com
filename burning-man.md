---
id: 14122
title: 'Burning Man'
date: '2021-05-12T14:57:05-07:00'
author: cjtrowbridge
layout: page
guid: 'https://blog.cjtrowbridge.com/?page_id=14122'
---

## Burning Man!

{% assign burn_category_names = '2026 Burn|2025 Burn|2020 Burn|2019 Burn|2018 Burn|2019 Burning Man|2018 Burning Man' | split: '|' %}
{% for cat_name in burn_category_names %}
  {% if site.categories[cat_name] %}
### {{ cat_name }}
  <ul>
    {% assign posts = site.categories[cat_name] | sort: 'date' | reverse %}
    {% for post in posts %}
      <li><a href="{{ post.url }}">{{ post.title }}</a></li>
    {% endfor %}
  </ul>
  {% endif %}
{% endfor %}
