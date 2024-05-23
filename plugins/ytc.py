from pyrogram import filters, Client as ace
from main import LOGGER as LOGS, prefixes
from pyrogram.types import Message
from main import Config
import os
import requests
import shutil
from PIL import Image
from io import BytesIO

@ace.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("ytc", prefixes=prefixes)
)
async def drm(bot: ace, m: Message):
    path = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/PHOTO/{m.chat.id}"
    os.makedirs(path, exist_ok=True)
    os.makedirs(tPath, exist_ok=True)

    pages_msg = await bot.ask(m.chat.id, "Send Pages Range Eg: '1:100'\nBook Name\nBookId")
    pages, Book_Name, bid = str(pages_msg.text).split("\n")

    base_url = "https://yctpublication.com/master/api/MasterController/booklist"
    page = pages.split(":")
    page_1 = int(page[0])
    last_page = int(page[1]) + 1

    def download_image(image_link, file_name):
        try:
            response = requests.get(url=image_link)
            response.raise_for_status()  # Check if the request was successful
            if 'image' in response.headers.get('Content-Type', ''):
                with open(f"{tPath}/{file_name}.jpg", "wb") as f:
                    f.write(response.content)
                return f"{tPath}/{file_name}.jpg"
            else:
                raise Exception("The response is not an image.")
        except requests.RequestException as e:
            raise Exception(f"Failed to download image: {str(e)}")

    show = await bot.send_message(
        m.chat.id,
        "Downloading"
    )
    img_list = []

    for i in range(page_1, last_page):
        try:
            print(f"Downloading Page - {str(i).zfill(3)}")
            name = f"{str(i).zfill(3)}.page_no_{str(i)}"
            image_url = base_url.format(pag=i, bid=bid)
            image_path = download_image(image_link=image_url, file_name=name)
            
            # Validate the downloaded image
            try:
                with Image.open(image_path) as img:
                    img.verify()  # Verify that it is an image
                img_list.append(image_path)
            except (IOError, SyntaxError) as e:
                print(f"Invalid image file: {image_path}, {str(e)}")
                os.remove(image_path)  # Remove invalid image file
        except Exception as e:
            await m.reply_text(str(e))
            continue

    if not img_list:
        await m.reply_text("No valid images were downloaded.")
        return

    for img_path in img_list:
        try:
            await bot.send_photo(m.chat.id, photo=img_path, caption=Book_Name)
        except Exception as e:
            await m.reply_text(f"Failed to send image: {str(e)}")

    await show.delete()
    print("Done")
    shutil.rmtree(tPath)
