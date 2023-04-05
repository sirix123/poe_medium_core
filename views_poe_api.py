import os
import time
import requests
from datetime import datetime

from app.models.model import *
from . import scripts

@scripts.route('/get-poe-account-character-data/<key>')
def index(key):
    if key != os.environ.get('SECRET_KEY'):
        return 'Invalid key'
    
    death_messages = DiscordDeathMessages.retrieve_discord_death_messages()
    if death_messages:
        for death_message in death_messages:
            if datetime.now() >= DiscordDeathMessages.get_discord_death_message_api_interval_date(death_message.message_id) and datetime.now() >= DiscordDeathMessages.get_discord_death_message_retry_after_date(death_message.message_id):
                send_discord_death_message(death_message)
            else:
                continue
    
    cheater_messages = DiscordCheatMessages.retrieve_discord_cheat_messages()
    if cheater_messages:
        for cheater_message in cheater_messages:
            if datetime.now() >= DiscordCheatMessages.get_discord_cheat_message_api_interval_date(cheater_message.message_id) and datetime.now() >= DiscordCheatMessages.get_discord_cheat_message_retry_after_date(cheater_message.message_id):
                send_discord_cheat_message(cheater_message)
            else:
                continue

    accounts = UserOG.retrieve_poe_accounts()
    for user in accounts:

        if user.access_token == None:
            continue

        url_profile = 'https://api.pathofexile.com/character'
        headers = {
            'Authorization': 'Bearer ' + user.access_token,
            'User-Agent': 'OAuth ' + os.environ.get('OAUTH_CREDENTIALS_ID') + '/1.0.0 (contact: stefan@sdgames.co) StrictMode'
        }

        if datetime.now() >= UserOG.get_interval_time(user.username) and datetime.now() >= UserOG.get_retry_time(user.username):
            response_character = requests.get(url_profile, headers=headers)
        else:
            continue

        headers_response = response_character.headers

        max_hits = 0
        current_hits = 0
        period = 0
        rule_1_retry_time_after_max_hits = 0

        if "X-Rate-Limit-Account" in headers_response:
            rate_chunks = headers_response['X-Rate-Limit-Account'].split(',')
            chunks_1 = rate_chunks[0].split(':') # rule 1
            max_hits = int(chunks_1[0])
            period = int(chunks_1[1])
            rule_1_retry_time_after_max_hits = period = int(chunks_1[2])
            UserOG.set_interval_time(user.username, period)

        if "X-Rate-Limit-Account-State" in headers_response:
            rate_chunks = headers_response['X-Rate-Limit-Account-State'].split(',')
            chunks_1 = rate_chunks[0].split(':') # rule 1
            current_hits = int(chunks_1[0])
            if current_hits >= max_hits:
                UserOG.set_interval_time(user.username, rule_1_retry_time_after_max_hits)
                print("--")
                continue
            UserOG.set_interval_time(user.username, period)

        if response_character.status_code == 401:
            print("invalid token for " + user.username + "error " + url_profile + " " + str(response_character.status_code))
            UserOG.remove_access_token_for_user(user.username)
            print("--")
            continue

        # log the timestamp retry headerr + current time
        if response_character.status_code == 429:
            headers_response = response_character.headers
            print("retry after " + str(int(headers_response['Retry-After'])) + " for user " + user.username)
            print("--")
            UserOG.set_retry_time(user.username, int(headers_response['Retry-After']))
            continue

        if response_character.status_code != 200:
            print(user.username + " error2 " + url_profile + " " + str(response_character.status_code))
            print("--")
            return 'Error ' + str(response_character.status_code)

        character_data = response_character.json()
        account = user.username

        for character in character_data['characters']:
            character_name = character['name']
            level = character['level']
            league = character['league']
            class_poe = character['class']
            experience = character['experience']

            if Character.does_character_already_exist(character_name):
                if league == os.environ.get('POE_MEDIUM_CORE_LEAGUE_NAME') and level >= 71 :
                    populate_item_database(character_name, url_profile, headers, user.username)
                    if Character.get_character_last_known_xp(character_name) > character['experience']:
                        Character.increase_character_death_count(character_name)
                        create_death_message_in_database(character_name)

            if Character.does_character_already_exist(character_name):
                Character.if_character_already_exists_update_fields(account, character_name, level, experience, class_poe)
                continue

            Character.create_character_entry(account, character_name, level, league, experience, class_poe)
            continue

    return 'Success'

def populate_item_database(characterName, url_profile, headers, userName):
    url_profile_details = url_profile + '/' + characterName

    if datetime.now() >= Character.get_retry_time_character_details(characterName) and datetime.now() >= Character.get_interval_time_character(characterName):
        response_character_details = requests.get(url_profile_details, headers=headers)
    else:
        return
    
    max_hits = 0
    current_hits = 0
    period = 0
    rule_1_retry_time_after_max_hits = 0

    if "X-Rate-Limit-Account" in response_character_details.headers:
        rate_chunks = response_character_details.headers['X-Rate-Limit-Account'].split(',')
        chunks_1 = rate_chunks[0].split(':') # rule 1
        max_hits = int(chunks_1[0])
        period = int(chunks_1[1])
        rule_1_retry_time_after_max_hits = int(chunks_1[2])
        Character.set_interval_time_character(characterName, period)

    if "X-Rate-Limit-Account-State" in response_character_details.headers:
        rate_chunks = response_character_details.headers['X-Rate-Limit-Account-State'].split(',')
        chunks_1 = rate_chunks[0].split(':') # rule 1
        current_hits = int(chunks_1[0])
        if current_hits >= max_hits:
            Character.set_all_characters_by_account_interval_time(userName, rule_1_retry_time_after_max_hits + period)
            return
        Character.set_interval_time_character(characterName, period)

    if response_character_details.status_code == 429:
        headers = response_character_details.headers
        if 'Retry-After' in headers:
            print(characterName +  " char details retry after " + str(int(headers['Retry-After'])) + " for characterName " + characterName)
            Character.set_all_characters_by_account_interval_time(userName, int(headers['Retry-After']))
        return

    if response_character_details.status_code != 200:
        print("error " + url_profile_details + " " + str(response_character_details.status_code))
        return 'Error ' + str(response_character_details.status_code)

    character_data_details = response_character_details.json()

    if CharacterEquipment.does_character_already_exist(characterName):
        for item in character_data_details['character']['equipment']:

            if DeletedItems.is_item_present_in_deleted_table(item['id']):
                itemData = Item.get_item_name(characterName, item['id'])
                create_discord_cheater_message(characterName, itemData)

            CharacterEquipment.update_equipment_slot(characterName, item['inventoryId'], item['id'])

            itemMods = "Item mods"

            if "explicitMods" in item:
                for explicitMod in item['explicitMods']:
                    itemMods = itemMods + ", " + explicitMod

            if "craftedMods" in item:
                for craftedMod in item['craftedMods']:
                    itemMods = itemMods + ", " + craftedMod

            if "fracturedMods" in item:
                for fracturedMod in item['fracturedMods']:
                    itemMods = itemMods + ", " + fracturedMod

            if "implicitMods" in item:
                for implicitMod in item['implicitMods']:
                    itemMods = itemMods + ", " + implicitMod

            if "utilityMods" in item:
                for utilityMod in item['utilityMods']:
                    itemMods = itemMods + ", " + utilityMod

            if "enchantMods" in item:
                for enchantMod in item['enchantMods']:
                    itemMods = itemMods + ", " + enchantMod

            if "crucibleMods" in item:
                for crucibleMod in item['crucibleMods']:
                    itemMods = itemMods + ", " + crucibleMod

            create_item_in_item_database(characterName, item['id'], itemMods, item['name'], item['inventoryId'])

    else:
        CharacterEquipment.create_character_entry(characterName)
        for item in character_data_details['character']['equipment']:

            CharacterEquipment.update_equipment_slot(characterName, item['inventoryId'], item['id'])

            itemMods = "Item mods"

            if "explicitMods" in item:
                for explicitMod in item['explicitMods']:
                    itemMods = itemMods + ", " + explicitMod

            if "craftedMods" in item:
                for craftedMod in item['craftedMods']:
                    itemMods = itemMods + ", " + craftedMod

            if "fracturedMods" in item:
                for fracturedMod in item['fracturedMods']:
                    itemMods = itemMods + ", " + fracturedMod

            if "implicitMods" in item:
                for implicitMod in item['implicitMods']:
                    itemMods = itemMods + ", " + implicitMod

            if "utilityMods" in item:
                for utilityMod in item['utilityMods']:
                    itemMods = itemMods + ", " + utilityMod

            if "enchantMods" in item:
                for enchantMod in item['enchantMods']:
                    itemMods = itemMods + ", " + enchantMod

            if "crucibleMods" in item:
                for crucibleMod in item['crucibleMods']:
                    itemMods = itemMods + ", " + crucibleMod

            create_item_in_item_database(characterName, item['id'], itemMods, item['name'], item['inventoryId'])

def create_item_in_item_database(characterName, itemGuid, itemMods, itemName, item_slot):
    if not Item.does_item_already_exist(characterName, itemGuid):
        Item.create_item_entry(characterName, itemGuid, itemMods, itemName, item_slot)
    else:
        Item.update_item_entry(characterName, itemGuid, itemMods, itemName, item_slot)

def create_death_message_in_database(characterName):
    quotes = [
        "Did the earth move for you, baby? Probably, you hit the ground quite hard.",
        "There is a fine line between consideration and hesitation. The former is wisdom, the latter is fear.",
        "Don't be frightened, little mountain. It'll all be over soon.",
        "This world is an illusion, exile.",
        "Poor fish wife",
        "Your crime is trespass. Your sentence is death.",
        "OOoooOOoooOOOoohh the weary traveler draws close to the end of the path",
        "Touch of God!",
        "The Light of Divinity!",
        "Still sane, exile?",
        "Why are you so in love with death",
        "Life is too precious to waste on you!"
        ]

    item_to_destroy = CharacterEquipment.get_random_equipped_item(characterName)

    death_message = ""
    if item_to_destroy == "No item found!" or item_to_destroy == None:
        death_message = characterName + " has died but isn't wearing any items!"
    else:
        DeletedItems.create_deleted_item_entry(item_to_destroy)
        death_message = Item.get_item_data(characterName, item_to_destroy) + "\n"

    quote = quotes[random.randint(0, len(quotes) - 1)]
    death_message = " **" + quote + "** " + "\n" + death_message

    DiscordDeathMessages.create_discord_death_message_entry(death_message)


def create_discord_cheater_message(characterName, itemName):
    cheater_message =  characterName + " is cheating " + " by wearing a deleted item: " + itemName
    DiscordCheatMessages.create_discord_cheat_message_entry(cheater_message)
    
def send_discord_death_message(death_message_list):
    url_profile = 'https://discord.com/api/v10/channels/684192893312827459/messages'
    
    body = {
        'content': death_message_list.message
    }

    header = {
        'Authorization': 'Bot ' + os.environ.get('DISCORD_BOT_TOKEN'),
        'Content-Type': 'application/json',
        'User-Agent': 'SDGamesBot (https://github.com/sirix123/sd-games-web-app, 1.0.0)'
    }

    response = requests.post(url_profile, json=body, headers=header)

    if "X-RateLimit-Remaining" in response.headers:
        # print("discod X-RateLimit-Remaining " + response.headers["X-RateLimit-Remaining"])
        if response.headers["X-RateLimit-Remaining"] == "0":
            # print("discord X-RateLimit-Remaining is 0")
            return

    if response.status_code == 429:
        headers = response.headers
        if 'retry_after' in headers:
            print("discord send death message details retry after " + str(int(headers['retry_after'])))
            DiscordDeathMessages.update_discord_death_message_retry_after_date(death_message_list.message_id,int(headers['retry_after']))
        return

    if response.status_code != 200:
        print("error " + url_profile + " " + str(response.status_code))
        return 'Error ' + str(response.status_code)
    
def send_discord_cheat_message(cheat_message_list):
    url_profile = 'https://discord.com/api/v10/channels/684192893312827459/messages'

    body = {
        'content': cheat_message_list.message
    }

    header = {
        'Authorization': 'Bot ' + os.environ.get('DISCORD_BOT_TOKEN'),
        'Content-Type': 'application/json',
        'User-Agent': 'SDGamesBot (https://github.com/sirix123/sd-games-web-app, 1.0.0)'
    }

    response = requests.post(url_profile, json=body, headers=header)

    if "X-RateLimit-Remaining" in response.headers:
        print("discod X-RateLimit-Remaining " + response.headers["X-RateLimit-Remaining"])
        if response.headers["X-RateLimit-Remaining"] == "0":
            # print("discord X-RateLimit-Remaining is 0")
            return

    if response.status_code == 429:
        headers = response.headers
        if 'retry_after' in headers:
            print("discord cheater send death message details retry after " + str(int(headers['retry_after'])))
            DiscordCheatMessages.update_discord_death_message_retry_after_date(cheat_message_list.message_id,int(headers['retry_after']))
        return

    if response.status_code != 200:
        print("error " + url_profile + " " + str(response.status_code))
        return 'Error ' + str(response.status_code)