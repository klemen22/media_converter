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

    # -------------------------Stats---------------------------#

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            total_conversions INTEGER DEFAULT 0,
            number_of_mp3 INTEGER DEFAULT 0,
            number_of_mp4 INTEGER DEFAULT 0,
            number_of_video INTEGER DEFAULT 0,
            number_of_picture INTEGER DEFAULT 0
        )
        """
    )

    rowNames = ["youtube", "instagram", "tiktok"]

    for row in rowNames:
        cursor.execute("SELECT id FROM stats WHERE title = ?", (row,))

        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT OR IGNORE INTO stats (title, total_conversions, number_of_mp3, number_of_mp4, number_of_video, number_of_picture) VALUES (?, 0, 0, 0, 0, 0)",
                (row,),
            )
    # ------------------------Users---------------------------#
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS new_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT,
            timestamp TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS approved_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
        """
    )

    connect.commit()
    connect.close()


# -------------------------------------------------------------------------------------------#
#                                        Youtube logs                                        #
# -------------------------------------------------------------------------------------------#


def saveConversion(title, format):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    timeStamp = datetime.now().strftime("%d. %B %Y %H:%M:%S")

    # Shrani v log tabelo
    cursor.execute(
        "INSERT INTO yt_logs (video_title, format, timestamp) VALUES (?, ?, ?)",
        (title, format, timeStamp),
    )

    # Posodobi stats tabelo
    if format == "mp3":
        cursor.execute(
            "UPDATE stats SET number_of_mp3 = number_of_mp3 + 1, total_conversions = total_conversions + 1 WHERE title = 'youtube'"
        )
    else:
        cursor.execute(
            "UPDATE stats SET number_of_mp4 = number_of_mp4 + 1, total_conversions = total_conversions + 1 WHERE title = 'youtube'"
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

    # Shrani v log tabelo
    cursor.execute(
        "INSERT INTO insta_logs (content_title, type, timestamp) VALUES (?, ?, ?)",
        (title, type, timeStamp),
    )

    # Posodobi stats tabelo
    if type == "video":
        cursor.execute(
            "UPDATE stats SET number_of_video = number_of_video + 1, total_conversions = total_conversions + 1 WHERE title = 'instagram'"
        )
    else:
        cursor.execute(
            "UPDATE stats SET number_of_picture = number_of_picture + 1, total_conversions = total_conversions + 1 WHERE title = 'instagram'"
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

    # Shrani v log tabelo
    cursor.execute(
        "INSERT INTO tiktok_logs (content_title, timestamp) VALUES (?, ?)",
        (title, timeStamp),
    )

    # Posodobi stats tabelo
    cursor.execute(
        "UPDATE stats SET total_conversions = total_conversions + 1 WHERE title = 'tiktok'"
    )

    connect.commit()
    connect.close()


# -------------------------------------------------------------------------------------------#
#                                           Users                                            #
# -------------------------------------------------------------------------------------------#


def registerNewUser(username, email, password, table):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    timeStamp = datetime.now().strftime("%d. %B %Y %H:%M:%S")

    if table == "new_users":
        cursor.execute(
            "INSERT INTO new_users (username, email, password, timestamp) VALUES (?, ?, ?, ?)",
            (username, email, password, timeStamp),
        )
    elif table == "approved_users":
        cursor.execute(
            "INSERT INTO approved_users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password),
        )

    connect.commit()
    connect.close()


def getUsers(table, id=None, username=None):
    allowed_tables = ["new_users", "approved_users"]
    if table not in allowed_tables:
        raise ValueError("Invalid table name! >:(")

    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    try:
        if id is None and username is None:
            cursor.execute(f"SELECT * FROM {table}")
            users = cursor.fetchall()
        elif id is None:
            cursor.execute(f"SELECT * FROM {table} WHERE username = ?", (username,))
            users = cursor.fetchone()
        else:
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (id,))
            users = cursor.fetchone()
    finally:
        connect.close()
    return users


def searchUser(username, email):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    cursor.execute(
        "SELECT * FROM approved_users WHERE username = ? OR email = ?",
        (username, email),
    )
    approvedUser = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM new_users WHERE username = ? OR email = ?",
        (username, email),
    )
    newUser = cursor.fetchone()

    connect.close()

    if approvedUser or newUser:
        return True
    else:
        return False


def deleteUser(id, table):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    allowed_tables = ["new_users", "approved_users"]

    if table not in allowed_tables:
        return ValueError("Invalid table name! >:(")

    cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (id,))
    selectedUser = cursor.fetchone()

    if not selectedUser:
        connect.close()
        return False
    else:
        cursor.execute(f"DELETE FROM {table} WHERE id = ?", (id,))

    connect.commit()
    connect.close()

    return True


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


def getStats(platform):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    cursor.execute("SELECT * FROM stats WHERE title = ?", (platform,))
    stats = cursor.fetchone()
    connect.close()

    return stats
