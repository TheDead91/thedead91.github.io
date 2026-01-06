---
title: Visual Firewall Thinger
author: thedead91
tags:
  - SANS Holiday Hack Challenge 2025
  - Holiday Hack Challenge
  - Holiday Hack Challenge 2025
  
  - Visual Firewall Thinger
categories:
  - SANS Holiday Hack Challenge 2025
  - SANS Holiday Hack Challenge 2025 - Act I
date: 2026-01-06 00:05:00
description: Find Elgee in the big hotel for a firewall frolic and some techy fun.
---

# Visual Firewall Thinger
Difficulty: <span style="color:red">❄</span> ❄ ❄ ❄ ❄  
Find Elgee in the big hotel for a firewall frolic and some techy fun.

## Hints
### Visual Firewall Thinger
This terminal has built-in hints!

## Solution
### The network
![2025-05-Visual-Firewall-Thinger-06](/assets/static/posts/2025/2025-05-Visual-Firewall-Thinger/2025-05-Visual-Firewall-Thinger-06.png)
### The firewall rules
- Internet to DMZ: Allow only HTTP and HTTPS traffic
![2025-05-Visual-Firewall-Thinger-01](/assets/static/posts/2025/2025-05-Visual-Firewall-Thinger/2025-05-Visual-Firewall-Thinger-01.png)
- DMZ to Internal: Allow HTTP, HTTPS, and SSH traffic
![2025-05-Visual-Firewall-Thinger-02](/assets/static/posts/2025/2025-05-Visual-Firewall-Thinger/2025-05-Visual-Firewall-Thinger-02.png)
- Internal to DMZ: Allow HTTP, HTTPS, and SSH traffic
![2025-05-Visual-Firewall-Thinger-03](/assets/static/posts/2025/2025-05-Visual-Firewall-Thinger/2025-05-Visual-Firewall-Thinger-03.png)
- Internal to Cloud: Allow HTTP, HTTPS, SSH, and SMTP traffic
![2025-05-Visual-Firewall-Thinger-04](/assets/static/posts/2025/2025-05-Visual-Firewall-Thinger/2025-05-Visual-Firewall-Thinger-04.png)
- Internal to Workstations: Allow all traffic types
![2025-05-Visual-Firewall-Thinger-05](/assets/static/posts/2025/2025-05-Visual-Firewall-Thinger/2025-05-Visual-Firewall-Thinger-05.png)
- Security Best Practice: Block direct Internet to Internal access  
Already compliant