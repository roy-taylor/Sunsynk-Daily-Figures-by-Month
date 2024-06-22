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
import urllib3
import json
from datetime import date, datetime, timedelta 

# not the proper way to do things, but set to True for debugging
debugFlag = False
verifyTLS = True
http = urllib3.PoolManager()

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
# This function will fetch your bearer/access token, first looks for a 
# cached token in a file, if not found or expired then gets a new token
# 
# Sunsync modified their authentication API so frequent calls would be rejected
# so token is cached for reuse
#
# #############################################################################
def getBearerToken(username, password):

    # initialise variables, set expiry to the past in case cached value not found
    bearerTokenString = ""
    tokenExpiry = datetime.now() - timedelta(days=1)

    # #########################################################################
    # 
    #   Open the cache file, and retrieve values.  The exception will catch any 
    #   errors
    #   
    # #########################################################################
    try:
        with open('sunsyncApiToken.json', 'r') as openfile:
            apiTokenLoad = json.load(openfile)
            bearerTokenString = apiTokenLoad["bearerToken"]
            tokenExpiryStr = apiTokenLoad["expiryDate"]
            tokenExpiry = datetime.strptime(tokenExpiryStr, "%Y-%m-%d %H:%M:%S")
    except:
        if debugFlag:
            print("Token file not found")
            
    # #########################################################################
    # 
    #   Return token if it has not expired, otherwise get a new token
    #   
    # #########################################################################
    if tokenExpiry > datetime.now():
        return bearerTokenString
    else:
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
        r = urllib3.request("POST", loginEndpoint, json=payload, headers=headers).json()
        if debugFlag:
            print('****************************************************')
            print('Authentication Response: ')
            print(r)

        # Your access token extracted from response
        accessToken = r["data"]["access_token"]
        tokenExpiryPeriod = r["data"]["expires_in"]
        bearerTokenString = ('Bearer '+ accessToken)
        tokenExpiryDate = datetime.combine(date.today(), datetime.min.time()) + timedelta(seconds=tokenExpiryPeriod)
        tokenExpiryDateStr = tokenExpiryDate.strftime("%Y-%m-%d %H:%M:%S")

        # #########################################################################
        # 
        #   Save the token and expiry date to a cache file for the next run
        #   
        # #########################################################################
        with open("sunsyncApiToken.json", "w") as outfile:
            json.dump({'bearerToken': bearerTokenString, "expiryDate": tokenExpiryDateStr}, outfile)

        if debugFlag:
            print('****************************************************')
            print('Your access token is: ' + bearerTokenString)
            print("Your token expires in (secs)" + str(tokenExpiry))
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
#    r = requests.get(plantIdEndpoint, headers=headers_and_token)
#    r = requests.get(plantIdEndpoint, headers=headers_and_token, verify=verifyTLS)

    r = urllib3.request("GET", plantIdEndpoint, headers=headers_and_token)
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

#    r = requests.get(url, headers=headers_and_token)
#    r = requests.get(url, headers=headers_and_token, verify=verifyTLS)
    r = urllib3.request("GET", url, headers=headers_and_token)
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


