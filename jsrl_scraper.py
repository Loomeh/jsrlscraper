import os
import platform
import subprocess
import requests
import logging
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import unquote

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up the headless browser options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Determine the operating system
operating_system = platform.system()

# Find the ChromeDriver path based on the operating system
if operating_system == "Windows":
    find_command = "where chromedriver"
else:
    find_command = "which chromedriver"

chrome_driver_path = subprocess.run(find_command, shell=True, stdout=subprocess.PIPE, text=True).stdout.strip()

# Set up the WebDriver
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Check if any command-line arguments are provided
wayback = "-wayback" in sys.argv

if wayback:
    logger.info("Capturing the January 2020 Wayback Machine archive.")

# URL to scrape
url = "https://web.archive.org/web/20200715234245/http://jetsetradio.live/" if wayback else "https://jetsetradio.live/tv/APP/index.html"
logger.info(f"Loading the webpage: {url}")

if wayback:
    logger.info("Capturing the January 2020 Wayback Machine archive.")

    # Initial click to enter the site
    try:
        logger.info("Attempting to click anywhere on the screen to enter the site.")
        action = ActionChains(driver)
        action.move_by_offset(500, 500).click().perform()  # Adjust the offset values as needed
        logger.info("Successfully clicked on the screen.")
    except Exception as e:
        logger.error(f"Error clicking on the screen: {e}")

    # Wait for the page to react
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'tvButton'))
    )

    # Find and click the 'tvButton'
    try:
        logger.info("Attempting to click on the 'tvButton'.")
        tv_button = driver.find_element(By.ID, "tvButton")
        tv_button.click()
        logger.info("Successfully clicked on the 'tvButton'.")
    except Exception as e:
        logger.error(f"Error clicking on the 'tvButton': {e}")

    # Wait for the next page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    )

    # Click on the screen again
    try:
        logger.info("Attempting to click on the screen again.")
        action = ActionChains(driver)
        action.move_by_offset(500, 500).click().perform()  # Adjust the offset values as needed
        logger.info("Successfully clicked on the screen again.")
    except Exception as e:
        logger.error(f"Error clicking on the screen again: {e}")

# Proceed with the rest of the script as usual

# Load the webpage
driver.get(url)

# Wait for the page to load completely
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.TAG_NAME, 'body'))
)

# Click anywhere on the screen (e.g., center of the screen)
try:
    logger.info("Attempting to click anywhere on the screen to enter the site.")
    action = ActionChains(driver)
    action.move_by_offset(500, 500).click().perform()  # Adjust the offset values as needed
    logger.info("Successfully clicked on the screen.")
except Exception as e:
    logger.error(f"Could not click the screen: {e}")
    driver.quit()
    exit()

# Create a directory to store the videos
os.makedirs('downloaded_videos', exist_ok=True)
logger.info("Created directory for downloaded videos.")

# Initialize the counter at the start of the script
successful_downloads = 0

def download_video(video_url, directory='downloaded_videos'):
    global successful_downloads  # Use the global counter
    
    if not video_url or "undefined.mp4" in video_url:
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Decode the video URL to handle spaces and other characters
    video_url = unquote(video_url)
    file_name = os.path.join(directory, os.path.basename(video_url))

    if os.path.exists(file_name):
        logger.info(f"File {file_name} already exists. Skipping download.")
        successful_downloads += 1  # Increment counter even if download is skipped
    else:
        logger.info(f"Downloading {video_url} to {file_name}")
        response = requests.get(video_url, stream=True, headers=headers, allow_redirects=True)
        download_attempted = True

        if response.status_code == 200:
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > 0:
                with open(file_name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Downloaded {file_name}")
            else:
                logger.warning(f"Empty or invalid content for {video_url}.")
        else:
            logger.error(f"Failed to download {video_url}. Status code: {response.status_code}")

while True:
    try:
        # Wait for the video element to be present and get the video URL
        logger.info("Waiting for the video element to be present.")
        video_frame = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'videoFrame'))
        )
        video_source = video_frame.find_element(By.TAG_NAME, 'source')

        if wayback:
            video_url = "https://web.archive.org/web/20201213013328/" + video_source.get_attribute('src')
        else:
            video_url = video_source.get_attribute('src')

        if not video_url:
            logger.warning("Video URL is empty. Skipping this video.")
            continue

        # Log and download the video if it's not undefined.mp4
        if "undefined.mp4" not in video_url:
            logger.info(f"Video URL found: {video_url}")
            download_video(video_url)
        else:
            pass  # Do nothing for undefined.mp4

        # Find and click the skip button
        logger.info("Waiting for the skip button to be clickable.")
        skip_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'skipVideoButton'))
        )
        skip_button.click()
        logger.info("Clicked the skip button.")
        
        # Wait for the next video to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'videoFrame'))
        )
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        break

# Close the browser
logger.info("Closing the browser.")
driver.quit()
