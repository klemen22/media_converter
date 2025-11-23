//-----------------------------------------------------------------------------------//
//                                  DOM Elements                                     //
//-----------------------------------------------------------------------------------//

const loginUsername = document.getElementById("login_username");
const loginPassword = document.getElementById("login_password");
const loginButton = document.getElementById("login_button");
const loginInvalid = document.getElementById("login_invalid");
const baseURL = `${window.location.protocol}//${window.location.hostname}:9999`;

document.addEventListener("DOMContentLoaded", async () => {
  await checkToken();

  loginInvalid.hidden = true;

  loginButton.addEventListener("click", async () => {
    const username = loginUsername.value.trim();
    const password = loginPassword.value.trim();

    if (username == "" || password == "") {
      loginInvalid.hidden = false;
      loginInvalid.innerHTML =
        "Username or password is incorrect! (don't play around broski)";
    }

    loginInvalid.hidden = true;
    sendLoginPayload(username, password);
  });
});

async function sendLoginPayload(username, password) {
  const payload = {
    username: username,
    password: password,
  };
  console.log("Payload: ", payload);
  try {
    const response = await fetch(`${baseURL}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    console.log("Recieved data: \n", data);

    if (data.status == "success") {
      localStorage.setItem("access_token", data.access_token);
      window.location.href = "youtube_converter.html";
    } else if (data.status == "invalid") {
      loginInvalid.hidden = false;
      loginInvalid.innerHTML = data.message;
    } else {
      loginInvalid.hidden = false;
      loginInvalid.innerHTML = data.message;
    }
  } catch (error) {
    console.error("Error:", error);
    loginInvalid.hidden = false;
    loginInvalid.innerHTML = str(error);
  }
}

//-----------------------------------------------------------------------------------//
//                                     Token Check                                   //
//-----------------------------------------------------------------------------------//
async function checkToken() {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return;
  }

  try {
    const response = await fetch(`${baseURL}/api/user_info`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    data = await response.json();

    if (data.status != "success") {
      localStorage.removeItem("access_token");
    } else {
      window.location.href = "youtube_converter.html";
    }
  } catch (error) {
    console.log("Error: ", error);
  }
}
