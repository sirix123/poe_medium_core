from passlib.hash import sha256_crypt
from better_profanity import profanity
from datetime import datetime, timedelta
import random
import typing as t
from app import db

class UserOG(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=True)
    code = db.Column(db.String(256), nullable=True)
    access_token = db.Column(db.String(256), nullable=True)
    refresh_token = db.Column(db.String(256), nullable=True)
    retry_after_date = db.Column(db.DateTime, nullable=False)
    api_interval_date = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return '<User %r>' % self.username

    @classmethod
    def retrieve_poe_accounts(cls):
        return cls.query.all()

    @classmethod
    def check_og_poe_userbase(cls, username) -> bool:
        _ = cls.query.filter_by(username=username).first()
        if _:
            return True
        return False

    @classmethod
    def create_og_poe_user(cls, username, access_token) -> None:
        _ = cls(username=username, access_token=access_token, retry_after_date=datetime.now(), api_interval_date=datetime.now())
        db.session.add(_)
        db.session.commit()

    @classmethod
    def update_access_token_for_user(cls, username, access_token) -> None:
        _ = cls.query.filter_by(username=username).first()
        _.access_token = access_token
        db.session.commit()

    @classmethod
    def remove_access_token_for_user(cls, username) -> None:
        _ = cls.query.filter_by(username=username).first()
        _.access_token = None
        db.session.commit()

    @classmethod
    def set_retry_time(cls, username, retry_after) -> None:
        _ = cls.query.filter_by(username=username).first()
        now = datetime.now()
        _.retry_after_date = now + timedelta(seconds=retry_after)
        db.session.add(_)
        db.session.commit()

    @classmethod
    def get_retry_time(cls, username) -> None:
        _ = cls.query.filter_by(username=username).first()
        if _:
            return _.retry_after_date

    @classmethod
    def set_interval_time(cls, username, interval_time) -> None:
        _ = cls.query.filter_by(username=username).first()
        now = datetime.now()
        _.api_interval_date = now + timedelta(seconds=interval_time)
        db.session.add(_)
        db.session.commit()

    @classmethod
    def get_interval_time(cls, username) -> None:
        _ = cls.query.filter_by(username=username).first()
        if _:
            return _.api_interval_date

class Character(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(50), nullable=False)
    character_name = db.Column(db.String(50), nullable=False)
    class_poe = db.Column(db.String(50))
    clean_character_name = db.Column(db.String(50))
    level = db.Column(db.Integer, nullable=False)
    experience = db.Column(db.Integer, nullable=True)
    league = db.Column(db.String(50), nullable=False)
    retry_after_date_character_details = db.Column(db.DateTime, nullable=False)
    character_api_interval_date = db.Column(db.DateTime, nullable=False)
    deaths = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Character %r>' % self.character

    @classmethod
    def retrieve_character_entries(cls):
        return cls.query.all()

    @classmethod
    def does_character_already_exist(cls, character_name) -> bool:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            return True
        return False

    @classmethod
    def create_character_entry(
            cls,
            account, character_name, level, league, experience, class_poe
    ) -> None:
        _ = cls(
            account=account,
            character_name=character_name,
            level=level,
            league=league,
            experience=experience,
            class_poe=class_poe,
            retry_after_date_character_details=datetime.now(),
            character_api_interval_date=datetime.now(),
            deaths=0
        )
        if _.clean_character_name == None:
            if detect_profanity(character_name) or _.account == 'Nizcoer' or _.account == 'skiliev' or _.account == 'Marcjr':
                _.clean_character_name = clean_name()
            else:
                _.clean_character_name = character_name
        db.session.add(_)
        db.session.commit()

    @classmethod
    def if_character_already_exists_update_fields(
            cls,
            account, character_name, level, experience, class_poe
    ) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            if _.clean_character_name == None::
                _.clean_character_name = character_name

            _.level = level
            _.experience = experience
            _.class_poe = class_poe
            db.session.add(_)
            db.session.commit()

    @classmethod
    def get_character_last_known_xp(
            cls,
            character_name
    ) -> int:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            return _.experience

    @classmethod
    def get_character_level(cls, character_name) -> int:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            return _.level

    @classmethod
    def set_retry_time_character_details(cls, character_name, retry_after) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        now = datetime.now()
        _.retry_after_date_character_details = now + timedelta(seconds=retry_after)
        db.session.add(_)
        db.session.commit()

    @classmethod
    def get_retry_time_character_details(cls, character_name) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            return _.retry_after_date_character_details
        
    @classmethod
    def set_interval_time_character(cls, character_name, interval_time) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        now = datetime.now()
        _.character_api_interval_date = now + timedelta(seconds=interval_time)
        db.session.add(_)
        db.session.commit()

    @classmethod
    def get_interval_time_character(cls, character_name) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            return _.character_api_interval_date
        
    @classmethod
    def increase_character_death_count(cls, character_name) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        _.deaths = _.deaths + 1
        db.session.add(_)
        db.session.commit()

    @classmethod
    def get_character_deaths(cls, character_name) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            return _.deaths
        
    @classmethod
    def set_all_characters_by_account_interval_time(cls, account, interval_time) -> None:
        _ = cls.query.filter_by(account=account).all()
        now = datetime.now()
        for character in _:
            character.character_api_interval_date = now + timedelta(seconds=interval_time)
            db.session.add(character)
            db.session.commit()

class Item(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    item_guid = db.Column(db.String(128), nullable=True)
    item_name = db.Column(db.String(128), nullable=True)
    item_slot = db.Column(db.String(128), nullable=True)
    character_name = db.Column(db.String(50), nullable=False)
    item_mods = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return '<Item %r>' % self.item

    @classmethod
    def retrieve_character_item_entries(cls):
        return cls.query.all()

    # create item entry
    @classmethod
    def create_item_entry(
        cls,
        character_name, item_guid, item_mods, item_name, item_slot
    ) -> None:
        _ = cls( character_name=character_name, item_guid=item_guid, item_mods=item_mods, item_name=item_name, item_slot=item_slot )
        db.session.add(_)
        db.session.commit()

    @classmethod
    def update_item_entry(cls,
        character_name, item_guid, item_mods, item_name, item_slot
    ) -> None:
        _ = cls.query.filter_by(character_name=character_name, item_guid=item_guid).first()
        if _:
            _.item_mods = item_mods
            _.item_name = item_name
            _.item_slot = item_slot
            db.session.add(_)
            db.session.commit()

    # does item already exist (guid lookup)
    @classmethod
    def does_item_already_exist(cls, character_name, item_guid) -> bool:
        _ = cls.query.filter_by(character_name=character_name, item_guid=item_guid).first()
        if _:
            return True
        return False

    @classmethod
    def get_item_data(cls, character_name, item_guid) -> str:
        _ = cls.query.filter_by(character_name=character_name, item_guid=item_guid).first()
        if _:
            item_mods_list = _.item_mods.split(",")

            item_message = character_name + " has died at level: " + str(Character.get_character_level(character_name)) + "!\n" + "Item: " + _.item_name + "\n" + "Slot: " + _.item_slot + "\n"+ _.item_name + " " + _.item_slot + " must be destroyed! \n" + "Total deaths: " + str(Character.get_character_deaths(character_name)) + "\n"
            
            item_mod_message = ""
            for item_mod in item_mods_list:
                item_mod_message = item_mod_message + item_mod + "\n"

            item_message = item_message + item_mod_message

            print("item_message: " + item_message)
            return item_message
        
    @classmethod
    def get_item_name(cls, character_name, item_guid) -> str:
        _ = cls.query.filter_by(character_name=character_name, item_guid=item_guid).first()
        if _:
            return _.item_name

class CharacterEquipment(db.Model):
    equipment_id = db.Column(db.Integer, primary_key=True)
    character_name = db.Column(db.String(50), nullable=False)
    gloves = db.Column(db.String(128), nullable=True)
    body_armour = db.Column(db.String(128), nullable=True)
    boots = db.Column(db.String(128), nullable=True)
    ring = db.Column(db.String(128), nullable=True)
    ring2 = db.Column(db.String(128), nullable=True)
    weapon = db.Column(db.String(128), nullable=True)
    helm = db.Column(db.String(128), nullable=True)
    offhand = db.Column(db.String(128), nullable=True)
    belt = db.Column(db.String(128), nullable=True)
    amulet = db.Column(db.String(128), nullable=True)

    # inventory slot id from API
    # Gloves, BodyArmour, Boots, Ring, Ring2, Weapon, Helm, Offhand, Belt, Amulet,

    def __repr__(self):
        return '<CharacterEquipment %r>' % self.character_equipment

    @classmethod
    def retrieve_character_equipment_entries(cls):
        return cls.query.all()

    @classmethod
    def update_equipment_slot(
        cls,
        character_name, slot, item_id
    ) -> None:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            if slot == 'Gloves':
                _.gloves = item_id
            elif slot == 'BodyArmour':
                _.body_armour = item_id
            elif slot == 'Boots':
                _.boots = item_id
            elif slot == 'Ring':
                _.ring = item_id
            elif slot == 'Ring2':
                _.ring2 = item_id
            elif slot == 'Weapon':
                _.weapon = item_id
            elif slot == 'Helm':
                _.helm = item_id
            elif slot == 'Offhand':
                _.offhand = item_id
            elif slot == 'Belt':
                _.belt = item_id
            elif slot == 'Amulet':
                _.amulet = item_id
            db.session.add(_)
            db.session.commit()

    @classmethod
    def create_character_entry(
        cls,
        character_name
    ) -> None:
        _ = cls( character_name=character_name)
        db.session.add(_)
        db.session.commit()

    @classmethod
    def does_character_already_exist(cls, character_name) -> bool:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            return True
        return False

    @classmethod
    def get_random_equipped_item(cls, character_name) -> str:
        _ = cls.query.filter_by(character_name=character_name).first()
        if _:
            inventory_slots = [
                "Gloves", 
                "BodyArmour", 
                "Boots", 
                "Ring", 
                "Ring2", 
                "Weapon",
                "Helm",
                "Offhand",
                "Belt",
                "Amulet"
                ]

            # item_chosen = random.choices(inventory_slots, weights=10, k=1)
            item_chosen = random.choice(inventory_slots)
            count = 0
            while(item_chosen == None and count < 30):
                item_chosen = random.choice(inventory_slots)
                count = count + 1

            print("character_name "+ character_name + " "+ "item_chosen " + item_chosen)
            if item_chosen == None:
                return "No item found!"

            if item_chosen == 'Gloves':
                return _.gloves
            elif item_chosen == 'BodyArmour':
                return _.body_armour
            elif item_chosen == 'Boots':
                return _.boots
            elif item_chosen == 'Ring':
                return _.ring
            elif item_chosen == 'Ring2':
                return _.ring2
            elif item_chosen == 'Weapon':
                return _.weapon
            elif item_chosen == 'Helm':
                return _.helm
            elif item_chosen == 'Offhand':
                return _.offhand
            elif item_chosen == 'Belt':
                return _.belt
            elif item_chosen == 'Amulet':
                return _.amulet

class DeletedItems(db.Model):
    equipment_id = db.Column(db.Integer, primary_key=True)
    item_guid = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return '<DeletedItems %r>' % self.deleted_items

    # create item entry
    @classmethod
    def create_deleted_item_entry(
        cls, item_guid
    ) -> None:
        _ = cls(item_guid=item_guid)
        db.session.add(_)
        db.session.commit()

    # check if the deleted item is in the table
    @classmethod
    def is_item_present_in_deleted_table(cls, item_guid) -> bool:
        _ = cls.query.filter_by(item_guid=item_guid).first()
        if _:
            return True
        return False

class DiscordDeathMessages(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(256), nullable=False)
    time_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    retry_after_date_discord_death = db.Column(db.DateTime, nullable=False)
    discord_death_api_interval_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<DiscordDeathMessages %r>' % self.discord_death_messages
    
    # retrieve discord death messages
    @classmethod
    def retrieve_discord_death_messages(cls) -> list:
        _ = cls.query.all()
        if _:
            return _
    
    # create discord death message entry
    @classmethod
    def create_discord_death_message_entry(
        cls, message
    ) -> None:
        _ = cls(message=message, retry_after_date_discord_death=datetime.now(), discord_death_api_interval_date=datetime.now())
        db.session.add(_)
        db.session.commit()

    # retrieve oldest discord death message and message id
    @classmethod
    def retrieve_oldest_discord_death_message(cls) -> list:
        _ = cls.query.order_by(cls.time_added).first()
        if _:
            return [_.message, _.message_id]
        
    # delete discord death message
    @classmethod
    def delete_discord_death_message(cls, message_id) -> None:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            db.session.delete(_)
            db.session.commit()

    # update discord death message retry after date
    @classmethod
    def update_discord_death_message_retry_after_date(cls, message_id, retry_after_date) -> None:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            _.retry_after_date_discord_death = retry_after_date
            db.session.commit()

    # update discord death message api interval date
    @classmethod
    def update_discord_death_message_api_interval_date(cls, message_id, api_interval_date) -> None:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            _.discord_death_api_interval_date = api_interval_date
            db.session.commit()

    # get discord death message retry after date
    @classmethod
    def get_discord_death_message_retry_after_date(cls, message_id) -> datetime:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            return _.retry_after_date_discord_death
        
    # get discord death message api interval date
    @classmethod
    def get_discord_death_message_api_interval_date(cls, message_id) -> datetime:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            return _.discord_death_api_interval_date

class DiscordCheatMessages(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(256), nullable=False)
    time_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    retry_after_date_discord_cheat = db.Column(db.DateTime, nullable=False)
    discord_cheater_api_interval_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<DiscordCheatMessages %r>' % self.discord_cheat_messages
    
    # retrieve discord cheat messages
    @classmethod
    def retrieve_discord_cheat_messages(cls) -> list:
        _ = cls.query.all()
        if _:
            return _
    
    # create discord cheat message entry
    @classmethod
    def create_discord_cheat_message_entry(
        cls, message
    ) -> None:
        _ = cls(message=message, retry_after_date_discord_cheat=datetime.now(), discord_cheater_api_interval_date=datetime.now())
        db.session.add(_)
        db.session.commit()

    # retrieve oldest discord cheat message and message id
    @classmethod
    def retrieve_oldest_discord_cheat_message(cls) -> list:
        _ = cls.query.order_by(cls.time_added).first()
        if _:
            return [_.message, _.message_id]
        
    # delete discord cheat message
    @classmethod
    def delete_discord_cheat_message(cls, message_id) -> None:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            db.session.delete(_)
            db.session.commit()

    # update discord cheat message retry after date
    @classmethod
    def update_discord_cheat_message_retry_after_date(cls, message_id, retry_after_date) -> None:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            _.retry_after_date_discord_cheat = retry_after_date
            db.session.commit()

    # update discord cheat message api interval date
    @classmethod
    def update_discord_cheat_message_api_interval_date(cls, message_id, api_interval_date) -> None:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            _.discord_cheater_api_interval_date = api_interval_date
            db.session.commit()
    
    # get discord cheat message retry after date
    @classmethod
    def get_discord_cheat_message_retry_after_date(cls, message_id) -> datetime:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            return _.retry_after_date_discord_cheat
        
    # get discord cheat message api interval date
    @classmethod
    def get_discord_cheat_message_api_interval_date(cls, message_id) -> datetime:
        _ = cls.query.filter_by(message_id=message_id).first()
        if _:
            return _.discord_cheater_api_interval_date

