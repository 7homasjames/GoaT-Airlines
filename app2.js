let selectedSeat = null;
let passengerDetails = {};

document.addEventListener("DOMContentLoaded", () => {
    showPage('welcome-page'); // ✅ Ensure the first page is 'Welcome Page'
});

const backendURL = "https://your-app.onrender.com";  // Update with Render link

async function verifyPassenger() {
    const formData = new FormData();
    formData.append("file", document.getElementById("passenger-photo").files[0]);

    const response = await fetch(`${backendURL}/verify-passenger/`, {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    alert(data.message);
}

/* ==================================================
   🔹 PAGE NAVIGATION FUNCTION
================================================== */
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');

    // ✅ Remove 'active' class from all sidebar buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

    // ✅ Highlight the clicked sidebar button
    const activeBtn = document.querySelector(`[onclick="showPage('${pageId}')"]`);
    if (activeBtn) activeBtn.classList.add('active');
}

/* ==================================================
   🔹 SEAT SELECTION LOGIC
================================================== */
document.querySelectorAll(".seat").forEach(seat => {
    seat.addEventListener("click", function () {
        document.querySelectorAll(".seat").forEach(s => s.classList.remove("selected"));
        this.classList.add("selected");
        
        selectedSeat = this.dataset.seat;
        document.getElementById("selected-seat").innerText = selectedSeat;

        // Enable "Next" button when a seat is selected
        document.getElementById("seat-next-btn").disabled = false;
    });
});

// Navigate to Passenger Details
function goToPassengerDetails() {
    if (!selectedSeat) {
        alert("Please select a seat before proceeding.");
        return;
    }
    showPage('passenger-details');
}

/* ==================================================
   🔹 PASSENGER REGISTRATION FORM HANDLING
================================================== */
document.getElementById("passenger-form").addEventListener("submit", function (event) {
    event.preventDefault();

    const firstName = document.getElementById("passenger-first-name").value;
    const lastName = document.getElementById("passenger-last-name").value;
    const email = document.getElementById("passenger-email").value;
    const photo = document.getElementById("passenger-photo").files[0];

    if (!firstName || !lastName || !email || !photo) {
        alert("Please fill in all required fields and upload a photo.");
        return;
    }

    passengerDetails = {
        name: `${firstName} ${lastName}`,
        email: email,
        seat: selectedSeat
    };

    showPage('boarding-pass');
    updateBoardingPass();
});

/* ==================================================
   🔹 UPDATE BOARDING PASS PAGE
================================================== */
function updateBoardingPass() {
    document.getElementById("bp-name").textContent = passengerDetails.name;
    document.getElementById("bp-seat").textContent = selectedSeat || "Not Selected";
    document.getElementById("bp-date").textContent = new Date().toLocaleDateString();
}

/* ==================================================
   🔹 PRINT BOARDING PASS
================================================== */
function printBoardingPass() {
    window.print();
}

/* ==================================================
   🔹 WEBCAM CAPTURE LOGIC
================================================== */
document.getElementById("open-webcam").addEventListener("click", function () {
    const video = document.createElement("video");
    video.setAttribute("id", "webcam-video");
    video.setAttribute("autoplay", "true");

    const captureButton = document.createElement("button");
    captureButton.innerHTML = "Capture Photo";
    captureButton.classList.add("capture-btn");

    const closeButton = document.createElement("button");
    closeButton.innerHTML = "Close Webcam";
    closeButton.classList.add("close-btn");

    const previewContainer = document.querySelector(".image-preview");
    previewContainer.innerHTML = "";
    previewContainer.appendChild(video);
    previewContainer.appendChild(captureButton);
    previewContainer.appendChild(closeButton);

    // Access the webcam
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(err => {
            console.error("Error accessing webcam:", err);
            alert("Unable to access webcam. Please check your permissions.");
        });

    // Capture Photo
    captureButton.addEventListener("click", function () {
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageDataURL = canvas.toDataURL("image/jpeg");

        // Stop the webcam stream
        video.srcObject.getTracks().forEach(track => track.stop());

        // Replace webcam with captured image
        previewContainer.innerHTML = `<img id="face-preview" src="${imageDataURL}" alt="Captured Face">`;

        // Convert imageDataURL to a file for submission
        fetch(imageDataURL)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], "face_capture.jpg", { type: "image/jpeg" });
                document.getElementById("passenger-photo").files = createFileList(file);
            });
    });

    // Close Webcam
    closeButton.addEventListener("click", function () {
        video.srcObject.getTracks().forEach(track => track.stop());
        previewContainer.innerHTML = `<img id="face-preview" src="face_cap.avif" alt="Face Capture Preview">`;
    });
});

// Helper function to create a FileList from a single file
function createFileList(file) {
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    return dataTransfer.files;
}

/* ==================================================
   🔹 PASSENGER VERIFICATION (Optional API Call)
================================================== */
document.querySelector(".verify-btn").addEventListener("click", async function () {
    const formData = new FormData();
    formData.append("file", document.getElementById("passenger-photo").files[0]);

    const response = await fetch("http://127.0.0.1:8000/verify-passenger/", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    alert(data.message);
});
