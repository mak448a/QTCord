import os
import requests
import json
import platformdirs


api_base = "https://discord.com/api/v9"
auth = ""  # Will be overridden in load_token
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}


def load_token():
    global auth, headers
    if os.path.isfile(platformdirs.user_config_dir("QTCord") + "/discordauth.txt"):
        with open(platformdirs.user_config_dir("QTCord") + "/discordauth.txt") as f:
            auth = f.read()
        headers["authorization"] = auth


# Load token
load_token()


def get_messages(channel_id: int, limit: int = 100) -> list:
    """
    Returns messages from a given channel.
    Args:
        channel_id (int): The channel ID to request from
        limit (int): Amount of messages to request

    Returns:
        list: Messages from the specified channel.

    """
    r = requests.get(f"{api_base}/channels/{channel_id}/messages?limit={limit}", headers=headers)
    
    jsonn = json.loads(r.text)
    new_list = []

    if r.status_code != 200:
        new_list.append({"username": "System", "content": "Error. This may be a forum channel, or you're not allowed to view the content.", "id": 0})
        return new_list
    
    for value in jsonn:
        if not value["author"].get("global_name", False):
            author = value["author"]["username"]
        else:
            author = value["author"]["global_name"]
        if not value["content"]:
            new_list.append(
                {"username": author, "content": "[(call/image/other)]", "id": value["id"]})
        else:
            new_list.append(
                {"username": author, "content": value["content"], "id": value["id"]})

    # Reverse the list of messages
    new_list.reverse()
    return new_list


def send_message(msg, channel) -> None:
    """
    Sends a message to a given channel.
    Args:
        msg (str): Message
        channel (int): The channel to send the message

    Returns:
        None: Nothing

    """
    r = requests.post(f"{api_base}/channels/{channel}/messages",
                      headers=headers,
                      json={"content": msg})
    # print(r.text)


def get_friends() -> dict:
    """
    Returns a list of friends for the current account.
    Returns:
        dict: Friends of the current account
    """
    r = requests.get(f"{api_base}/users/@me/relationships",
                     headers=headers)

    # for friend in r.json():
    #     print(friend["user"]["global_name"])

    return r.json()


def get_channel_from_id(user_id: int) -> int:
    """
    Converts a user ID into a channel ID.
    Args:
        user_id (int): The user's ID

    Returns:
        int: The user's channel which they can be reached
    """
    r = requests.post(f"{api_base}/users/@me/channels",
                      headers=headers, json={"recipient_id": user_id})
    return r.json()["id"]


def get_guilds() -> dict:
    """
    Returns all guilds (aka servers) that the current user is in. Also downloads the icons of the servers.
    Returns:
        dict: Guilds that the current account is in.
    """

    r = requests.get(f"{api_base}/users/@me/guilds",
                     headers=headers)

    # TODO: You can get the icon of the server by: https://cdn.discordapp.com/icons/{id}/{icon_name}.
    # Icon name and id is in the icon.  
    # Make sure to handle blank icons!!!! they are set to none
    # You get the rest of the info from this function.
    for server in r.json():
        if os.path.exists(f"{platformdirs.user_cache_dir('QTCord')}/servers/{server['id']}.png"):
            continue
        
        # print(f"https://cdn.discordapp.com/icons/{server['id']}/{server['icon']}")
        server_icon = requests.get(f"https://cdn.discordapp.com/icons/{server['id']}/{server['icon']}")
        
        # Handle no image servers
        if server_icon.status_code == 404:
            continue
        
        if not os.path.exists(f"{platformdirs.user_cache_dir('QTCord')}/servers"):
            os.makedirs(f"{platformdirs.user_cache_dir('QTCord')}/servers")

        with open(f"{platformdirs.user_cache_dir('QTCord')}/servers/{server['id']}.png", "wb") as f:
            for chunk in server_icon.iter_content():
                f.write(chunk)
        
    # print(f"https://cdn.discordapp.com/icons/{r.json()[1]["id"]}/{r.json()[1]["icon"]}")
    return r.json()


def get_guild_channels(guild_id: int) -> dict:
    """
    Returns all channels in a guild.
    Args:
        guild_id (int): Any guild that the current user is in.

    Returns:
        dict: The channels in the guild.
    """

    r = requests.get(f"{api_base}/guilds/{guild_id}/channels",
                     headers=headers)

    return r.json()


def login(email: str, password: str, totp_code: str = ""):
    """
    Takes in an email and a password, logs in, and spits out a token.

    Args:
        email (str): Your email, e.g., example@example.com
        password (str): Your password for that account.

    Returns:
        str: Your token.
    """
    payload = {
        "login": email,
        "password": password,
        "undelete": False,
        "login_source": None,
        "gift_code_sku_id": None
    }

    r = requests.post(f"{api_base}/auth/login",
                      json=payload)

    # Check for errors
    if r.json().get("errors", False):
        return None

    # Return token if it succeeds, otherwise, return nothing.
    if r.json().get("token", False):
        return r.json()["token"]
    else:
        # If we have 2fa with totp
        if r.json().get("totp", False):
            totp_payload = {
                "ticket": r.json()["ticket"],
                "code": totp_code
            }

            res = requests.post(f"{api_base}/auth/mfa/totp", json=totp_payload)

            if res.status_code == 400:
                # If authentication was a failure
                return None
            else:
                # Else, we have our token!
                return res.json()["token"]
        else:
            print(
                "Error. You probably entered in your credentials wrong.\n"
                + "Or maybe you have SMS 2FA? SMS 2FA is not supported currently.\n"
                + "Ask for it at https://github.com/mak448a/QTCord/issues"
            )
            return None


def send_typing(channel: int):
    """
    Sends a typing indicator to a channel.
    Args:
        channel (int): The discord channel to send the typing indicator to

    Returns:
        None
    """
    
    requests.post(f"{api_base}/channels/{channel}/typing", headers=headers)
