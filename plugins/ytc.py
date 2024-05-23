from pyrogram import filters, Client as ace
from pyrogram.types import Message
from main import LOGGER as LOGS, prefixes, Config
import os
import requests
import wget
import img2pdf
import shutil
from PIL import Image
from handlers.uploader import Upload_to_Tg

@ace.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("ytc", prefixes=prefixes)
)
async def drm(bot: ace, m: Message):
    path = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/PHOTO/{m.chat.id}"
    os.makedirs(path, exist_ok=True)
    os.makedirs(tPath, exist_ok=True)

    # Ask user for pages range, book name, and book ID
    pages_msg = await bot.ask(m.chat.id, "Send Pages Range Eg: '1:100'\nBook Name\nBookId")
    pages, book_name, book_id = str(pages_msg.text).split("\n")

    url = "https://yctpublication.com:443/master/api/PdfController/getSinglePageExtractedFromPdfFileUsingImagickCodeigniter3?book_id={bid}&page_no={pag}&user_id=14593&token=eyJhbGciOiJSUzI1NiIsImtpZCI6IjVkZjFmOTQ1ZmY5MDZhZWFlZmE5M2MyNzY5OGRiNDA2ZDYwNmIwZTgiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyMjkwMDE2MzYyNTQtZWZjcDlqYm4wMzJzbmpmc"

    page_start, page_end = map(int, pages.split(":"))
    page_end += 1  # Increase the end page by 1 to include the last page in the range

    # Function to download an image from a given URL
    def download_image(image_link, file_name):
        response = requests.get(url=image_link)
        if response.status_code == 200:
            with open(f"{tPath}/{file_name}.jpg", "wb") as f:
                f.write(response.content)
            return f"{tPath}/{file_name}.jpg"
        else:
            print(f"Failed to download image: {response.status_code}")
            return None

    # Function to download image using wget
    def down(image_link, file_name):
        wget.download(image_link, f"{tPath}/{file_name}.jpg")
        return f"{tPath}/{file_name}.jpg"

    # Function to validate image format
    def validate_image(image_path):
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception as e:
            print(f"Invalid image: {image_path} - {e}")
            return False

    # Function to convert a list of images to a PDF
    def download_pdf(title, imagelist):
        if not imagelist:
            raise ValueError("No valid images to convert to PDF.")
        valid_images = [i for i in imagelist if validate_image(i)]
        if not valid_images:
            raise ValueError("All images are invalid.")
        with open(f"{path}/{title}.pdf", "wb") as f:
            f.write(img2pdf.convert(valid_images))
        return f"{path}/{title}.pdf"

    # Notify user that download has started
    show_msg = await bot.send_message(m.chat.id, "Downloading")
    img_list = []

    # Download each page within the specified range
    for i in range(page_start, page_end):
        try:
            print(f"Downloading Page - {str(i).zfill(3)}")
            name = f"{str(i).zfill(3)}.page_no_{str(i)}"
            img_path = download_image(image_link=url.format(pag=i, bid=book_id), file_name=name)
            if img_path and validate_image(img_path):
                img_list.append(img_path)
            else:
                print(f"Skipping invalid or failed download image: {img_path}")
        except Exception as e:
            await m.reply_text(f"Error downloading page {i}: {e}")
            continue

    try:
        # Create PDF from downloaded images
        pdf_path = download_pdf(title=book_name, imagelist=img_list)
    except Exception as e1:
        await m.reply_text(f"Error creating PDF: {e1}")
        return

    # Upload PDF to Telegram
    ul = Upload_to_Tg(
        bot=bot, m=m, file_path=pdf_path, name=book_name,
        Thumb="hb", path=path, show_msg=show_msg, caption=book_name
    )
    await ul.upload_doc()
    print("Upload Done")

    # Clean up temporary directories
    shutil.rmtree(tPath)
