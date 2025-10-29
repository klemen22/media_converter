# -------------------------------------------------------------------------------------------#
#                                         Imports                                            #
# -------------------------------------------------------------------------------------------#

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL
from fastapi.responses import FileResponse
import os
import re
import threading
import time
import hashlib
import random
from database import initializeDB, saveConversion, getLogs, getStats
import instaloader

initializeDB()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# download dir for youtube
downloadDir = "downloads"
if os.path.exists(downloadDir) == False:
    os.mkdir(downloadDir)

# download dir for instagram
downloadDirInsta = "downloads_instagram"
if os.path.exists(downloadDirInsta) == False:
    os.mkdir(downloadDirInsta)


class request(BaseModel):
    url: str
    format: str
    resolution: str | None = None


# -------------------------------------------------------------------------------------------#
#                                     API calls - Youtube                                    #
# -------------------------------------------------------------------------------------------#
# TODO: changes "status" into actual HTTP status codes


@app.post("/api/convert")
async def convertVideo(payload: request):
    print("Payload retrieved!", payload)

    uniqueHash = generateHash()
    ydl_opts = {}

    if payload.format == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(downloadDir, f"%(title)s_{uniqueHash}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "postprocessor_cleanup": True,
            "rm_cache_dir": True,
            "no_cache_dir": True,
            "cachedir": False,
            "nopart": True,
            "noplaylist": True,
        }

    elif payload.format == "mp4":
        resolution = payload.resolution or "best"
        ydl_opts = {
            "format": f"bestvideo[height<={resolution}]+bestaudio/best",
            "outtmpl": os.path.join(downloadDir, f"%(title)s_{uniqueHash}.%(ext)s"),
            "merge_output_format": "mp4",
            "postprocessor_cleanup": True,
            "rm_cache_dir": True,
            "no_cache_dir": True,
            "cachedir": False,
            "nopart": True,
            "noplaylist": True,
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.url, download=True)
            filename = ydl.prepare_filename(info)
            if filename is None:
                raise ValueError("Filename could not be determined.")
            if payload.format == "mp3":
                filename = filename.rsplit(".", 1)[0] + ".mp3"
            cleanName = os.path.basename(filename)
            saveConversion(cleanName, payload.format)
        return {
            "status": "success",
            "message": "Download complete",
            "filename": cleanName,
        }
    except Exception as e:
        print("Error while downloading: ", e)
        return {"status": "error", "message": str(e)}


@app.get("/api/download/{filename}")
def downloadFile(filename: str):
    filePath = os.path.join(downloadDir, filename)
    if os.path.exists(filePath):
        return FileResponse(
            path=filePath, filename=filename, media_type="application/octet-stream"
        )
    else:
        return {"status": "error", "message": "File not found"}


@app.delete("/api/delete/{filename}")
async def deleteFile(filename: str):
    filePath = os.path.join(downloadDir, filename)
    try:
        if os.path.exists(filePath):
            os.remove(filePath)
            return {"status": "deleted"}
        else:
            return {"status": "not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/logs")
def downloadLogs():
    try:
        logs = getLogs()
        logsFilePath = "downloads/logs.txt"
        with open(logsFilePath, "w", encoding="utf-8") as temp:
            for row in logs:
                temp.write(f"{row}\n")
        return FileResponse(
            path=logsFilePath, filename="logs.txt", media_type="text/plain"
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/stats")
def downloadStats():
    try:
        stats = getStats()
        return {
            "status": "success",
            "total_conversions": stats[1],
            "number_of_mp3": stats[2],
            "number_of_mp4": stats[3],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------------------------------------------------------------------------------#
#                                   API calls - Instagram                                    #
# -------------------------------------------------------------------------------------------#


class InstagramRequest(BaseModel):
    url: str
    type: str


class InstagramFilesRequest(BaseModel):
    filenames: list[str]


@app.post("/api/instagram/convert")
async def convertInstagramContent(payload: InstagramRequest):
    print("Payload:", payload)

    if payload.type == "video":
        loader = instaloader.Instaloader(
            download_comments=False,
            download_geotags=False,
            download_pictures=False,
            download_video_thumbnails=False,
            download_videos=True,
            save_metadata=False,
            post_metadata_txt_pattern="",
        )
    elif payload.type == "picture":
        loader = instaloader.Instaloader(
            download_comments=False,
            download_geotags=False,
            download_pictures=True,
            download_video_thumbnails=False,
            download_videos=False,
            save_metadata=False,
            post_metadata_txt_pattern="",
        )
    else:
        return {"status": "error", "message": "invalid content type"}

    contentURL = payload.url
    shortCode = contentURL.split("/")[-2]
    fileNames = []

    try:
        post = instaloader.Post.from_shortcode(
            context=loader.context, shortcode=shortCode
        )

        if post.typename == "GraphSidecar":
            for index, node in enumerate(post.get_sidecar_nodes(), start=1):
                if payload.type == "video":
                    fileExt = ".mp4"
                    contentID = f"instagram_video_{index}_{generateHash()}"
                    fileURL = node.video_url
                else:
                    fileExt = ".jpg"
                    contentID = f"instagram_picture_{index}_{generateHash()}"
                    fileURL = node.display_url

                filePath = os.path.join(downloadDirInsta, contentID)
                loader.download_pic(
                    filename=filePath, url=fileURL, mtime=post.date_local
                )
                fileNames.append(contentID + fileExt)
        else:
            if payload.type == "video":
                fileExt = ".mp4"
                contentID = f"instagram_video_{generateHash()}"
                fileURL = post.video_url

            else:
                fileExt = ".jpg"
                contentID = f"instagram_picture_{generateHash()}"
                fileURL = post.url

            filePath = os.path.join(downloadDirInsta, contentID)
            loader.download_pic(filename=filePath, url=fileURL, mtime=post.date_local)
            fileNames.append(contentID + fileExt)

        return {
            "status": "success",
            "message": "download complete",
            "filenames": fileNames,
            "num": len(fileNames),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# TODO: fix download API call for multiple files request (for reference look at delete API call), also pack more files into a zip file or something
@app.get("/api/instagram/download/{filename}")
def downloadInstagramContent(filename: str):
    filePath = os.path.join(downloadDirInsta, filename)

    if os.path.exists(filePath):
        return FileResponse(
            path=filePath, filename=filename, media_type="application/octet-stream"
        )
    else:
        return {"status": "error", "message": "File not found"}


@app.delete("/api/instagram/delete")
async def deleteInstagramContent(request: InstagramFilesRequest):
    deletedFiles = []
    lostFiles = []
    try:
        for filename in request.filenames:
            filePath = os.path.join(downloadDirInsta, filename)

            if os.path.exists(filePath):
                os.remove(filePath)
                deletedFiles.append(filename)
            else:
                lostFiles.append(filename)

        return {
            "status": "success",
            "message": "delete complete",
            "deleted files": deletedFiles,
            "lost files": lostFiles,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------------------------------------------------------------------------------#
#                                    Garbage collector                                       #
# -------------------------------------------------------------------------------------------#


def deleteGarbage():
    # on set interval delete all files / leftovers in downloads folder

    while True:
        startInt = time.time()
        endInt = startInt - 30 * 60

        filesList = os.listdir(downloadDir)

        for file in filesList:
            filePath = os.path.join(downloadDir, file)
            if os.path.isfile(filePath):
                if os.path.getatime(filePath) < endInt:
                    try:
                        os.remove(filePath)
                        print(f"Deleted old file: {file}")
                    except Exception as e:
                        print(f"Error deleting {file}: {e}")

        time.sleep(600)


# start new thread
threading.Thread(target=deleteGarbage, daemon=True).start()


# -------------------------------------------------------------------------------------------#
#                                     Helper functions                                       #
# -------------------------------------------------------------------------------------------#


def generateHash():
    uniqueHash = hashlib.sha1(str(random.random()).encode()).hexdigest()[:8]
    return uniqueHash
