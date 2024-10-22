#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>

const char* ssid = "Redmi";
const char* password = "12345678";

ESP8266WebServer server(80);

// HTML form page
const char MAIN_page[] PROGMEM = R"=====(
<!DOCTYPE html>
<html>
<head>
    <title>ESP8266 Web Form</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 0 auto;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"],
        input[type="email"],
        input[type="file"] {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .error {
            color: red;
            font-size: 0.9em;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>User Details Form</h2>
        <form id="userForm" onsubmit="return validateForm()" action="/submit" method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
                <span id="emailError" class="error">Please enter a valid email address</span>
            </div>
            
            <div class="form-group">
                <label for="phone">Phone Number:</label>
                <input type="text" id="phone" name="phone" pattern="[0-9]{10}" required>
                <span id="phoneError" class="error">Please enter a valid 10-digit phone number</span>
            </div>
            
            <div class="form-group">
                <label for="file">Upload File:</label>
                <input type="file" id="file" name="file" required>
                <span id="fileError" class="error">Please select a file</span>
            </div>
            
            <button type="submit">Submit</button>
        </form>
    </div>

    <script>
        function validateForm() {
            let isValid = true;
            
            // Email validation
            const email = document.getElementById('email').value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                document.getElementById('emailError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('emailError').style.display = 'none';
            }
            
            // Phone validation
            const phone = document.getElementById('phone').value;
            const phoneRegex = /^[0-9]{10}$/;
            if (!phoneRegex.test(phone)) {
                document.getElementById('phoneError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('phoneError').style.display = 'none';
            }
            
            // File validation
            const file = document.getElementById('file').value;
            if (!file) {
                document.getElementById('fileError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('fileError').style.display = 'none';
            }
            
            return isValid;
        }
    </script>
</body>
</html>
)=====";

void handleRoot() {
    server.send(200, "text/html", MAIN_page);
}

void handleSubmit() {
    String name = server.arg("name");
    String email = server.arg("email");
    String phone = server.arg("phone");
    
    // Handle file upload
    HTTPUpload& upload = server.upload();
    if (upload.status == UPLOAD_FILE_START) {
        String filename = upload.filename;
        if (!filename.startsWith("/")) filename = "/" + filename;
        // Open the file for writing
        File fsUploadFile = LittleFS.open(filename, "w");
    }
    else if (upload.status == UPLOAD_FILE_WRITE) {
        // Write the received bytes to the file
        File fsUploadFile = LittleFS.open(upload.filename, "a");
        if(fsUploadFile) {
            fsUploadFile.write(upload.buf, upload.currentSize);
            fsUploadFile.close();
        }
    }
    
    // Send response
    String response = "<!DOCTYPE html><html><body>";
    response += "<h2>Submission Successful!</h2>";
    response += "<p>Name: " + name + "</p>";
    response += "<p>Email: " + email + "</p>";
    response += "<p>Phone: " + phone + "</p>";
    response += "<p>File uploaded successfully!</p>";
    response += "<a href='/'>Back to form</a>";
    response += "</body></html>";
    
    server.send(200, "text/html", response);
}

void setup() {
    Serial.begin(115200);
    
    // Initialize LittleFS
    if (!LittleFS.begin()) {
        Serial.println("An error occurred while mounting LittleFS");
        return;
    }
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    
    // Handle routes
    server.on("/", HTTP_GET, handleRoot);
    server.on("/submit", HTTP_POST, handleSubmit);
    
    server.begin();
    Serial.println("HTTP server started");
}

void loop() {
    server.handleClient();
} 