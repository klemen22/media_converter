//-----------------------------------------------------------------------------------//
//                                  DOM Elements                                     //
//-----------------------------------------------------------------------------------//

const logsLink = document.getElementById("tiktok_logs_link");
const statsLink = document.getElementById("tiktok_stats_link");
const toastContainer = document.getElementById("tiktok_toast_container");
const toastTitle = document.getElementById("tiktok_toast_title");
const toastBody = document.getElementById("tiktok_toast_body");
const xMark = document.getElementById("tiktok_x_mark");
const results = document.getElementById("tiktok_convert_result");
const submitButton = document.getElementById("tiktok_submit_button");
const downloadButton = document.getElementById("tiktok_download_button");
const tiktokURL = document.getElementById("tiktok_url");
const invalidLinkFeedback = document.getElementById("tiktok_invalid_link");
const logoutBtn = document.getElementById("logoutBtn");
const activeUser = document.getElementById("activeUser");
const baseURL = `${window.location.protocol}//${window.location.hostname}:9999`;
let downloadUrl = null;
let filename = null;

document.addEventListener("DOMContentLoaded", async () => {
  await validateToken();

  invalidLinkFeedback.hidden = true;
  downloadButton.hidden = true;
  submitButton.hidden = false;
  submitButton.disabled = false;
  downloadButton.disabled = false;
  results.hidden = true;
  logsLink.disabled = false;
  toastContainer.classList.remove("slide-in");
  toastContainer.classList.remove("fade-out");

  if (tiktokURL.classList.contains("is-invalid")) {
    tiktokURL.classList.remove("is-invalid");
    invalidLinkFeedback.hidden = true;
  }

  logsLink.addEventListener("click", downloadLogs);
  statsLink.addEventListener("click", (e) => {
    e.preventDefault();
    showStatsToast();
  });

  xMark.addEventListener("click", hideToast);

  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("access_token");
    window.location.href = "index.html";
  });

  submitButton.addEventListener("click", async (event) => {
    console.log("Download");
    event.preventDefault();
    event.stopPropagation();
    submitRequest();
  });
});

//-----------------------------------------------------------------------------------//
//                                   Submit Request                                  //
//-----------------------------------------------------------------------------------//

async function submitRequest() {
  if (downloadUrl) {
    window.URL.revokeObjectURL(downloadUrl);
    downloadUrl = null;
    filename = null;
  }

  const url = tiktokURL.value.trim();

  if (!url.includes("https://www.tiktok.com/")) {
    tiktokURL.classList.add("is-invalid");
    invalidLinkFeedback.hidden = false;
    return;
  }

  tiktokURL.classList.remove("is-invalid");
  invalidLinkFeedback.hidden = true;
  submitButton.disabled = true;

  const payload = {
    url: url,
  };

  const token = localStorage.getItem("access_token");

  results.hidden = false;
  results.textContent = "Converting...";

  try {
    const response = await fetch(`${baseURL}/api/tiktok/convert`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
        Expires: "0",
      },
      body: JSON.stringify(payload),
    });

    if (response.ok == false) {
      results.textContent = "Error while sedning data!";
      console.log("Error while sending data!");
      return;
    }

    const data = await response.json();
    if (data.status == "success") {
      results.textContent = "Download is ready!";
      downloadButton.hidden = false;
      submitButton.hidden = true;

      downloadButton.addEventListener("click", async () => {
        downloadRequest(data);
      });
    } else {
      results.textContent = "Error: " + data.message;
    }
  } catch (error) {
    console.error("Error:", error);
    results.textContent = "Error with backend connection!";
  }
}

//-----------------------------------------------------------------------------------//
//                                  Download Request                                 //
//-----------------------------------------------------------------------------------//

async function downloadRequest(data) {
  const downloadLink = `${baseURL}/api/tiktok/download`;
  downloadButton.disabled = true;
  results.textContent = "Downloading...";
  try {
    const response = await fetch(downloadLink, {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename: data.filename }),
    });

    if (response.ok == false) {
      results.textContent = "Error downloading file!";
      downloadButton.disabled = false;
      return;
    }

    const blob = await response.blob();
    const objectURL = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    // create an invisible element to signalize when the download of the file is complete
    a.href = objectURL;
    a.download = data.filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(objectURL);

    results.textContent = "Download finished!";
    submitButton.disabled = false;
    submitButton.hidden = false;
    downloadButton.disabled = false;
    downloadButton.hidden = true;

    // send signal to backend to delete the file
    await fetch(`${baseURL}/api/tiktok/delete`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename: data.filename }),
    });
    window.location.reload();
  } catch (error) {
    console.error("Download error: ", error);
    results.textContent = "Error while downloading the file!";
    downloadButton.disabled = false;
  }
}

//-----------------------------------------------------------------------------------//
//                                    Download logs                                  //
//-----------------------------------------------------------------------------------//

async function downloadLogs() {
  logsLink.disabled = true;
  const token = localStorage.getItem("access_token");

  const resposne = await fetch(`${baseURL}/api/logs`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ table: "tiktok" }),
  });
  const blob = await resposne.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");

  a.href = url;
  a.download = "tiktok_logs.txt";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  await fetch(`${baseURL}/api/tiktok/delete`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename: "tiktok_logs.txt" }),
  });
  logsLink.disabled = false;
}

//-----------------------------------------------------------------------------------//
//                                      Toast                                        //
//-----------------------------------------------------------------------------------//

async function showStatsToast() {
  try {
    const response = await fetch(`${baseURL}/api/stats`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ table: "tiktok" }),
    });
    if (response.ok == false) {
      throw new Error("Error while fetching server stats!");
    }
    const stats = await response.json();
    toastTitle.textContent = "Page stats";
    toastBody.innerHTML = `
      Total conversions: ${stats.total_conversions}`;
    showToast();
    setTimeout(() => {
      hideToast();
    }, 5000);
  } catch (error) {
    toastTitle.textContent = "Error";
    toastBody.textContent = "Could not load stats!";
    console.error(error);
    showToast();
    setTimeout(() => {
      hideToast();
    }, 5000);
  }
}

function showToast() {
  console.log("Toast");
  if (!toastContainer) {
    console.error("Toast container not found!");
    return;
  }
  toastContainer.hidden = false;
  toastContainer.classList.remove("fade-out");
  toastContainer.classList.add("slide-in");
}

function hideToast() {
  toastContainer.classList.remove("slide-in");
  toastContainer.classList.remove("fade-out");
  toastContainer.classList.add("fade-out");

  toastContainer.addEventListener(
    "animationend",
    () => {
      toastContainer.hidden = true;
      toastContainer.classList.remove("fade-out");
    },
    { once: true }
  );
}

//-----------------------------------------------------------------------------------//
//                                   Token Validation                                //
//-----------------------------------------------------------------------------------//

async function validateToken() {
  const token = localStorage.getItem("access_token");

  // if token is not present return to index.html
  if (!token) {
    window.location.href = "index.html";
    return;
  }

  // if token is present validate the token
  try {
    const response = await fetch(`${baseURL}/api/user_info`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    data = await response.json();
    activeUser.innerHTML = data.user;

    if (data.status != "success") {
      localStorage.removeItem("access_token");
      window.location.href = "index.html";
    }
  } catch (error) {
    console.log("Error: ", error);
    window.location.href = "index.html";
  }
}
