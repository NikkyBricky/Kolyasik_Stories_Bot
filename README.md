# Kolyasik_Stories_Bot
GPT bot that you can use to generate stories with the neural network

[link to git](https://github.com/NikkyBricky/Kolyasik_Stories_Bot.git)
# Description

To generate stories you can use different parameters:
1. Genres (drama, detective, comedy, action-movie)
2. Characters (Monkey Di Luffy, Mable Panes, Robert Lohkamp, Lara Croft)
3. Settings (ocean, lost iceland, catastrophy)
4. You can also add additional information 

This bot uses model "yandexgpt-lite" 

# Usage:
If you want to make your bot with the functions like here, I suggest you to:
 1. Clone this repository
 2. Create .env file with BOT_TOKEN, GPT_TOKEN, FOLDER_ID and ADMIN_ID (your telegram_id) variables
 3. install packages from requirements.txt 
 4. If you want to move bot to the server, you may not use GPT_TOKEN, but func get_creds() from file make_gpt_token.py to get token automatically  
 5. You can also use infra directory from the project to make it work non-stop on your server 

If you just want to see it work:
 1. go to https://t.me/fascinating_stories_bot (bot is launched on cloud)
 2. Choose parameters 
 3. Create your stories

Enjoy!

# Bot logic
![](https://github.com/NikkyBricky/Kolyasik_Stories_Bot/blob/main/bot_schema.png)