This project is a simple Python application that interacts with a Reolink camera to capture snapshots and display them on a web server. Originally developed for a friend's shooting range, the primary goal was to provide a way to view snapshots of targets at regular intervals.

Project Motivation
The Solution was made becaue its a low Budget Project, we take pictures because the reolink snapshots, are 4k. The Reolink just acts as a normal Camera. The Video Stream quality is not good so we rather take a picture every sec. Then Streaming bad Quality 


Reolink 8111a camera (~$70 used)
Raspberry Pi 3b
Managed Cisco Switch
Standard router for network configuration

Why Not Use the Raspberry Pi for DHCP?
For reliability and network consistency, a more robust router or dedicated device is preferable for DHCP. Using the Raspberry Pi for DHCP is not ideal since it should focus on its primary task—capturing images and running the web server—rather than managing network addresses.

Why a Managed Switch?
Multiple shooting ranges can be connected simultaneously (up to 5), requiring a managed switch to handle multiple camera streams efficiently and without network issues.

Getting Started

Requirements
Install the necessary libraries:

pip install requests Flask python-dotenv pillow

Setting up the Raspberry Pi
To run this project on a Raspberry Pi:

Copy the code onto the Raspberry Pi.

Configure the Raspberry Pi to launch this script on startup and open a web browser at localhost:8000 to view the images.
.env Configuration

Create a .env file in the project directory with the following variables:


# Camera IP address
CAMERA_IP=Your_Camera_IP

# Camera password (username is set to 'admin' in the script)
PASSWORD=Your_Camera_Password

# Directory to save images
SAVE_DIR=./images

# Port for the Flask web server
PORT=8000

# Time in milliseconds to refresh the image on the webpage
TIMETOLOAD=5000

# Crop settings for the image
CROP_LEFT=0
CROP_RIGHT=0
CROP_TOP=0
CROP_BOTTOM=0



Explanation of the Code

Camera Authentication: The code first logs into the camera using its API, retrieving a token needed to access the camera’s images.

Image Capture: Once authenticated, the script sends a request to the camera to capture a snapshot, which is saved locally.

Image Cropping: After capturing, the image is cropped based on the dimensions defined in the .env file (if specified). This allows you to focus on the target and adjust the view as needed.

Flask Web Server: A simple Flask web server is then launched, serving an HTML page that displays the latest image and refreshes every few seconds, providing near-real-time updates.

Future Plans
Currently, there are no images available, but I hope to add photos of the shooting range setup soon to illustrate how the project functions.

Enjoy :D 

