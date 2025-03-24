import jmcomic
import os
from PIL import Image
from PyPDF2 import PdfMerger

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
    option = jmcomic.create_option_by_file('jm_dl_option.yml')
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


# for test only
# download_comic(422866)
