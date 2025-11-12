//-----------------------------------------------------------------------------------//
//                                  DOM Elements                                     //
//-----------------------------------------------------------------------------------//

const registerUsername = document.getElementById("register_username");
const registerEmail = document.getElementById("register_email");
const registerPassword = document.getElementById("register_password");
const registerConfirmPassword = document.getElementById(
  "register_confirm_password"
);
const registerButton = document.getElementById("register_button");
const registerResult = document.getElementById("register_result");
const registerInvalid = document.getElementById("register_invalid");
const baseURL = `${window.location.protocol}//${window.location.hostname}:8000`;

document.addEventListener("DOMContentLoaded", () => {
  registerResult.hidden = true;
  registerInvalid.hidden = true;
  registerButton.addEventListener("click", async () => {
    const username = registerUsername.value.trim();
    const password = registerPassword.value.trim();
    const confirmPassword = registerConfirmPassword.value.trim();
    const email = registerEmail.value.trim();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (username == "") {
      registerInvalid.hidden = false;
      registerInvalid.innerHTML = "Username is empty!";
      return;
    } else if (password == "") {
      registerInvalid.hidden = false;
      registerInvalid.innerHTML = "Password field is empty!";
      return;
    } else if (!emailPattern.test(email)) {
      registerInvalid.hidden = false;
      registerInvalid.innerHTML = "Invalid email!";
      return;
    } else if (password != confirmPassword) {
      registerInvalid.hidden = false;
      registerInvalid.innerHTML = "Passwords are not matching!";
      return;
    }

    registerInvalid.hidden = true;
    sendPayload(username, email, password);
  });
});

async function sendPayload(username, email, password) {
  const payload = {
    username: username,
    email: email,
    password: password,
  };
  console.log("Payload: ", payload);
  try {
    const response = await fetch(`${baseURL}/api/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (response.ok) {
      registerResult.hidden = false;
      registerResult.innerHTML = "Registration submitted for approval.";
      setTimeout(() => {
        window.location.href = "index.html";
      }, 5000);
    } else {
      registerResult.hidden = false;
      registerResult.innerHTML = data.message;
    }
  } catch (error) {
    console.error("Error:", error);
    registerResult.hidden = false;
    registerResult.innerHTML = str(error);
  }
}
