from __future__ import annotations
import json
import random
import discord
import shared
import mysql.connector
import ddbconnector

class CarGacha:
    #Constants
    __delay = 60
    __got_car_message = "Congratulations author you have obtained a rarity car"
    __cars_list_message = "These are author's cars\n"

    __rarities = {
        0:"common",
        1:"uncommon",
        2:"rare",
        3:"epic",
        4:"legendary",
        5:"Mythical"
    }
    def __init__(self):
        pass
       
    #Handles all events that come from a message
    async def message(self,message : discord.Message):
        commands = message.content.split(" ")
        command = commands[1] if len(commands)>1 else "help"
        if command=='gacha':
            await self.__gacha_car(message)

    #Sorts a random car from the list
    async def __gacha_car(self,message : discord.Message):
        rarity  = self.__get_random_rarity()
        car = Car.get_random_car(rarity)
        discord_tag = message.author.global_name
        user = shared.User.search_user(discord_tag)
        #Adds the car to the user's list
        car.add_owner(user)

        embed_car = discord.Embed()
        embed_car.set_image(url=car.image_url)
        text = CarGacha.__got_car_message.replace('car',car.model).replace('author',message.author.name).replace('rarity',CarGacha.__rarities[rarity])
        embed_car.description = text
        await message.channel.send(embed = embed_car)

    #Sends the list of cars the user has
    async def __get_user_Cars(self,message : discord.Message):
        discord_tag = message.author.global_name
        user = shared.User.search_user(discord_tag)
        cars = Car.get_user_cars(user)
        if len(cars)==0:
            await message.channel.send("It seems you have no cars, use the $car gacha command to roll for a random car")
            return
        cars_list_message = CarGacha.__cars_list_message
        for car in cars:
            cars_list_message = cars_list_message+ " "+car.model + "\n"

    #Gets a random rarity
    def __get_random_rarity(self):
        rand = random.randint(1,1000)
        if rand>=995:
            return 5
        elif rand>=975:
            return 4
        elif rand>=925:
            return 3
        elif rand>=825:
            return 2
        elif rand >=650:
            return 1
        else:
            return 0
        
        

class Car:

    def __init__(self,id : int,model : str,brand : str,price : float,image_url : str,rarity : int):
        self.id = id
        self.model = model
        self.brand = brand
        self.price = price
        self.image_url = image_url
        self.rarity = rarity

    #Gets a car by id
    @staticmethod
    def get_car_by_id(id : int) ->Car:
        cnx = ddbconnector.get_connection()
        cursor = cnx.cursor()

        query = "SELECT id,model,brand,price,image_url,rarity FROM car WHERE id=%s"
        cursor.execute(query,id)
        data = cursor.fetchone()
        if data== None:
            return None
        
        model = data[1]
        brand = data[2]
        price = data[3]
        image_url = data[4]
        rarity = data[5]
        
        cursor.close()
        cnx.close()

        return Car(id,model,brand,price,image_url,rarity)
    
    #Gets a random car based on rarity
    @staticmethod
    def get_random_car(rarity = None)-> Car:
        cnx = ddbconnector.get_connection()
        cursor = cnx.cursor()

        #If no rarity has been sent simply gets a random from all possible cars
        if rarity==None:
            query = "SELECT id,model,brand,price,image_url,rarity FROM CAR ORDER BY RAND() LIMIT 1"
            cursor.execute(query)
            data = cursor.fetchone()
            if data==None:
                cursor.close()
                cnx.close()
                Exception("Database has no cars!")

            id = data[0]
            model = data[1]
            brand = data[2]
            price = data[3]
            image_url = data[4]
            rarity = data[5]

            cursor.close()
            cnx.close()
            return Car(id,model,brand,price,image_url,rarity)

        query = "SELECT id,model,brand,price,image_url,rarity FROM CAR WHERE rarity= %(rarity)s ORDER BY RAND() LIMIT 1"
        cursor.execute(query,{'rarity':rarity})
        data = cursor.fetchone()
        if data==None:
            Exception("No car found with this rarity value, was an invalid value sent?")

        id = data[0]
        model = data[1]
        brand = data[2]
        price = data[3]
        image_url = data[4]
        
        cursor.close()
        cnx.close()
        return Car(id,model,brand,price,image_url,rarity)
    
    #Adds a ownership of this car to the database
    def add_owner(self,user : shared.User):
        cnx = ddbconnector.get_connection()
        cursor = cnx.cursor()

        insert = "INSERT INTO car_possession(car_id,user_discordtag) VALUES(%(car_id)s,%(user_discordtag)s)"
        data = {
            "car_id": self.id,
            "user_discordtag":user.discord_tag
        }
        cursor.execute(insert,data)

        cursor.close()
        cnx.close()

    #Gets all the cars of the user and returns them as a list
    @staticmethod
    def get_user_cars(user : shared.User)->list:
        cnx =ddbconnector.get_connection()
        cursor = cnx.cursor()
        
        query = "SELECT c.id,c.model,c.brand,c.price,c.image_url,c.rarity FROM car c JOIN car_possession cp ON c.id=cp.car_id JOIN user u ON u.id = %(user_id)s"
        data = {
            "user_id": user.id
        }
        cursor.execute(query,data)
        cars_raw = cursor.fetchall()
        cars = []
        
        for car_raw in cars_raw:
            id = car_raw[0]
            model = car_raw[1]
            brand = car_raw[2]
            price = car_raw[3]
            image_url = car_raw[4]
            rarity = car_raw[5]
            car = Car(id,model,brand,price,image_url,rarity)
            cars.append(car)

        cursor.close()
        cnx.close()
        return cars
