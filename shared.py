from __future__ import annotations
import mysql.connector
import ddbconnector
from datetime import datetime
class User:

    def __init__(self,tag : str,last_gacha : datetime = None,gacha_money :int =0):
        self.discord_tag = tag
        self.last_gacha = last_gacha
        self.gacha_money = gacha_money
    
    #Searches for the user's tag in the database, if it does not find it it will then insert it, in both cases returns the a user object
    @staticmethod
    def search_user(tag : str)-> User:
        connector = ddbconnector.get_connection()
        cursor = connector.cursor()

        query = "SELECT discord_tag, last_gacha, gacha_money FROM discord_user WHERE discord_tag = %(tag)s"
        cursor.execute(query,{'tag':tag})
       
        data = cursor.fetchone()
        if data == None:
            insert = "INSERT INTO discord_user(discord_tag) VALUES(%(tag)s)"
            cursor.execute(insert,{"tag":tag})
            connector.commit()
            cursor.close()
            connector.close()
            return User(tag)

        last_gacha = data[1]
        gacha_money = data[2]
        cursor.close()
        connector.close()
        return User(tag,last_gacha,gacha_money)
    
    #Sets the gacha time for this user to now
    def set_time(self):
        connector = ddbconnector.get_connection()
        cursor = connector.cursor()
        update = "UPDATE discord_user SET last_gacha = %(last_gacha)s WHERE discord_tag = %(discord_tag)s"
        data = {
            "last_gacha": datetime.now(),
            "discord_tag": self.discord_tag
        }
        cursor.execute(update,data)
        connector.commit()
        cursor.close()
        connector.close()