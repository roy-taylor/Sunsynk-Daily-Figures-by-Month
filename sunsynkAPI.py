# #############################################################################
#   Library of functions to connect to the SunSync API and retrieve
#   Daily figures by month
# 
#   Thanks to https://github.com/AsTheSeaRises/SunSynk_API for showing how to
#   connect to the API
#   Sunsynk API calls were found using the network view in browser development 
#   tools
# #############################################################################

import sys
import requests
import json
from requests.auth import HTTPBasicAuth

# not the proper way to do things, but set to True for debugging
debugFlag = False

# #############################################################################
#
#   URLs to access Sunsynk API
#       login:                          https://pv.inteless.com/oauth/token
#       plantId:                        https://pv.inteless.com/api/v1/plants?page=1&limit=10&name=&status=
#       monthy stats by day:            https://pv.inteless.com/api/v1/plant/energy/<plantId>/month?lan=en&date=<YYYY-MM&id=<plantId>
#       daily stats by 5 min interval:  https://pv.inteless.com/api/v1/plant/energy/<plantId>/day?lan=en&date=<YYYY-MM-DD&id=<plantId>
#
# #############################################################################

# loginEndpoint = ('https://pv.inteless.com/oauth/token')
# plantIdEndpoint = ('https://pv.inteless.com/api/v1/plants?page=1&limit=10&name=&status=')
# statsEndpoint = ('https://pv.inteless.com/api/v1/plant/energy/')

loginEndpoint = ('https://api.sunsynk.net/oauth/token')
plantIdEndpoint = ('https://api.sunsynk.net/api/v1/plants?page=1&limit=10&name=&status=')
statsEndpoint = ('https://api.sunsynk.net/api/v1/plant/energy/')

# #############################################################################
#
# This function will print your bearer/access token
#
# #############################################################################
def getBearerToken(username, password):
    headers = {
    'Content-type':'application/json', 
    'Accept':'application/json'
    }

    payload = {
        "username": username,
        "password": password,
        "grant_type":"password",
        "client_id":"csp-web"
        }
    r = requests.post(loginEndpoint, json=payload, headers=headers).json()
    # Your access token extracted from response
    accessToken = r["data"]["access_token"]
    bearerTokenString = ('Bearer '+ accessToken)
    if debugFlag:
        print('****************************************************')
        print('Your access token is: ' + bearerTokenString)
    return bearerTokenString

# #############################################################################
#
# Get plant id
# Note, if you have multiple plant Ids it will return the last one 
#
# #############################################################################
def getPlantId(bearerToken):
    headers_and_token = {
    'Content-type':'application/json', 
    'Accept':'application/json',
    'Authorization': bearerToken
    }
    if debugFlag:
        print ('Request endpoint:', plantIdEndpoint)
        print ('Headers: ', headers_and_token)
    r = requests.get(plantIdEndpoint, headers=headers_and_token)
    data_response = r.json()
    if debugFlag:
        print ('Response: ', json.dumps(data_response, indent = 4) )
        print ('****************************************************')
    plant_id_and_pac = data_response['data']['infos']
    for d in plant_id_and_pac:
        plantId = d['id']
        if debugFlag:
            print('Your plant id is: ' + str(plantId))
            print('****************************************************')
    return str(plantId)

# #############################################################################
#
# Get stats for the month
#   bearerToken:    authentication/authorisation for the API call
#   plantId:        palntId is used in the URL to get readings
#   month:          month stats are wanted for in YYYY-MM fornmat.  Format isn't 
#                   checked, invalid format will either cause an error or null return
#
# #############################################################################
def getMonthlyStats(bearerToken, plantId, month):
    headers_and_token = {
    'Content-type':'application/json', 
    'Accept':'application/json',
    'Authorization': bearerToken
    }
    url = "".join([statsEndpoint, plantId, "/month?lan=en&date=", month, "&id=99741"])
    if debugFlag:
        print ('Request endpoint:', statsEndpoint)
        print ('Headers: ', headers_and_token)
        print(url)
        print('https://pv.inteless.com/api/v1/plant/energy/99741/month?lan=en&date=2023-08&id=99741')

    r = requests.get(url, headers=headers_and_token)
    data_response = r.json()
    if debugFlag:
        print ('Response: ', json.dumps(data_response, indent = 4) )
        print('****************************************************\n')

    # #########################################################################
    #
    #   Build a Dictionary of readings by day
    #
    # #########################################################################
    readingsByDay = {}
    readings = data_response['data']['infos']
    for r in readings:
        for d in r['records']:
            if d['time'] not in readingsByDay:
                readingsByDay[d['time']] = {}
            readingsByDay[d['time']][r['label']] = d['value']

    if debugFlag:
        print(json.dumps(readingsByDay, indent = 4) )
    return readingsByDay


