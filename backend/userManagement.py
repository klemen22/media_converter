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
    # welcome to if city brother (try to fix this slop later)
    while True:

        print(
            "\nAllowed actions:\nID (1) - Delete new user\nID (2) - Approve new user.\nID (3) - Remove existing user\nID (4) - Exit"
        )
        selectedActions = int(input("\nInput ID of desired action: "))

        if selectedActions in [1, 2]:

            users = getUsers(table="new_users")
            if not users:
                print("No new users found.")
                break

            for user in users:
                print(
                    f"ID: {user[0]}, username: {user[1]}, email: {user[2]}, password: {user[3]}, timestamp: {user[4]}"
                )

            if selectedActions == 1:
                selectedUser = input(
                    "\nEnter user ID to delete a new user (enter 'exit' to exit): "
                )
            elif selectedActions == 2:
                selectedUser = input(
                    "\nEnter user ID to approve a new user (enter 'exit' to exit): "
                )

            if selectedUser.lower() == "exit":
                print("\nEnding...")
                break
            elif not selectedUser.isdigit():
                print("\nInvalid ID!")
                break
            elif selectedActions == 1:
                userID = int(selectedUser)
                deleteUser(id=userID, table="new_users")
            elif selectedActions == 2:
                userID = int(selectedUser)
                approveNewUser(userID=userID)

        elif selectedActions == 3:

            users = getUsers(table="approved_users")
            if not users:
                print("No users found.")
                break

            for user in users:
                print(
                    f"ID: {user[0]}, username: {user[1]}, email: {user[2]}, password: {user[3]}"
                )
            selectedUser = input(
                "\nEnter user ID to delete an approved user (enter 'exit' to exit): "
            )

            if selectedUser.lower() == "exit":
                print("Ending...")
                break
            elif not selectedUser.isdigit():
                print("Invalid ID!")
                break
            else:
                userID = int(selectedUser)
                deleteUser(id=userID, table="approved_users")

        elif selectedActions == 4:
            print("\nEnding...")
            break
        else:
            print("Invalid actions ID.")
            break
