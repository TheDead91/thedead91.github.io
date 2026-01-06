---
title: Santa's Gift-Tracking Service Port Mystery
author: thedead91
tags:
  - SANS Holiday Hack Challenge 2025
  - Holiday Hack Challenge
  - Holiday Hack Challenge 2025
  
  - Santa's Gift-Tracking Service Port Mystery
categories:
  - SANS Holiday Hack Challenge 2025
  - SANS Holiday Hack Challenge 2025 - Act I
date: 2026-01-06 00:03:00
description: Chat with Yori near the apartment building about Santa's mysterious gift tracker and unravel the holiday mystery.
---

# Santa's Gift-Tracking Service Port Mystery
Difficulty: <span style="color:red">❄</span> ❄ ❄ ❄ ❄  
Chat with Yori near the apartment building about Santa's mysterious gift tracker and unravel the holiday mystery.

## Hints
### Who is Netstat?
Back in my day...we just used Netstat. I hear `ss` is the new kid on the block. A lot of the parameters are the same too...such as listing only the ports that are currenting LISTENING on the system.
### Web Requests without a Browser??
Since we don't have a web browser to connect to this HTTP service...There is another common tool that you can use from the cli.

## motd
```bash
======= Neighborhood Santa-Tracking Service =======

Oh no! Mischievous gnomes have tampered with the neighborhood's Santa-tracking service,
built by the local tinkerer to help everyone know when Santa arrives on Christmas Eve!

The tracking application was originally configured to run on port 8080, but after the
gnomes' meddling, it's nowhere to be found. Without this tracker, nobody in the neighborhood
will know when to expect Santa's arrival!

The tinkerer needs your help to find out which port the santa_tracker process is 
currently using so the neighborhood tracking display can be updated before Christmas Eve!

Your task:
1. Use the 'ss' tool to identify which port the santa_tracker process is 
   listening on
2. Connect to that port to verify the service is running

Hint: The ss command can show you all listening TCP ports and the processes 
using them. Try: ss -tlnp

Good luck, and thank you for helping save the neighborhood's Christmas spirit!

- The Neighborhood Tinkerer 🔧🎄
```

## Solution
Following the `motd` instructions, I executed `ss -tlnp` to show listening ports:
```bash
🎄 tinkerer @ Santa Tracker ~ 🎅 $ ss -tlnp
State              Recv-Q             Send-Q                         Local Address:Port                           Peer Address:Port             Process             
LISTEN             0                  5                                    0.0.0.0:12321                               0.0.0.0:*        
```

Then connecting to `localhost:12321` solved the challenge:
```bash
🎄 tinkerer @ Santa Tracker ~ 🎅 $ curl localhost:12321
{
  "status": "success",
  "message": "\ud83c\udf84 Ho Ho Ho! Santa Tracker Successfully Connected! \ud83c\udf84",
  "santa_tracking_data": {
    "timestamp": "2025-11-05 20:51:12",
    "location": {
      "name": "Whoville Heights",
      "latitude": 57.861741,
      "longitude": -114.387588
    },
    "movement": {
      "speed": "875 mph",
      "altitude": "29363 feet",
      "heading": "244\u00b0 SE"
    },
    "delivery_stats": {
      "gifts_delivered": 1721597,
      "cookies_eaten": 33370,
      "milk_consumed": "4158 gallons",
      "last_stop": "Mistletoe Lane",
      "next_stop": "Frosty's Passage",
      "time_to_next_stop": "6 minutes"
    },
    "reindeer_status": {
      "rudolph_nose_brightness": "93%",
      "favorite_reindeer_joke": "What's Rudolph's favorite currency? Sleigh bells!",
      "reindeer_snack_preference": "magical carrots"
    },
    "weather_conditions": {
      "temperature": "-16\u00b0F",
      "condition": "Scattered cloud magic"
    },
    "special_note": "Thanks to your help finding the correct port, the neighborhood can now track Santa's arrival! The mischievous gnomes will be caught and will be put to work wrapping presents."
  }
}
```
