import jmcomic
import os
import datetime
import asyncio
import telegram

from PIL import Image
from PyPDF2 import PdfMerger
from telegram import Update
from telegram.ext import ContextTypes

temp_download_path = "download"

# if pdf_name is not None, combine all pdfs
def convert_image_folder_to_pdf(directory, pdf_name=None):
    # get all images in /download, process them and add them to pdf
    print(f"Converting {directory} to PDF.")
    if pdf_name is not None:
        merger = PdfMerger()
        for file_name in sorted(os.listdir(directory)):
            if file_name.endswith(".pdf"):
                merger.append(os.path.join(directory, file_name))
        if merger.pages:
            merger.write(f"{temp_download_path}/{pdf_name}")
            merger.close()
            os.chmod(f"{temp_download_path}/{pdf_name}", 0o777)

    else:
        pdf_name = directory
        images = []
        for image_path in sorted(os.listdir(directory)):
            if image_path.endswith(".png"):
                image = Image.open(os.path.join(directory, image_path))
                image.convert("RGB")
                images.append(image)
        if images:
            images[0].save(f"{pdf_name}.pdf", save_all=True, append_images=images[1:])
            os.chmod(f"{pdf_name}.pdf", 0o777)

def download_comic(comic_id):
    # if download folder does not exist, create it
    if not os.path.exists(temp_download_path):
        os.mkdir(temp_download_path)
    # clear download folder
    for file in os.listdir(temp_download_path):
        os.remove(os.path.join(temp_download_path, file))
    # download comic
    option = jmcomic.create_option_by_file('../config/jm_dl_option.yml')
    jmcomic.download_album(comic_id, option)
    # convert comic to pdf, by chapter
    for folders in sorted(os.listdir(temp_download_path)):  # only process folders in /download
        folder_path = os.path.join(temp_download_path, folders)
        if os.path.isdir(folder_path):
            convert_image_folder_to_pdf(folder_path)
    # combine all chapters into one pdf
    convert_image_folder_to_pdf(temp_download_path, f"{comic_id}.pdf")
    # clean up
    # delete all sub folders
    for folders in sorted(os.listdir(temp_download_path)):
        folder_path = os.path.join(temp_download_path, folders)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                os.remove(os.path.join(folder_path, file))
            os.rmdir(folder_path)
    # delete all files except {comic_id}.pdf
    for file in os.listdir(temp_download_path):
        if file != f"{comic_id}.pdf":
            os.remove(os.path.join(temp_download_path, file))
    return f"{comic_id}.pdf"

# download comic from jm and send to chat
async def jm_comic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received /jm, ", end="")
    comic_id = update.message.text.replace('/jm ', '')
    print("Trying to download jm " + comic_id)
    # if comic id is not digit, show usage
    if not comic_id.isdigit():
        print(datetime.datetime.now(), "\t", "Invalid comic_id.")
        await update.message.reply_text("Usage: /jm <comic_id>")
        return

    await update.message.reply_text(f"Downloading comic {update.message.text.replace('/jm ', '')}...")
    # create a background task and download the comic
    asyncio.create_task(jm_comic_download(comic_id, update, context))

async def jm_comic_download(comic_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "A new thread started to download comic " + comic_id)
    # if comic exists, send it directly
    if os.path.exists(f"download/{comic_id}.pdf"):
        print(datetime.datetime.now(), "\t", "Comic " + comic_id + " already exists, sending it directly.")
        with open(f"download/{comic_id}.pdf", 'rb') as pdf_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file)
        return
    # if comic not exist, download
    try:
        pdf_path = await asyncio.to_thread(download_comic, comic_id)
        with open(f"download/{pdf_path}", 'rb') as pdf_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file)
        print(datetime.datetime.now(), "\t", "Comic " + comic_id + " sent to chat.")

    except telegram.error.TimedOut:
        pass    # This error is expected when the download takes too long, we will just ignore it
    except telegram.error.NetworkError as e:
        if "Request Entity Too Large" in str(e):
            print("Error: File size exceeds the limit.")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: File is too large to send.")
        else:
            print("NetworkError: ", e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="NetworkError: " + str(e))
    except Exception as e:
        print("Error: ", e)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e))


# for test only
# download_comic(422866)
