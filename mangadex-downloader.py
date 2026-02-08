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
        print("could not find manga")
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

    titles = get_titles(manga_id)
    
    name_found = False

    for title in titles:
        if os.path.isdir(title):
            name_found = True 
            os.chdir(title)
    
    if not name_found:
        print("possible titles:")
        i = 0
        for title in titles:
            print("[" + str(i) + "] " + title)
            i += 1

        name = titles[int(input("number: "))]
        os.mkdir(name)
        os.chdir(name)
    


    if os.path.isdir(language):
        os.chdir(language)
    else:
        os.mkdir(language)
        os.chdir(language)

    if os.path.isdir(wanted_chapter):
        os.chdir(wanted_chapter)
    else:
        os.mkdir(wanted_chapter)
        os.chdir(wanted_chapter)

    i = 1
    amount = len(urls)
    for url in urls:
        print(f"\rProgress: {round((i/amount)*100)}%", end="", flush=True)
        page = requests.get(url).content
        name = str(i) + re.search(r"(\.(?:jpg|jpeg|png|gif|webp|bmp|svg))(?:\?.*)?$", url).group(1)
        path = os.path.join(os.getcwd(), name)
        f = open(path, 'wb')
        f.write(page)
        f.close()
        i += 1

def get_titles(manga_id):
    titles = []
    r = requests.get("https://api.mangadex.org/manga/" + manga_id)
    attributes = r.json()["data"]["attributes"]
    titles.extend(attributes["title"].values())
    for alt_title in attributes["altTitles"]:
        titles.extend(alt_title.values())

    return titles

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

UUID_REGEX = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

def is_uuid(value: str) -> bool:
    return bool(UUID_REGEX.match(value))

def choose_chapter(manga_id):
    possible_languages = []
    r = requests.get("https://api.mangadex.org/manga/" + manga_id)
    attributes = r.json()["data"]["attributes"]
    possible_languages.append(attributes["originalLanguage"])
    for lang in attributes["availableTranslatedLanguages"]:
        possible_languages.append(lang)
    print("possible_languages:")
    for lang in possible_languages:
        print(lang)
    global language
    language = input("language code(s) [en]: ")
    if language == '':
        language = "en"

    if not os.path.exists(os.path.join(script_dir, 'data' , language + manga_id + ".json")):
        base_url = "https://api.mangadex.org"
        r = requests.get(
            f"{base_url}/manga/{manga_id}/feed",
            params={"originalLanguage[]": [language]},             
            )
        if r.json()["data"] == []:
            r = requests.get(
                    f"{base_url}/manga/{manga_id}/feed",
                    params={"translatedLanguage[]": [language]},             
                    )
        # print(r.json()["data"])
        # title = str(r.json()["data"][0]["attributes"]["title"])
        # print(title)
        tags = []
        for tag in attributes["tags"]:
            tags.append(tag["attributes"]["name"])
        # print(tags)
        if "Oneshot" in tags:
            chapters = {"1.0": r.json()["data"][0]["id"]}
        else:
            chapters = {
                    float(chapter["attributes"]["chapter"]): chapter["id"]
                    for chapter in r.json()["data"]
                    }
        f = open(os.path.join(script_dir,'data', language + manga_id + ".json"), "at")
        f.write(json.dumps(chapters))
        f.close
    
    f = open(os.path.join(script_dir,'data', language + manga_id + ".json"), "rt")
    file_str = f.read()
    chapters = json.loads(file_str)
    f.close

    print("possible chapters:")
    chapter_list = []
    for i in chapters.keys():
        chapter_list.append(float(i))
    for i in sorted(chapter_list):
        print(i)

    global wanted_chapter
    wanted_chapter = str(float(input("chapter to download: ")))
    if wanted_chapter in chapters:
        return chapters[wanted_chapter] 
    else:
        print(f"'{wanted_chapter}' is not a chapter")
        exit(1)

if os.path.exists(os.path.join(script_dir, "info.json")):
    read_json()
else:
    auth()
    create_json()
    try:
        os.mkdir('data')
    except Exception as e:
        raise e

name = input("manga id or name: ")
if is_uuid(name):
    manga_id = name
else:
    r = requests.get(f"https://api.mangadex.org/manga", params={"title": name})
    if len(r.json()["data"]) > 1:
        i = 0
        for manga_name in r.json()["data"]:
            print(f"[{i}]" + manga_name["attributes"]["title"])
            i += 1
        manga_id = r.json()["data"][input("select number: ")]["id"]
    elif len(r.json()["data"]) < 1:
        print("didnt find anything with that name")
        exit(1)
    else:
        manga_id = r.json()["data"][0]["id"]

chapter_id = choose_chapter(manga_id)

get_images(chapter_id)
