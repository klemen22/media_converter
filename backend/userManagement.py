from database import getUsers, registerNewUser, deleteUser


def approveNewUser(userID):
    user = getUsers(table="new_users", id=userID)

    registerNewUser(
        username=user[1], email=user[2], password=user[3], table="approved_users"
    )

    flag = deleteUser(id=userID, table="new_users")

    if flag:
        print(f"User with ID {userID} was approved!")
    else:
        print(f"User was not found.")


if __name__ == "__main__":

    while True:
        users = getUsers(table="new_users")

        if not users:
            print("No new users found.")

        for user in users:
            print(
                f"ID: {user[0]}, username: {user[1]}, email: {user[2]}, password: {user[3]}, timestamp: {user[4]}"
            )

        selectedUser = input(
            "Enter user ID to approve a new user (enter 'exit' to exit): "
        )

        if selectedUser.lower() is "exit":
            break
        elif not selectedUser.isdigit():
            print("Error: enter a valid ID.")
        else:
            userID = int(selectedUser)
            approveNewUser(userID=userID)
