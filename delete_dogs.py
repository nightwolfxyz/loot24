import os
import os.path
import requests
import json
import math
import time

BASE_URL = "https://api.vk.com/method/"

CONFIG = {}

deleted_users_count = 0

def ProcessGroupMembers(group_id):
    global CONFIG

    offset = 0
    count = 0
    url = BASE_URL + "groups.getMembers?group_id=" + str(group_id) + "&offset=" + str(offset) + "&count=" + str(count) + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
    print(url)
    print()

    request = requests.get(url)
    time.sleep(1)
    content = request.content
    print(content)
    print()
    response = json.loads(content)

    if ("response" not in response):
        return -1

    response_body = response["response"]
    number_of_group_members = response_body["count"]
    number_of_pages = math.ceil(number_of_group_members / CONFIG["PAGE_SIZE"])
    print("Number of group members: " + str(number_of_group_members))
    print("Number of pages: " + str(number_of_pages))
    print()

    for page_index in range(number_of_pages):
        offset = page_index * CONFIG["PAGE_SIZE"]
        count = CONFIG["PAGE_SIZE"]
        url = BASE_URL + "groups.getMembers?group_id=" + str(group_id) + "&offset=" + str(offset) + "&count=" + str(count) + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
        print(url)
        print()
        request = requests.get(url)
        time.sleep(1)
        content = request.content
        print(content)
        print()
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
    params = ""
    index = 0
    for user_id in user_ids:
        params = params + str(user_id)
        if (index < len(user_ids) - 1):
            params = params + ", "
        index = index + 1
    url = BASE_URL + "users.get?user_ids=" + params + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
    print(url)
    print()
    request = requests.get(url)
    time.sleep(1)
    content = request.content
    print(content)
    print()
    response = json.loads(content)
    print(response)
    print()
    if "response" not in response:
        return -1
    response_body = response["response"]
    print(response_body)
    print()
    for user in response_body:
        if "id" in user and "deactivated" in user:
            print("User with id " + str(user["id"]) + " is deactivated. Reason: " + str(user["deactivated"]) + ". Deleting from community...")
            print()
            result = DeleteUser(user["id"])
            if result < 0:
                return result
    return 0

def DeleteUser(user_id):
    global CONFIG
    url = BASE_URL + "groups.removeUser?group_id=" + CONFIG["COMMUNITY_ID"] + "&user_id=" + str(user_id) + "&access_token=" + CONFIG["USER_ACCESS_TOKEN"] + "&v=" + CONFIG["API_VERSION"]
    print(url)
    print()
    request = requests.get(url)
    time.sleep(1)
    content = request.content
    print(content)
    print()
    response = json.loads(content)
    if "response" not in response:
        return -1
    response_body = response["response"]
    print(response_body)
    print()
    deleted_users_count += 1
    return 0

def LoadConfig():
    global CONFIG
    config_fp = open("delete_dogs.conf", "r")
    config_content = config_fp.read()
    config_fp.close()
    CONFIG = json.loads(config_content)

def ReadConfig():
    global CONFIG

    if not os.path.exists("delete_dogs.conf"):
        print("ERROR: Configuration file is missing!")
        return -1

    with open("delete_dogs.conf", "r") as read_file:
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

    if "PAGE_SIZE" not in CONFIG:
        print("ERROR: PAGE_SIZE setting is missing!")
        return -1

    if "API_VERSION" not in CONFIG:
        print("ERROR: API_VERSION setting is missing!")
        return -1

    print("Configuration: ")
    print(CONFIG)
    print()
    print("USER_ID: " + CONFIG["USER_ID"])
    print("COMMUNITY_ID: " + CONFIG["COMMUNITY_ID"])
    print("USER_ACCESS_TOKEN: " + CONFIG["USER_ACCESS_TOKEN"])
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

    print("Total deleted users: " + str(deleted_users_count))

    return result

if __name__ == "__main__":
    main()