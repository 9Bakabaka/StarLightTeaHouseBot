import jmcomic
import os
import datetime
import asyncio
import telegram

from PIL import Image
from PyPDF2 import PdfMerger
from telegram import Update
from telegram.ext import ContextTypes

# use absolute path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
temp_download_path = os.path.join(base_dir, "download", "cache")

# if pdf_name is not None, combine all pdfs
def convert_image_folder_to_pdf(directory, pdf_name=None):
    # get all images in the folder and process them and add them to pdf
    print(f"[jm] Converting {directory} to PDF.")
    if pdf_name is not None:
        merger = PdfMerger()
        for file_name in sorted(os.listdir(directory)):
            if file_name.endswith(".pdf"):
                merger.append(os.path.join(directory, file_name))
        if merger.pages:
            output_path = os.path.join(temp_download_path, pdf_name)
            merger.write(output_path)
            merger.close()
            os.chmod(output_path, 0o777)

    else:
        pdf_name = os.path.basename(directory)
        images = []
        for image_path in sorted(os.listdir(directory)):
            if image_path.endswith(".png"):
                image = Image.open(os.path.join(directory, image_path))
                image.convert("RGB")
                images.append(image)
        if images:
            output_path = os.path.join(temp_download_path, f"{pdf_name}.pdf")
            images[0].save(output_path, save_all=True, append_images=images[1:])
            os.chmod(output_path, 0o777)

def download_comic(comic_id):
    # if download folder does not exist, create it
    if not os.path.exists(temp_download_path):
        os.makedirs(temp_download_path, exist_ok=True)
    # clear cache folder
    for file in os.listdir(temp_download_path):
        file_path = os.path.join(temp_download_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    # download comic
    option = jmcomic.create_option_by_file(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'jm_dl_option.yml'))
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
    # target_pdf = f"{comic_id}.pdf"
    # for file in os.listdir(temp_download_path):
    #     if file != target_pdf:
    #         file_path = os.path.join(temp_download_path, file)
    #         if os.path.isfile(file_path):
    #             os.remove(file_path)

    # move {comic_id}.pdf to download folder aka ../ to store it
    os.rename(os.path.join(temp_download_path, f"{comic_id}.pdf"), os.path.join(os.path.dirname(temp_download_path), f"{comic_id}.pdf"))
    # clear cache folder
    for file in os.listdir(temp_download_path):
        file_path = os.path.join(temp_download_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    pdf_to_sent = os.path.join(os.path.dirname(temp_download_path), f"{comic_id}.pdf")
    return pdf_to_sent

# download comic from jm and send to chat
async def jm_comic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage_msg = "Usage: /jm <comic_id>\nOr /jm listcache to list cached comics.\nOr /jm clearcache to clear cached comics."
    print(datetime.datetime.now(), "\t", "[jm] Received /jm ", end="")
    parameters = update.message.text.replace('/jm ', '')
    # catch /jm listcache and /jm clearcache
    if parameters == "listcache":
        print("listcache.")
        await jm_list_cache(update, context)
        return
    if parameters == "clearcache":
        print("clearcache.")
        await jm_clear_cache(update, context)
        return
    # if comic id is not digit
    if not parameters.isdigit():
        print(datetime.datetime.now(), "\t", "Invalid comic_id. Showing usage.")
        await update.message.reply_text(usage_msg)
        return
    print("Trying to download jm " + parameters)
    await update.message.reply_text(f"Downloading comic {update.message.text.replace('/jm ', '')}...")
    # if the comic is already in ./download, send it directly
    if os.path.exists(os.path.join(os.path.dirname(temp_download_path), f"{parameters}.pdf")):
        print(datetime.datetime.now(), "\t", "[jm] Comic " + parameters + " already exists, sending it directly.")
        with open(os.path.join(os.path.dirname(temp_download_path), f"{parameters}.pdf"), 'rb') as pdf_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file)
        return
    # otherwise, create a background task and download the comic
    asyncio.create_task(jm_comic_download(parameters, update, context))

async def jm_comic_download(comic_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "[jm] A new thread started to download comic " + comic_id)
    # if comic exists, send it directly
    pdf_path = os.path.join(temp_download_path, f"{comic_id}.pdf")
    if os.path.exists(pdf_path):
        print(datetime.datetime.now(), "\t", "[jm] Comic " + comic_id + " already exists, sending it directly.")
        with open(pdf_path, 'rb') as pdf_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file)
        print(datetime.datetime.now(), "\t", "[jm] Comic " + comic_id + " sent to chat.")
        return
    # if comic not exist, download
    try:
        pdf_filename = await asyncio.to_thread(download_comic, comic_id)
        full_pdf_path = os.path.join(temp_download_path, pdf_filename)
        with open(full_pdf_path, 'rb') as pdf_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file)
        print(datetime.datetime.now(), "\t", "[jm] Comic " + comic_id + " sent to chat.")

    except telegram.error.TimedOut:
        pass    # This error is expected when the download takes too long, we will just ignore it
    except telegram.error.NetworkError as e:
        if "Request Entity Too Large" in str(e):
            print("[jm] Error: File size exceeds the limit.")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: File is too large to send.")
        else:
            print("[jm] NetworkError: ", e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="NetworkError: " + str(e))
    except Exception as e:
        print("[jm] Error: ", e)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e))

async def jm_list_cache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = os.listdir(os.path.dirname(temp_download_path))
    pdf_files = [f for f in files if f.endswith('.pdf')]
    if not pdf_files:
        await update.message.reply_text("No cached comics found.")
        return
    reply_text = "Cached comics:\n" + "\n".join(pdf_files)
    await update.message.reply_text(reply_text)

async def jm_clear_cache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = os.listdir(os.path.dirname(temp_download_path))
    pdf_files = [f for f in files if f.endswith('.pdf')]
    if not pdf_files:
        await update.message.reply_text("No cached comics to delete.")
        return
    for f in pdf_files:
        print(f"[jm] Deleting cached comic: {f}")
        os.remove(os.path.join(os.path.dirname(temp_download_path), f))
    await update.message.reply_text("Cleared all cached comics.")


# for test only
# download_comic(422866)
