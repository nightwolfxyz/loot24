import os
import os.path
import requests
import json
import math
import time

BASE_URL = "https://api.vk.com/method/"

CONFIG = {}

deleted_users_count = 0
inactive_users_count = 0
online_users_count = 0
deactivated_users_count = 0

platform = {
    1: "mobile version", 
    2: "iPhone App", 
    3: "iPad App",
    4: "Android App", 
    5: "Windows Phone App", 
    6: "Windows 10 App",
    7: "full version of website"
    }

def Log(message):
    print(message)
    print()
    return 0

def ProcessGroupMembers(group_id):
    global CONFIG

    offset = 0
    count = 0
    url = BASE_URL + "groups.getMembers?group_id=" + str(group_id) + "&offset=" + str(offset) + "&count=" + str(count) + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
    Log(url)

    request = requests.get(url)
    time.sleep(1)
    content = request.content
    Log(content)
    response = json.loads(content)

    if ("response" not in response):
        return -1

    response_body = response["response"]
    number_of_group_members = response_body["count"]
    number_of_pages = math.ceil(number_of_group_members / CONFIG["PAGE_SIZE"])
    Log("Number of group members: " + str(number_of_group_members) + "\nNumber of pages: " + str(number_of_pages))

    for page_index in range(number_of_pages):
        offset = page_index * CONFIG["PAGE_SIZE"]
        count = CONFIG["PAGE_SIZE"]
        url = BASE_URL + "groups.getMembers?group_id=" + str(group_id) + "&offset=" + str(offset) + "&count=" + str(count) + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
        Log(url)
        request = requests.get(url)
        time.sleep(1)
        content = request.content
        Log(content)
        response = json.loads(content)
        if ("response" in response):
            response_body = response["response"]
            items = response_body["items"]
            result = ProcessUsers(items)
            if result < 0:
                return result
    return 0

def ProcessUsers(user_ids: list):
    global CONFIG
    global inactive_users_count
    global online_users_count
    global deactivated_users_count

    params = ""
    index = 0
    for user_id in user_ids:
        params = params + str(user_id)
        if (index < len(user_ids) - 1):
            params = params + ", "
        index = index + 1
    url = BASE_URL + "users.get?user_ids=" + params + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
    Log(url)
    request = requests.get(url)
    time.sleep(1)
    content = request.content
    Log(content)
    response = json.loads(content)
    Log(response)
    if "response" not in response:
        return -1
    response_body = response["response"]
    Log(response_body)
    for user in response_body:
        if "id" in user:
            # print("id in user") 
            if "deactivated" in user:
                print("deactivated in user")
                print("User with id " + str(user["id"]) + " is deactivated. Reason: " + str(user["deactivated"]) + ". Deleting from community...")
                deactivated_users_count += 1
                result = DeleteUser(user["id"])
                if result < 0:
                    return result
            if "online" in user:
                print("online in user")
                print("User with id " + str(user["id"]) + " is online: " + str(user["online"]) + ".")
                online_users_count += 1
            if "online_mobile" in user:
                print("online_mobile in user")
                print("User with id " + str(user["id"]) + " is online on mobile: " + str(user["online_mobile"]) + ".")
            if "online_app" in user:
                print("online_app in user")
                print("User with id " + str(user["id"]) + " is online on app: " + str(user["online_app"]) + ".")
            if "last_seen" in user:
                print("last_seen in user")
                last_seen = user["last_seen"]
                if "time" in last_seen:
                    print("time in last_seen, last_seen in user")
                    last_seen_time = last_seen["time"]
                    print("User with id " + str(user["id"]) + " was last seen at " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_seen_time)) + ".")
                if "platform" in last_seen:
                    print("platform in last_seen, last_seen in user")
                    last_seen_platform = last_seen["platform"]
                    print("User with id " + str(user["id"]) + " was last seen using " + platform.get(last_seen_platform, "unknown platform") + ".")
                if "time" in last_seen:
                    print("Again: time in last_seen, last_seen in user")
                    last_seen_time = last_seen["time"]
                    current_time = int(time.time())
                    inactive_period = current_time - last_seen_time
                    print("User's inactive period (seconds): " + str(inactive_period))
                    # Consider inactive if not seen for more than CONFIG["INACTIVE_PERIOD"] seconds
                    if inactive_period > CONFIG["INACTIVE_PERIOD"]:
                        print("inactive_period > CONFIG[\"INACTIVE_PERIOD\"]")
                        print("User with id " + str(user["id"]) + " is inactive for more than " + str(CONFIG["INACTIVE_PERIOD"]) + " seconds. Deleting from community...")
                        print()
                        inactive_users_count += 1
                        result = DeleteUser(user["id"])
                        if result < 0:
                            return result
    return 0

def DeleteUser(user_id):
    global CONFIG
    global deleted_users_count
    url = BASE_URL + "groups.removeUser?group_id=" + CONFIG["COMMUNITY_ID"] + "&user_id=" + str(user_id) + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
    Log(url)
    request = requests.get(url)
    time.sleep(1)
    content = request.content
    Log(content)
    response = json.loads(content)
    if "response" not in response:
        return -1
    response_body = response["response"]
    Log(response_body)
    deleted_users_count += 1
    return 0

def LoadConfig():
    global CONFIG
    config_fp = open("delete_inactive.conf", "r")
    config_content = config_fp.read()
    config_fp.close()
    CONFIG = json.loads(config_content)

def ReadConfig():
    global CONFIG

    if not os.path.exists("delete_inactive.conf"):
        print("ERROR: Configuration file is missing!")
        return -1

    with open("delete_inactive.conf", "r") as read_file:
        CONFIG = json.load(read_file)

    if "USER_ID" not in CONFIG:
        print("ERROR: USER_ID setting is missing!")
        return -1

    if "COMMUNITY_ID" not in CONFIG:
        print("ERROR: COMMUNITY_ID setting is missing!")
        return -1

    if "USER_ACCESS_TOKEN" not in CONFIG:
        print("ERROR: USER_ACCESS_TOKEN setting is missing!")
        return -1

    if "INACTIVE_PERIOD" not in CONFIG:
        print("ERROR: INACTIVE_PERIOD setting is missing!")
        return -1

    if "PAGE_SIZE" not in CONFIG:
        print("ERROR: PAGE_SIZE setting is missing!")
        return -1

    if "API_VERSION" not in CONFIG:
        print("ERROR: API_VERSION setting is missing!")
        return -1

    print("Configuration: ")
    Log(CONFIG)
    print("USER_ID: " + CONFIG["USER_ID"])
    print("COMMUNITY_ID: " + CONFIG["COMMUNITY_ID"])
    print("USER_ACCESS_TOKEN: " + CONFIG["USER_ACCESS_TOKEN"])
    print("INACTIVE_PERIOD: " + str(CONFIG["INACTIVE_PERIOD"]))
    print("PAGE_SIZE: " + str(CONFIG["PAGE_SIZE"]))
    print("API_VERSION: " + CONFIG["API_VERSION"])
    print()

    return 0

def LoadState():
    return 0

def SaveState():
    return 0

def main():
    result = ReadConfig()
    if result < 0:
        return result

    result = ProcessGroupMembers(CONFIG["COMMUNITY_ID"])

    print("Total users online: " + str(online_users_count) + "\n")
    print("Total deactivated users: " + str(deactivated_users_count) + "\n")
    print("Total inactive users: " + str(inactive_users_count) + "\n")
    print("Total deleted users: " + str(deleted_users_count) + "\n")

    return result

if __name__ == "__main__":
    main()