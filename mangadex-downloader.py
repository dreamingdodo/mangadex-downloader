import requests
import re
import json
import os

username = ""
password = ""
client_id = ""
client_secret = ""
access_token = ""
refresh_token = ""
urls = []

script_dir = os.path.dirname(os.path.abspath(__file__))

def auth():
    global username
    global password 
    global client_id 
    global client_secret 

    username = input("Enter username: ")
    password = input("Enter password: ")
    client_id = input("Enter client_id: ")
    client_secret = input("Enter client_secret: ")


    auth_creds = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "client_id": client_id,
        "client_secret": client_secret
    }

    r = requests.post(
        "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token",
        data=auth_creds
    )
    r_json = r.json()

    global access_token 
    global refresh_token
    access_token = r_json["access_token"]
    refresh_token = r_json["refresh_token"]

def reauth():
    reauth_creds = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }

    r = requests.post(
        "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token",
        data=reauth_creds,
    )

    global access_token
    access_token = r.json()["access_token"]

def get_image_urls(chapter_id):
    url = "https://api.mangadex.org/at-home/server/" + str(chapter_id)
    r = requests.get(url)
    r_json = r.json()

    if r_json["result"] != "ok":
        return 1

    base_url = r_json["baseUrl"]
    chapter = r_json["chapter"]
    chapter_hash = chapter["hash"]
    chapter_data = chapter["data"]

    for i in chapter_data:
        url = str(base_url) + "/data/" + str(chapter_hash) + "/" + str(i)
        urls.append(url) 

    return urls

def get_images(chapter_id):
    urls = get_image_urls(chapter_id)
    if urls == 1: #TODO send report automatically
        exit(1)
    i = 1
    for url in urls:
        print(url)
        page = requests.get(url).content
        name = str(i) + re.search(r"(\.(?:jpg|jpeg|png|gif|webp|bmp|svg))(?:\?.*)?$", url).group(1)
        path = os.path.join(os.getcwd(), name)
        f = open(path, 'wb')
        f.write(page)
        f.close()
        i += 1


def create_json(): # i fully know how stupid this is
    refresh_requirments = {
            "refresh_token": str(refresh_token),
            "client_id": str(client_id),
            "client_secret": str(client_secret)
            }
    refresh_requirments_json = json.dumps(refresh_requirments) 

    f = open(os.path.join(script_dir, "info.json"), "at")
    f.write(refresh_requirments_json)
    f.close()

def read_json():
    f = open(os.path.join(script_dir, "info.json"), "rt")
    file_str = f.read()
    file_json = json.loads(file_str)
    global refresh_token
    global client_id
    global client_secret
    refresh_token = file_json["refresh_token"]
    client_id = file_json["client_id"]
    client_secret = file_json["client_secret"]
    f.close()

def choose_chapter(manga_id):
    if os.path.exists(os.path.join(script_dir, manga_id + ".json")):
        f = open(os.path.join(script_dir, manga_id + ".json"), "rt")
        file_str = f.read()
        chapters = json.loads(file_str)
        f.close
    else:
        base_url = "https://api.mangadex.org"
        language = [input("language code(s) [en]: ")]
        if language[0] == '':
            language = ["en"]
        r = requests.get(
                f"{base_url}/manga/{manga_id}/feed",
                params={"translatedLanguage[]": language},             
                )
        print(r.json())
        if r.json()["data"][0]["attributes"]["title"] != "Oneshot": 
            chapters = {
                    float(chapter["attributes"]["chapter"]): chapter["id"]
                    for chapter in r.json()["data"]
                    }
        else: # its a oneshot
            chapters = {"1.0": r.json()["data"][0]["id"]}
        f = open(os.path.join(script_dir, manga_id + ".json"), "at")
        f.write(json.dumps(chapters))
        f.close
    
    print("possible chapters:")
    chapter_list = []
    for i in chapters.keys():
        chapter_list.append(float(i))
    for i in sorted(chapter_list):
        print(i)

    wanted_chapter = str(float(input("chapter to download: ")))
    if wanted_chapter in chapters:
        return chapters[wanted_chapter] 
    else:
        print(f"'{wanted_chapter}'not a chapter")
        exit(1)

if os.path.exists(os.path.join(script_dir, "info.json")):
    read_json()
else:
    auth()
    create_json()

chapter_id = choose_chapter(input("manga id: "))

get_images(chapter_id)
