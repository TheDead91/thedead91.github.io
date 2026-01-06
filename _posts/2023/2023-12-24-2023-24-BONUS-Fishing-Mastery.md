---
title: BONUS! Fishing Mastery
author: thedead91
tags:
  - SANS Holiday Hack Challenge 2023
  - Holiday Hack Challenge
  - Holiday Hack Challenge 2023

  - BONUS! Fishing Mastery
  - Poinsettia McMittens
categories:
  - SANS Holiday Hack Challenge 2023
description: Catch at least one of each species of fish that live around Geese islands. When you're done, report your findings to Poinsettia McMittens.
date: 2023-12-24 00:00:00
---

## BONUS! Fishing Mastery
Difficulty: 🎄🎄🎄🎄  
Catch at least one of each species of fish that live around Geese islands. When you're done, report your findings to Poinsettia McMittens.

### Hints
#### I Am Become Data
*From: Poinsettia McMittens*
One approach to automating web tasks entails the browser's developer console. Browsers' console allow us to manipulate objects, inspect code, and even interact with [websockets](https://javascript.info/websocket).
#### Fishing Machine
*From: Poinsettia McMittens*
There are a variety of strategies for automating repetative website tasks. Tools such as [AutoKey](https://github.com/autokey/autokey) and [AutoIt](https://www.autoitscript.com/site/) allow you to programmatically examine elements on the screen and emulate user inputs.

### Solution
I let my script run for quite a while but I wasn’t able to obtain all the fish, so I looked at the images I downloaded from [https://2023.holidayhackchallenge.com/sea/fishdensityref.html](https://2023.holidayhackchallenge.com/sea/fishdensityref.html). I understood that white gradient in the image would indicate where a fish could be found. I started overlapping the density with the [minimap](https://2023.holidayhackchallenge.com/sea/assets/minimap.png) and thought about automating the whole process of moving & catching for each fish. When doing that I noticed the Piscis Cyberneticus Skodo having a really narrow catching area that can be seen in white in the image below:  
![minimap_PiscisCyberneticusSkodo_overlay](/assets/static/posts/2023/2023-24-BONUS-Fishing-Mastery/minimap_PiscisCyberneticusSkodo_overlay.png)

While working on a new version, I let my old script run with the boat in the fishing area for the Piscis Cyberneticus Skodo. Eventually the night passed and I woke up having all 171 fish. The Piscis itself was catched #170 and the last one was actually a Whiskered Jumblefish 🙂