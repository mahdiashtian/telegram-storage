# telegram-storage
A robot to save your files (photos, videos, stickers, songs, etc.) and share them with others through links.

Robot capabilities:
- Storage of all files with any extension up to 1 GB
- SPassword support to prevent unauthorized access to your files
- Support for your desired caption (shown after receiving the file by the user)
- Displays the number of times your file has been downloaded

# Requirements
- Python (3.5, 3.6, 3.7, 3.8, 3.9, 3.10)
- Pyrogram (2.0.106)
- Postgres (12.16)


# Installation
```
git clone https://github.com/mahdiashtian/telegram-storage.git 
```
```
cd telegram-storage
```
```
pip install -r requirements.txt
```
# Usage
```
touch .env
```
Open the ".env" file and copy the following information into it:
```
API_ID=123456
API_HASH="35886641ed1bfaa92e7ee30er9888"
BOT_TOKEN='6788893252:AAGUrIEA8p5ZlLcy59eGsmrDeyB4f3f_WcR'
DB_USER='user'
DB_NAME='name'
DB_PASSWORD='password'
DB_HOST='localhost'
```
You should get the value of API_ID and API_HASH from my.telegram.org site, then you create a bot using [BotFather](https://t.me/BotFather) and replace your token with the value BOT_TOKEN, then create a postgres database and replace your database values with the four values DB_USER - DB_NAME - DB_PASSWORD - DB_HOST

Then enter the following command in the terminal:
```
python main.py 
```
or
```
python3 main.py 
```
