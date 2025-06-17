---
id: 13723
title: 'Data: Antivaxxer Prevalence Correlates With Covid Incidence'
date: '2020-12-01T21:12:52-08:00'
author: cjtrowbridge
layout: post
guid: 'https://blog.cjtrowbridge.com/?p=13723'
permalink: /2020/12/01/data-antivaxx-prevalence-correlates-with-covid-incidence/
categories:
    - Featured
    - 'USP493 Data Analysis'
tags:
    - 'Spicy Data'
---

CJ Trowbridge

USP 493 Data Analysis

2020-12-01

SPSS Final Project Outline

1. Introduction – what hypothesis you will test and why you expect your independent variable or variables will affect your dependent variable 
    - In the recent past, it was legal for California parents to refuse to vaccinate their children in on the basis of various superstitions. I hypothesize that there is a significant correlation between covid infection rates and the rates at which parents chose not to vaccinate their children before such decisions were banned. I am using counties as the unit of analysis to test this hypothesis.
2. Brief description of the data you will use 
    - There are several datasets that I will need to compile in order to test my hypothesis.
    - First, I need the covid case data by county. I am using the most recently published dataset from Johns Hopkins.
    - Second, I need the population for each county in order to calculate the percentage of the population that has become infected with covid. I am using the 2019 census population numbers.
    - Third, I need the kindergarten vaccination data from the year before the ban on exemptions happened. I got this from the California Department of Public Health Archives.
    -
3. Univariate statistics for each variable you will use in your hypothesis. Discussion of what these tables tell you. 
    - The kindergarten vaccination data for each county is my independent variable.
    - To get my dependent variable, I divide the covid infections by the population for each county in order to get the case incidence numbers for each county.
    - Here's what it all looks like put together;[![](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Data-1-1.png)](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Data-1-1.png)
4. Hypothesis testing. What do the statistics tell you. 
    - In order to visually compare the two values for each county, I first sorted the data by the independent variable's value. I then created a combo line-chart with two y-axes plus an x axis. The x axis in this chart is the county name. The dependent variable is on the second y-axis. Initially, the graph was not so clear to look at in SPSS. I asked the professor how to sort the x-axis by the value of the left y-axis but apparently that feature does not exist in SPSS...
    - [![](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/SPSS-Graph-1-1.png)](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/SPSS-Graph-1-1.png)
    - ...So I moved to Excel.
    - But first I ran the descriptive statistics in SPSS to find the minimum and maximum values for each variable in order to scale the axes so that the lines would be comparable as you see in the graph below.
    - [![](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Descriptives-1-1.png)](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Descriptives-1-1.png)
    - I then added trend lines to both y axes to simplify the visual representation of the data.
    - [![](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Graph-1-1.png)](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Graph-1-1.png)
    - Lastly, I ran a two-tailed Pearson Correlation at a .01 significance in SPSS to determine whether there is a significant correlation between the dependent and independent variables. The result was significant.
    - [![](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Correlations-1-1.png)](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Correlations-1-1.png)
5. Conclusion: Was your hypothesis supported? Implications of what you have found. 
    - The hypothesis is accepted. **There is a significant correlation between Kindergarten vaccination rates and covid infection rates by county**. As far as the possible implications, I will rely on this quote from Isaac Asimov, “There is a cult of ignorance in the United States, and there has always been. The strain of anti-intellectualism has been a constant thread winding its way through our political and cultural life, nurtured by the false notion that democracy means that 'my ignorance is just as good as your knowledge.”

## My Data Files

- [SPSS File](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/County-Project-1.rar)
- [Project](https://blog.cjtrowbridge.com/wp-content/uploads/2020/12/Project-1.xlsx)