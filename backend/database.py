import sqlite3
from datetime import datetime

DB_PATH = "logs.db"

# -------------------------------------------------------------------------------------------#
#                                     DB initialization                                      #
# -------------------------------------------------------------------------------------------#


def initializeDB():
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    # ---------------------------Youtube------------------------- #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS yt_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_title TEXT,
            format TEXT,
            timestamp TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS yt_stats (
            id INTEGER PRIMARY KEY,
            total_conversions INTEGER,
            number_of_mp3 INTEGER,
            number_of_mp4 INTEGER
        )
        """
    )

    # initialize table
    cursor.execute("SELECT COUNT(*) FROM yt_stats")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO yt_stats VALUES (1, 0, 0, 0)")

    # --------------------------Instagram------------------------- #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS insta_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_title TEXT,
            type TEXT,
            timestamp TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS insta_stats (
            id INTEGER PRIMARY KEY,
            total_conversions INTEGER,
            number_of_video INTEGER,
            number_of_picture INTEGER
        )
        """
    )

    # initialize table
    cursor.execute("SELECT COUNT(*) FROM insta_stats")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO insta_stats VALUES (1, 0, 0, 0)")

    # ---------------------------TikTok-------------------------- #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tiktok_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_title TEXT,
            timestamp TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tiktok_stats (
            id INTEGER PRIMARY KEY,
            total_conversions INTEGER
        )
        """
    )

    # initialize table
    cursor.execute("SELECT COUNT(*) FROM tiktok_stats")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO tiktok_stats VALUES (1, 0)")

    connect.commit()
    connect.close()


# -------------------------------------------------------------------------------------------#
#                                        Youtube logs                                        #
# -------------------------------------------------------------------------------------------#


def saveConversion(title, format):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    timeStamp = datetime.now().strftime("%d. %B %Y %H:%M:%S")

    cursor.execute(
        "INSERT INTO yt_logs (video_title, format, timestamp) VALUES (?, ?, ?)",
        (title, format, timeStamp),
    )

    if format == "mp3":
        cursor.execute(
            "UPDATE yt_stats SET number_of_mp3 = number_of_mp3 + 1 WHERE id = 1"
        )
    else:
        cursor.execute(
            "UPDATE yt_stats SET number_of_mp4 = number_of_mp4 + 1 WHERE id = 1"
        )

    cursor.execute(
        "UPDATE yt_stats SET total_conversions = total_conversions + 1 WHERE id = 1"
    )

    connect.commit()
    connect.close()


# -------------------------------------------------------------------------------------------#
#                                         Instagram logs                                     #
# -------------------------------------------------------------------------------------------#


def saveInstaConversion(title, type):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    timeStamp = datetime.now().strftime("%d. %B %Y %H:%M:%S")

    cursor.execute(
        "INSERT INTO insta_logs (content_title, type, timestamp) VALUES (?, ?, ?)",
        (title, type, timeStamp),
    )

    if type == "video":
        cursor.execute(
            "UPDATE insta_stats SET number_of_video = number_of_video + 1 WHERE id = 1"
        )
    else:
        cursor.execute(
            "UPDATE insta_stats SET number_of_picture = number_of_picture + 1 WHERE id = 1"
        )

    cursor.execute(
        "UPDATE insta_stats SET total_conversions = total_conversions + 1 WHERE id = 1"
    )

    connect.commit()
    connect.close()


# -------------------------------------------------------------------------------------------#
#                                           TikTok logs                                      #
# -------------------------------------------------------------------------------------------#


def saveTiktokConversion(title):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    timeStamp = datetime.now().strftime("%d. %B %Y %H:%M:%S")

    cursor.execute(
        "INSERT INTO tiktok_logs (content_title, timestamp) VALUES (?, ?)",
        (title, timeStamp),
    )

    cursor.execute(
        "UPDATE tiktok_stats SET total_conversions = total_conversions + 1 WHERE id = 1"
    )

    connect.commit()
    connect.close()


# -------------------------------------------------------------------------------------------#
#                                       Universal functions                                  #
# -------------------------------------------------------------------------------------------#


def getLogs(table):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    if table == "youtube":
        cursor.execute("SELECT * FROM yt_logs")
    elif table == "instagram":
        cursor.execute("SELECT * FROM insta_logs")
    else:
        cursor.execute("SELECT * FROM tiktok_logs")

    data = cursor.fetchall()
    connect.close()
    return data


def getStats(table):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    if table == "youtube":
        cursor.execute("SELECT * FROM yt_stats WHERE id = 1")
    elif table == "instagram":
        cursor.execute("SELECT * FROM insta_stats WHERE id = 1")
    else:
        cursor.execute("SELECT * FROM tiktok_stats WHERE id = 1")

    stats = cursor.fetchone()
    connect.close()
    return stats
