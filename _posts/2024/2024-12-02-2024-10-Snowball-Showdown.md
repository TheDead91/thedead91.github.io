---
title: Snowball Showdown
author: thedead91
tags:
  - SANS Holiday Hack Challenge 2024
  - Holiday Hack Challenge
  - Holiday Hack Challenge 2024
  - Snow-maggedon

  - act2
  
  - Snowball Showdown
  - Dusty Giftwrap
categories:
  - SANS Holiday Hack Challenge 2024  
  - SANS Holiday Hack Challenge 2024 - Act 2
date: 2024-12-02 10:00:00
description: Wombley has recruited many elves to his side for the great snowball fight we are about to wage. Please help us defeat him by hitting him with more snowballs than he does to us.
---

Difficulty: <span style="color:red">❄ ❄</span> ❄ ❄ ❄  
Wombley has recruited many elves to his side for the great snowball fight we are about to wage. Please help us defeat him by hitting him with more snowballs than he does to us.

## Silver trophy
### `singlePlayer=true`
Remembering the [Snowball Fight](https://github.com/LamonatoAndrea/HolidayHackChallenge2023_writeup/tree/main/02%20-%20Snowball%20Fight) challenge from Holiday Hack 2023, I quickly found the `singlePlayer = false` parameter in the url and changed it to `singlePlayer = true`. That allowed to play solo against Wombley.
### The lame solution
I forgot tha game open...and somehow when I noticed I already had the silver trophy... I guess my fellow snowballers did manage to beat Wombley :)
### The actual solution
Trying to alter parameters in different parts of [`phaser-snowball-game.js`](https://hhc24-snowballshowdown.holidayhackchallenge.com/js/phaser-snowball-game.js) I wasn't able to immediately tweak anything relevant aside from setting `this.throwRateOfFire = 1;` so to shoot faster. I then started analyzing the websocket messages being exchanged and I eventually noticed the message related to throwing a snowball:
```json
{
  "type": "snowballp",
  "x": 559,
  "y": 915.7559204101562,
  "owner": "d677f2bc-238b-41ef-9ffb-6c133d30c101",
  "isWomb": false,
  "blastRadius": 24,
  "velocityX": 445.01496716671596,
  "velocityY": -85.70936374799038
}
```
That `blastRadius` triggered my curiosity so I went ahed and ovverode it in `phaser-snowball-game.js` adding some `0`s value using developer tools:
![10_01_SnowballShowdown_blastRadius.png](/assets/img/posts/2024/2024-10-Snowball-Showdown/10_01_SnowballShowdown_blastRadius.png)
This trick basically destroyed the scenery, allowing to easily shoot Wombley while remaining in a safe zone and even behind the enemy lines:
<iframe width="100%" height="315" src="https://www.youtube.com/embed/LHvK-QOd5bY?si=sbGErMqVBsTQwVvo" title="Snowball Showdown - Silver trophy" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Gold trophy
While trying to figure out how to achieve the gold trophy, someone dropped a MOASB on my game...and then I knew what I was after 😊
![10_02_SnowballShowdown_MOASB-min-dwarf.png](/assets/img/posts/2024/2024-10-Snowball-Showdown/10_02_SnowballShowdown_MOASB-min-dwarf.png)

Looking for references to "moasb" I could find a function to send the message using ws:
```js
this.moasb = () => { this.ws.sendMessage({ type: 'moasb' }) }
```
At that point I thought "why should I shoot snowball if I can shoot MOASB?" and I modified the `phaser-snowball-game.js` again:
![10_03_SnowballShowdown_throwMoasb.png](/assets/img/posts/2024/2024-10-Snowball-Showdown/10_03_SnowballShowdown_throwMoasb.png)

Dropping a MOASB was a very interesting thing to do:
<iframe width="100%" height="315" src="https://www.youtube.com/embed/AsrxBEgVZl8?si=5Eq9pweJiA9cWVrF" title="Snowball Showdown - Gold trophy" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### What is a MOASB anyway? 
I actually didn't ask myself but I was pleasantly surprised when I spoke to Dusty Giftwrap again and he told me the meaning of MOASB: it's the ***'mother-of-all-snow-bombs'***.