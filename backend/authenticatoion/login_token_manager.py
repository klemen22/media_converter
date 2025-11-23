import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from database import getUsers

load_dotenv()

SECRET_KEY = os.getenv(key="SECRET_KEY")
ALGORITHM = os.getenv(key="ALGORITHM")
TOKEN_EXPIRE = os.getenv(key="TOKEN_EXPIRE")

oauth2Scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# -------------------------------------------------------------------------------------------#
#                                       Create token                                         #
# -------------------------------------------------------------------------------------------#


from datetime import datetime, timedelta, timezone


def createToken(data: dict):
    encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=int(TOKEN_EXPIRE))
    encode.update({"exp": expire})
    encodedJWT = jwt.encode(encode, key=SECRET_KEY, algorithm=ALGORITHM)

    return encodedJWT


# -------------------------------------------------------------------------------------------#
#                                        Decode token                                        #
# -------------------------------------------------------------------------------------------#


def checkTokenUser(token: str = Depends(oauth2Scheme)):
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return {"status": "error", "message": "Could not valiedate the user."}
        return username

    except JWTError:
        return {"status": "error", "message": str(JWTError)}


# -------------------------------------------------------------------------------------------#
#                                      Get user from token                                   #
# -------------------------------------------------------------------------------------------#


def getUserFromToken(currentUser: str = Depends(checkTokenUser)):
    if isinstance(currentUser, dict) and currentUser.get("status") == "error":
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": f"{currentUser.get("message")}"},
        )
    user = getUsers(table="approved_users", username=currentUser)

    if user:
        return user[0]
    else:
        return JSONResponse(
            status_code=404, content={"status": "error", "message": "User not found!"}
        )
