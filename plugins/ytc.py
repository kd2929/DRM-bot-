from pyrogram import filters, Client as ace
from main import LOGGER as LOGS, prefixes
from pyrogram.types import Message
from main import Config
import os
import requests
import wget
import img2pdf
import shutil

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

    base_url = "http://yctpublication.com/master/api/MasterController/getPdfPage?book_id={bid}&page_no={pag}&user_id=14593&token=eyJhbGciOiJSUzI1NiIsImtpZCI6IjVkZjFmOTQ1ZmY5MDZhZWFlZmE5M2MyNzY5OGRiNDA2ZDYwNmIwZTgiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyMjkwMDE2MzYyNTQtZWZjcDlqYm4wMzJzbmpmc"
    page = pages.split(":")
    page_1 = int(page[0])
    last_page = int(page[1]) + 1

    def download_image(image_link, file_name):
        k = requests.get(url=image_link)
        if k.status_code == 200:
            with open(f"{tPath}/{file_name}.jpg", "wb") as f:
                f.write(k.content)
            return f"{tPath}/{file_name}.jpg"
        else:
            raise Exception(f"Failed to download image: {k.status_code}")

    def down(image_link, file_name):
        try:
            wget.download(image_link, f"{tPath}/{file_name}.jpg")
            return f"{tPath}/{file_name}.jpg"
        except Exception as e:
            raise Exception(f"Failed to download image with wget: {str(e)}")

    def download_pdf(title, imagelist):
        pdf_path = f"{path}/{title}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert([i for i in imagelist]))
        return pdf_path

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
            y = down(image_link=image_url, file_name=name)
            img_list.append(y)
        except Exception as e:
            await m.reply_text(str(e))
            continue

    try:
        pdf_path = download_pdf(title=Book_Name, imagelist=img_list)
    except Exception as e1:
        await m.reply_text(str(e1))
        return

    thumb = "hb"  # Assuming you have a thumbnail image path or you can set it to None
    UL = Upload_to_Tg(bot=bot, m=m, file_path=pdf_path, name=Book_Name,
                      Thumb=thumb, path=path, show_msg=show, caption=Book_Name)
    await UL.upload_doc()
    
    print("Done")
    shutil.rmtree(tPath)
