# TODO: Fix / change formating of api requests for youtube videos
# TODO: creater or add seperate login function

# -------------------------------------------------------------------------------------------#
#                                         Imports                                            #
# -------------------------------------------------------------------------------------------#

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL
from fastapi.responses import FileResponse
import os
import threading
import time
import hashlib
import random
import bcrypt
from database import (
    initializeDB,
    saveConversion,
    getLogs,
    getStats,
    saveInstaConversion,
    saveTiktokConversion,
    registerNewUser,
    searchUser,
    getUsers,
)
import instaloader
import shutil
from authenticatoion.login_token_manager import createToken, getTokenUser

initializeDB()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # spicy setting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# download dir for youtube
downloadDir = "downloads_youtube"
if os.path.exists(downloadDir) == False:
    os.mkdir(downloadDir)

# download dir for instagram
downloadDirInsta = "downloads_instagram"
if os.path.exists(downloadDirInsta) == False:
    os.mkdir(downloadDirInsta)

# download dir for tiktok
downloadDirTikTok = "downloads_tiktok"
if os.path.exists(downloadDirTikTok) == False:
    os.mkdir(downloadDirTikTok)

downloadDirs = ["downloads_youtube", "downloads_instagram", "downloads_tiktok"]


# -------------------------------------------------------------------------------------------#
#                                     API calls - Youtube                                    #
# -------------------------------------------------------------------------------------------#


class youtubeConvert(BaseModel):
    url: str
    format: str
    resolution: str | None = None


class youtubeContentRequest(BaseModel):
    filename: str


@app.post("/api/youtube/convert")
async def convertVideo(payload: youtubeConvert):

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


@app.post("/api/youtube/download")
def downloadFile(payload: youtubeContentRequest):
    filePath = os.path.join(downloadDir, payload.filename)
    if os.path.exists(filePath):
        return FileResponse(
            path=filePath,
            filename=payload.filename,
            media_type="application/octet-stream",
        )
    else:
        return {"status": "error", "message": "File not found"}


@app.delete("/api/youtube/delete")
async def deleteFile(payload: youtubeContentRequest):
    filePath = os.path.join(downloadDir, payload.filename)
    try:
        if os.path.exists(filePath):
            os.remove(filePath)
            return {"status": "deleted"}
        else:
            return {"status": "not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------------------------------------------------------------------------------#
#                                   API calls - Instagram                                    #
# -------------------------------------------------------------------------------------------#


class InstagramRequest(BaseModel):
    url: str
    type: str


class InstagramFilesRequest(BaseModel):
    filename: str


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
                if fileExt == ".mp4":
                    saveInstaConversion(title=contentID, type="video")
                else:
                    saveInstaConversion(title=contentID, type="picture")
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
            if fileExt == ".mp4":
                saveInstaConversion(title=contentID, type="video")
            else:
                saveInstaConversion(title=contentID, type="picture")

        if len(fileNames) > 1:
            archiveHash = generateHash()
            archivePath = os.path.join(
                downloadDirInsta, f"instagram_content_{archiveHash}"
            )
            os.makedirs(archivePath, exist_ok=True)
            archiveName = f"instagram_{archiveHash}.zip"
            archiveFullPath = os.path.join(downloadDirInsta, archiveName)
            for fileName in fileNames:
                shutil.move(
                    os.path.join(downloadDirInsta, fileName),
                    os.path.join(archivePath, fileName),
                )

            shutil.make_archive(
                base_name=os.path.splitext(archiveFullPath)[0],
                format="zip",
                root_dir=archivePath,
            )

            shutil.rmtree(archivePath)
            return {
                "status": "success",
                "message": "download complete",
                "filename": archiveName,
            }

        else:
            return {
                "status": "success",
                "message": "download complete",
                "filename": fileNames[0],
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/instagram/download")
async def downloadInstagramContent(payload: InstagramFilesRequest):
    filePath = os.path.join(downloadDirInsta, payload.filename)
    if os.path.exists(filePath):
        media_type = (
            "application/zip"
            if filePath.endswith(".zip")
            else "application/octet-stream"
        )
        return FileResponse(
            path=filePath, filename=payload.filename, media_type=media_type
        )
    else:
        return {"status": "error", "message": "not found"}


@app.delete("/api/instagram/delete")
async def deleteInstagramContent(payload: InstagramFilesRequest):
    filePath = os.path.join(downloadDirInsta, payload.filename)
    try:
        if os.path.exists(filePath):
            os.remove(filePath)
            return {"status": "deleted"}
        else:
            return {"status": "error", "message": "not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------------------------------------------------------------------------------#
#                                   API calls - TikTok                                       #
# -------------------------------------------------------------------------------------------#
class tiktokConvertRequest(BaseModel):
    url: str


class tiktokDownloadRequest(BaseModel):
    filename: str


@app.post("/api/tiktok/convert")
async def convertTiktokContent(payload: tiktokConvertRequest):
    filePath = os.path.join(
        downloadDirTikTok, "%(title)s_" + generateHash() + ".%(ext)s"
    )

    ydl_opts = {
        "outtmpl": filePath,
        "format": "mp4",
        "noplaylist": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.url, download=True)
            filename = ydl.prepare_filename(info)
            cleanName = os.path.basename(filename)

            saveTiktokConversion(title=cleanName)

            return {
                "status": "success",
                "message": "Download complete",
                "filename": cleanName,
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/tiktok/download")
def downloadkTikTokContent(request: tiktokDownloadRequest):
    filePath = os.path.join(downloadDirTikTok, request.filename)

    print(filePath)

    if os.path.exists(filePath):
        return FileResponse(
            path=filePath,
            filename=request.filename,
            media_type="application/octet-stream",
        )
    else:
        return {"status": "error", "message": "File not found"}


@app.delete("/api/tiktok/delete")
async def deleteTiktokContent(request: tiktokDownloadRequest):
    filePath = os.path.join(downloadDirTikTok, request.filename)

    try:
        if os.path.exists(filePath):
            os.remove(filePath)
            return {"status": "deleted"}
        else:
            return {"status": "error", "message": "File not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------------------------------------------------------------------------------#
#                                       Logs & stats                                         #
# -------------------------------------------------------------------------------------------#


class statsRequest(BaseModel):
    table: str


@app.post("/api/logs")
def downloadLogs(payload: statsRequest):

    if payload.table == "youtube":
        type = "youtube"
    elif payload.table == "instagram":
        type = "instagram"
    elif payload.table == "tiktok":
        type = "tiktok"
    else:
        return {"status": "error", "message": "unknown table"}

    try:
        logs = getLogs(table=type)
        logsFilePath = f"downloads_{type}/{type}_logs.txt"
        with open(logsFilePath, "w", encoding="utf-8") as temp:
            for row in logs:
                temp.write(f"{row}\n")
        return FileResponse(
            path=logsFilePath, filename="logs.txt", media_type="text/plain"
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/stats")
def downloadStats(payload: statsRequest):
    try:
        stats = getStats(platform=payload.table)

        if stats is None:
            return {"status": "error", "message": "unknown table"}

        (
            _,
            title,
            total_conversions,
            number_of_mp3,
            number_of_mp4,
            number_of_video,
            number_of_picture,
        ) = stats

        if title == "youtube":
            return {
                "status": "success",
                "total_conversions": total_conversions,
                "number_of_mp3": number_of_mp3,
                "number_of_mp4": number_of_mp4,
            }
        elif title == "instagram":
            return {
                "status": "success",
                "total_conversions": total_conversions,
                "number_of_video": number_of_video,
                "number_of_picture": number_of_picture,
            }
        elif title == "tiktok":
            return {
                "status": "success",
                "total_conversions": total_conversions,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------------------------------------------------------------------------------#
#                                     Login & register                                       #
# -------------------------------------------------------------------------------------------#


class registerUserRequest(BaseModel):
    username: str
    email: str
    password: str


class loginUserRequest(BaseModel):
    username: str
    password: str


@app.post("/api/register")
def registerUser(payload: registerUserRequest):
    try:
        print(f"recieved payload: {payload}")
        userExists = searchUser(username=payload.username, email=payload.email)
        print(f"user exists: {userExists} ")

        if userExists:
            print("User already exists!")
            return {"status": "error", "message": "User already exists."}
        else:
            # hashedPassword = hashPassword(password=payload.password)
            hashedPassword = hashPassword(payload.password)  # for debugging
            print(f"Hashed password: {hashedPassword}")  # debug

            registerNewUser(
                username=payload.username,
                email=payload.email,
                password=hashedPassword,
                table="new_users",
            )
            print("new user registered")
            return {"status": "success", "message": "Registration successful."}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/login")
def loginUser(payload: loginUserRequest):

    try:
        registeredUser = getUsers(table="approved_users", username=payload.username)
        print(f"Retrieved user:\n{registeredUser}")

        if not registeredUser:
            print("User doesnt't exist.")
            return {"status": "error", "message": "User doens't exist!"}
        else:
            # if user exists compare passwords
            (_, _, _, registeredPassword) = registeredUser

            if checkPassword(
                loginPassword=payload.password, storedPassword=registeredPassword
            ):
                token = createToken({"sub": payload.username})
                return {
                    "status": "success",
                    "message": "Login successful!",
                    "access_token": token,
                    "token_type": "bearer",
                }
            else:
                return {
                    "status": "invalid",
                    "message": "Username or password is incorrect!",
                }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/user_info")  # validating token
def getUserInfo(currentUser: str = Depends(getTokenUser)):
    return {"status": "success", "user": currentUser}


# -------------------------------------------------------------------------------------------#
#                                    Garbage collector                                       #
# -------------------------------------------------------------------------------------------#
# on set interval delete all files / leftovers in downloads folder


def deleteGarbage():
    while True:
        startInt = time.time()
        endInt = startInt - 30 * 60

        for downloadDir in downloadDirs:
            if not os.path.exists(downloadDir):
                continue

            filesList = os.listdir(downloadDir)

            for file in filesList:
                if file == ".gitkeep":
                    continue

                filePath = os.path.join(downloadDir, file)
                if os.path.isfile(filePath):
                    if os.path.getatime(filePath) < endInt:
                        try:
                            os.remove(filePath)
                            print(f"Deleted old file: {filePath}")
                        except Exception as e:
                            print(f"Error deleting {filePath}: {e}")

        time.sleep(600)


# start new thread
threading.Thread(target=deleteGarbage, daemon=True).start()


# -------------------------------------------------------------------------------------------#
#                                     Helper functions                                       #
# -------------------------------------------------------------------------------------------#


def generateHash():
    uniqueHash = hashlib.sha1(str(random.random()).encode()).hexdigest()[:8]
    return uniqueHash


def hashPassword(password: str) -> str:
    passwordBytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(passwordBytes, salt)
    return hashed.decode("utf-8")


def checkPassword(loginPassword, storedPassword):
    loginPasswordBytes = loginPassword.encode("utf-8")
    storedPasswordBytes = storedPassword.encode("utf-8")
    return bcrypt.checkpw(
        password=loginPasswordBytes, hashed_password=storedPasswordBytes
    )
