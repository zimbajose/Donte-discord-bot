from __future__ import annotations

import random
import discord
import DiscordUser
from Car import Car
from datetime import datetime,timedelta
#Imports the prompts
from Other import MessagePrompt
from Other import Emojis
from Other import format_number
from Other import PromptList

class CarGacha:
    #Constants
    __DELAY = 0 # in minutes
    __SELL_RATE = 3 #The value that the price will be divided by when you sell the car
   
    #Car garage command
    __CARS_LIST_MESSAGE = "These are author's cars\n"
   
    #Car sell command
    __SELL_NO_CARS_FOUND = "No cars found on your list of this model for selling."
    __SELL_CONFIRMATION_TITLE = "Are you sure?"
    __SELL_CONFIRMATION_DESCRIPTION = "Your year model will be sold for price credits, this action cannot be undone."
    __SELL_CONFIRMED_TEXT = "You sold your model for price credits."
    __SELL_DECLINED_TEXT = "You decided to not sell your model."
    #Car gacha command
    __ALREADY_HAS_CAR_MESSAGE = "You already have this car, selling for value credits"
    __GACHA_COOLDOWN_MESSAGE = "author you need to wait time minutes to roll again"
    __GOT_CAR_MESSAGE = "Congratulations author you have obtained a brand year car"

    #User balance
    __USER_BALANCE_MESSAGE = "author you have money CR on your account."

    #Help texts
    __SELL_COMMAND_HELP = "The correct usage of this command is $car sell <car model>"
    __SEARCH_COMMAND_HELP = "The correct usage of this command is $car search <car name>"
    

    #Search command
    __SEARCH_LIST_TITLE = "Select the car you are looking for"
    __SEARCH_LIST_NOT_FOUND = "No cars found with similar names"

    #Rarity codes
    __rarities = {
        0:"common",
        1:"uncommon",
        2:"rare",
        3:"epic",
        4:"legendary",
        5:"Mythical"
    }

    __color_codes = {
        0: discord.Color.light_grey(),
        1: discord.Color.teal(),
        2: discord.Color.blue(),
        3: discord.Color.dark_purple(),
        4: discord.Color.orange(),
        5: discord.Color.gold()
    }

    def __init__(self):
        self.active_prompts = PromptList()
       
    #Handles all events that come from a message
    async def message(self,message : discord.Message):
        commands = message.content.split(" ")
        command = commands[1] if len(commands)>1 else "help"
        if command=='gacha':
            await self.__gacha_car(message.author,message.channel)
        elif command=='garage':
            await self.__get_user_cars(message.author,message.channel)
        elif command == 'balance':
            await self.__get_user_balance(message.author,message.channel)
        elif command=='search':
            commands.pop(0)
            commands.pop(0)
            prompt = ""
            if len(commands)==0:
                await message.channel.send(CarGacha.__SEARCH_COMMAND_HELP)
                return
            for text in commands:
                prompt = prompt+ text + " "
            await self.__search_for_car(message.author,message.channel,prompt)
        elif command == 'sell':
            commands.pop(0)
            commands.pop(0)
            prompt = ""
            if len(commands)==0:
                await message.channel.send(CarGacha.__SELL_COMMAND_HELP)
                return
            for text in commands:
                prompt = prompt+ text + " "
            await self.__search_car_to_sell(message.author,message.channel,prompt)
    
    #Handles all events tha come from reactions
    async def react(self,reaction:discord.Reaction, user: discord.User):
        #Verifies if the message is in the active prompts list
        selected_prompt = self.active_prompts.find_by_message(reaction.message)
        if selected_prompt == None:
            return
        #Verifies if the user is author of the original prompt
        if user !=selected_prompt.original_author:
            return
        #Calls function associated with prompt
        response = await selected_prompt.callback(selected_prompt,reaction)
        #If response is true, will remove the prompt message and remove the prompt from the active prompts
        if response:
            await self.active_prompts.remove(selected_prompt)

    #Sorts a random car from the list
    async def __gacha_car(self,author : discord.User, channel : discord.TextChannel):
        rarity  = self.__get_random_rarity()
        car = Car.get_random_car(rarity)
        discord_tag = author.global_name
        user = DiscordUser.User.search_user(discord_tag)
        if user.last_gacha!=None:
            time_to_next_roll = user.last_gacha + timedelta(minutes = CarGacha.__DELAY)

            if time_to_next_roll>=datetime.now():
                difference = time_to_next_roll - datetime.now()
                cooldown_message = CarGacha.__GACHA_COOLDOWN_MESSAGE.replace("author",author.display_name).replace("time",str(int(difference.total_seconds()/60)))
                await channel.send(cooldown_message)
                return
        
        has_car = car.check_owner(user)
        #Checks if user already has the car otherwise it will sell it
        if not has_car:
            #Adds the car to the user's list
            car.add_owner(user)
        user.set_time()
        embed_car = discord.Embed()
        embed_car.set_image(url=car.image_url)
        embed_car.set_footer(text = CarGacha.__rarities[rarity])
        embed_car.colour = CarGacha.__color_codes[rarity]
        text = CarGacha.__GOT_CAR_MESSAGE.replace('car',car.model).replace('author',author.name).replace('brand',car.brand)
        if car.year!=None:
            text.replace("year",str(car.year))
        else:
            text.replace("year","")
        embed_car.description = text
        await channel.send(embed = embed_car)
        if has_car:
            sell_price = car.price/3
            sell_message = CarGacha.__ALREADY_HAS_CAR_MESSAGE.replace("value",format_number(sell_price))
            user.add_money(sell_price)
            await channel.send(sell_message)

    #Checks the user's balance
    async def __get_user_balance(self,author: discord.User,channel : discord.TextChannel):
        user = DiscordUser.User.search_user(author.global_name)
        message_text = CarGacha.__USER_BALANCE_MESSAGE.replace("money",format_number(user.gacha_money))
        await channel.send(message_text)

    #Sends the list of cars the user has
    async def __get_user_cars(self,author : discord.User, channel : discord.TextChannel):
        discord_tag = author.global_name
        user = DiscordUser.User.search_user(discord_tag)
        cars = Car.get_user_cars(user)
        if cars==None:
            await channel.send("It seems you have no cars, use the $car gacha command to roll for a random car")
            return
        cars_list = ""
        for car in cars:
            if car.year!=None:
                cars_list = cars_list+"\n "+str(car.year)+" "+car.model
            else:
                cars_list = cars_list+"\n "+car.model
        embed = discord.Embed()
        embed.title = CarGacha.__CARS_LIST_MESSAGE.replace('author',author.display_name)
        embed.description = cars_list
        await channel.send(embed = embed)
    
    #Searches for a car by name, sends a embed when there is only one with similar name, if there are multiple matches it sends a prompt to select one of them with reactions
    async def __search_for_car(self,author : discord.User,channel : discord.TextChannel ,prompt : str):
        cars = Car.search_cars(prompt)
        if cars == None:
            await channel.send(CarGacha.__SEARCH_LIST_NOT_FOUND)
            return
        if len(cars) ==1:
            car_embed = self.__get_car_embed(cars[0])
            await channel.send(embed = car_embed)
            return
        await self.__send_car_select_prompt(channel,author,cars,self.__send_embed)

    #Searches for the car model in the user's cars, then send a prompt for the user to select the car he wants to sell
    async def __search_car_to_sell(self,author : discord.User,channel : discord.TextChannel, prompt : str):
        if prompt == "":
            await channel.send(CarGacha.__SELL_COMMAND_HELP)
            return
        user = DiscordUser.User.search_user(author.global_name)
        cars = Car.get_user_cars(user,prompt)
        #Checks the length, if its 0 will say it found no cars, if 1 it will send the confimartion prompt
        if cars == None:
            await channel.send(CarGacha.__SELL_NO_CARS_FOUND)
            return
        elif len(cars)==1:
            await self.__send_sell_confirmation_prompt(None,cars[0],author,channel)
            return
        #Sends a select prompt with the callback for the sell confirmation prompt function
        await self.__send_car_select_prompt(channel,author,cars,self.__send_sell_confirmation_prompt)

    #Sends a confirmation prompt to see if the user really wants to sell the car
    async def __send_sell_confirmation_prompt(self,message_prompt : MessagePrompt, car : Car, author : discord.User = None, channel : discord.TextChannel = None):
        if not message_prompt == None:
            channel = message_prompt.message.channel
            author = message_prompt.original_author
        sell_price = car.price/CarGacha.__SELL_RATE
        description = CarGacha.__SELL_CONFIRMATION_DESCRIPTION.replace("year",str(car.year)).replace("model",str(car.model)).replace("price",format_number(sell_price))
        message_embed = discord.Embed()
        message_embed.title = CarGacha.__SELL_CONFIRMATION_TITLE
        message_embed.description = description
        sent_message = await channel.send(embed = message_embed)
        await sent_message.add_reaction(Emojis.ACCEPT)
        await sent_message.add_reaction(Emojis.DECLINE)

        new_prompt = MessagePrompt(sent_message,author,self.__sell_car,car)
        await self.active_prompts.add(new_prompt)
        return True

    #Sells or not the car based on the reply
    async def __sell_car(self,message_prompt : MessagePrompt, reaction : discord.Reaction):
        car = message_prompt.data
        sell_price = car.price/CarGacha.__SELL_RATE
        if reaction.emoji==Emojis.DECLINE:
            decline_message = CarGacha.__SELL_DECLINED_TEXT.replace("model",car.model)
            await message_prompt.message.channel.send(decline_message)
            return True
        if reaction.emoji == Emojis.ACCEPT:
            accept_message = CarGacha.__SELL_CONFIRMED_TEXT.replace("model",car.model).replace("price",format_number(sell_price))
            user = DiscordUser.User.search_user(message_prompt.original_author.global_name)
            car.remove_owner(user)
            user.add_money(sell_price)
            await message_prompt.message.channel.send(accept_message)
            return True
        return False

    #Sends a car embed
    async def __send_embed(self,message_prompt : MessagePrompt,car : Car):
        
        car_embed = self.__get_car_embed(car)
        await message_prompt.message.channel.send(embed = car_embed)

    #Generates a embed with all the info of the selected car
    def __get_car_embed(self,car :Car)-> discord.Embed:
        car_embed = discord.Embed()
        if car.year!=None:
            car_embed.title = str(car.year)+" "+car.model
        else:
            car_embed.title = car.model
        car_embed.set_image(url=car.image_url)
        car_embed.set_footer(text=car.brand)
        car_embed.colour = CarGacha.__color_codes[car.rarity]
        info = car.drive+"\n"+str(car.horsepower)+" hp\n"+str(car.weight)+" kg\n"+ str(car.torque) + " nm\ndefault price "+format_number(car.price)+" CR"
        car_embed.description = info

        return car_embed
    
    #Sends a car selection prompt
    async def __send_car_select_prompt(self,channel : discord.TextChannel,author : discord.User,cars : list,callback : function):
        if len(cars)<2:
            Exception("Not enough cars to make a select prompt")
        i = 1
        list_embed = discord.Embed()
        list_embed.title = CarGacha.__SEARCH_LIST_TITLE
        message_text = ""
        for car in cars:
            if car.year == None:
                message_text = message_text+"\n"+str(i)+". "+car.model
            else:
                message_text = message_text+"\n"+str(i)+". "+str(car.year)+" "+car.model
        list_embed.description = message_text
        
        sent_message = await channel.send(embed= list_embed)
        await sent_message.add_reaction(Emojis.ONE)
        await sent_message.add_reaction(Emojis.TWO)
        if len(cars)>2:
            await sent_message.add_reaction(Emojis.THREE)
        if len(cars)>3:
            await sent_message.add_reaction(Emojis.FOUR)
        if len(cars)>4:
            await sent_message.add_reaction(Emojis.FIVE)
        data = {
            "cars":cars,
            "callback": callback 
        }
        new_message_prompt = MessagePrompt(sent_message,author,self.__select_car_prompt,data)
        await self.active_prompts.add(new_message_prompt)

    #Returns the car from a selected prompt on the callback
    async def __select_car_prompt(self,message_prompt : MessagePrompt,reaction: discord.reaction):
        cars = message_prompt.data['cars']
        #Checks for the reaction sent and sets the car based on the data sent
        if reaction.emoji == Emojis.ONE and len(cars)>0:
            car =cars[0]
        elif reaction.emoji == Emojis.TWO and len(cars)>1:
            car = cars[1]
        elif reaction.emoji == Emojis.THREE and len(cars)>2:
            car = cars[2]
        elif reaction.emoji == Emojis.FOUR and len(cars)>3:
            car = cars[3]
        elif reaction.emoji == Emojis.FIVE and len(cars)>4:
            car = cars[4]
        else:
            return False
        #Obtains the car based on the id
        car = Car.get_car_by_id(car.id)
        await message_prompt.data['callback'](message_prompt,car)
        return True

    #Gets a random rarity
    def __get_random_rarity(self) ->int:
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
        
        

