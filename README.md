# Macbook-Kiosk
Smart Laptop Locker . This project is a smart locker system for storing and managing school laptops. It combines Arduino, Raspberry Pi, and a Flask web application to provide secure access via RFID cards and live monitoring of the number of laptops inside.
🔹 Features

RFID authentication — students/teachers scan their card to access laptops.

Flask web interface — shows locker status and laptop count.

Relay-controlled door — locker door opens/closes automatically.

Real-time laptop tracking — 7 physical buttons/sensors detect how many laptops are inside.

Cancel / Take / Return actions — with proper redirects between pages.

🔹 System Architecture

Arduino

Reads RFID tags.

Controls the relay (locker door).

Sends button status (7 inputs) via Serial to Raspberry Pi.

Raspberry Pi (Flask server)

Hosts the web application (Python + Flask).

Communicates with Arduino over Serial.

Manages user sessions (current RFID user, redirects, etc.).

Displays laptop count on the main page.

🔹 Hardware Used

Raspberry Pi 4 (Flask server)

Arduino Uno (relay + RFID reader)

RC522 RFID module

Relay module (for locker door)

7 push-buttons (laptop presence detection)

12V solenoid lock (or relay-driven lock)

(Insert photos here: ![Locker Setup](images/locker.jpg))

🔹 Software

Python 3 + Flask (web interface)

Threading (parallel Arduino communication + Flask server)

HTML/Jinja templates (for pages: index, scan, hello, take, return)

🔹 How It Works

User scans RFID card → Flask verifies UID.

Flask redirects to Scan Page → then Hello Page.

User chooses action:

Take Laptop → relay opens door, count decreases.

Return Laptop → relay opens door, count increases.

Cancel → locker stays closed, user redirected to main page.

The main page always shows the current number of laptops inside.

🔹 Project Goals

Provide secure and simple laptop management in schools.

Prevent laptops from being lost or misplaced.

Demonstrate IoT integration of hardware + web server.

🔹 Future Improvements

Database integration (save history of who borrowed/returned laptops).

Admin panel for user management.

Telegram/Email notifications for teachers.

More sensors (door open/close status).

🔹 Demo
