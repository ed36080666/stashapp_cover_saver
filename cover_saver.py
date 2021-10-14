import base64
import json
from mimetypes import guess_extension
import os
import requests
import sys
import urllib
import urlparse

FRAGMENT = json.loads(sys.stdin.read())
FRAGMENT_SERVER = FRAGMENT["server_connection"]
FRAGMENT_SCENE_ID = FRAGMENT["args"]["hookContext"]["id"]
FRAGMENT_COVER_DATA = FRAGMENT["args"]["hookContext"]["input"]["cover_image"]

def printConsole(message):
    print(json.dumps({"output": message}))

def isUrl(str):
    return str[0:4] == "http"

# GraphQL functions taken from: https://github.com/stashapp/CommunityScripts/blob/52cc6cbfc212e6747cafee71eae2db55c669ddce/plugins/renamerOnUpdate/renamerOnUpdate.py#L65
def callGraphQL(query, variables=None):
    # Session cookie for authentication
    graphql_port = FRAGMENT_SERVER['Port']
    graphql_scheme = FRAGMENT_SERVER['Scheme']
    graphql_cookies = {
        'session': FRAGMENT_SERVER.get('SessionCookie').get('Value')
    }
    graphql_headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "DNT": "1"
    }
    if FRAGMENT_SERVER.get('Domain'):
        graphql_domain = FRAGMENT_SERVER['Domain']
    else:
        graphql_domain = 'localhost'
    # Stash GraphQL endpoint
    graphql_url = graphql_scheme + "://" + \
        graphql_domain + ":" + str(graphql_port) + "/graphql"

    json = {'query': query}
    if variables is not None:
        json['variables'] = variables
    response = requests.post(graphql_url, json=json,
                             headers=graphql_headers, cookies=graphql_cookies)
    if response.status_code == 200:
        result = response.json()
        if result.get("error"):
            for error in result["error"]["errors"]:
                raise Exception("GraphQL error: {}".format(error))
        if result.get("data"):
            return result.get("data")
    elif response.status_code == 401:
        sys.exit("HTTP Error 401, Unauthorised.")
    else:
        raise ConnectionError("GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(
            response.status_code, response.content, query, variables))

def findScene(scene_id):
    query = """
    query FindScene($id: ID!, $checksum: String) {
        findScene(id: $id, checksum: $checksum) {
            ...SceneData
        }
    }
    fragment SceneData on Scene {
        id
        oshash
        path
        phash
    }
    """
    variables = {
        "id": scene_id        
    }
    result = callGraphQL(query, variables)
    return result.get('findScene')

def writeFile(full_path, data):
    file_handle = open(full_path, "wb")
    file_handle.write(data)
    file_handle.close()



### Start Script ###

# if no cover data present, bail
if not FRAGMENT_COVER_DATA:
    printConsole("No cover image data found. Exiting...")
    sys.exit()

# retrieve scene to get filepath
scene = findScene(FRAGMENT_SCENE_ID)
scene_path, _ = os.path.splitext(scene["path"])

# check if an image exists for this file already
supported_extensions = ["jpg", "png", "jfif"]
image_found = False
for ext in supported_extensions:
    if os.path.exists(scene_path + "." + ext):
        image_found = True
        break

# todo config flag overwritting if exists?
if image_found:
    printConsole("Cover image already exists, skipping...")
    sys.exit()

else:
    if isUrl(FRAGMENT_COVER_DATA):
        url_path = urlparse.urlparse(FRAGMENT_COVER_DATA).path
        ext = os.path.splitext(url_path)[1]

        writeFile(scene_path + ext, requests.get(FRAGMENT_COVER_DATA).content)
    else:
        # split extension from a prefix like "data:image/jpeg;base64" (total hackjob)
        full_meta, b64data = FRAGMENT_COVER_DATA.split(',')
        img_type, encoding = full_meta.split(';')
        ext = img_type.split(':')[1].split('/')[1]

        writeFile(scene_path + "." + ext, base64.b64decode(b64data))

printConsole("New cover image saved at: " + scene_path)
sys.exit()

