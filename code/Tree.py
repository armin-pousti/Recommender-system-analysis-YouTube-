from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from pytube import YouTube
import json
from selenium.common.exceptions import TimeoutException
import time
import re
from pytube.exceptions import VideoUnavailable, RegexMatchError
from selenium.webdriver.common.by import By

class TreeNode:
    def __init__(self, video_id, parent=None):
        self.video_id = video_id
        self.children = []
        self.parent = parent

    def add_child(self, child):
        self.children.append(child)

    def to_dict(self):
        return {
            "video_id": self.video_id,
            "children": [child.to_dict() for child in self.children]
        }

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.video_id) + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret
    
def wait_for_ad_to_finish(driver):
    while True:
        try:
            # Wait for the skip ad button to be clickable for up to 30 seconds
            skip_ad_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-ad-skip-button"))
            )
            # Click the skip ad button to skip the ad
            skip_ad_button.click()

        except TimeoutException:
            # If the ad skip button is not found or not clickable, we break the loop and continue with the video
            break

def get_video_duration(video_url):
    try:
        yt = YouTube(video_url)
        duration_in_seconds = yt.length
        return duration_in_seconds
    except Exception as e:
        #print("Error fetching video duration:", e)
        return None

def watch_video(driver, video_url):
    try:
        driver.get(video_url)
        subscribe_channel(driver)
        wait_for_ad_to_finish(driver)  # Wait for the ad to finish before watching the video
        duration = get_video_duration(video_url)

        if duration:
            # Watch 60% of the video
            time_to_watch = duration * 0.6
            if time_to_watch >
            time.sleep(time_to_watch)

            # Pause the video after watching
            pause_button = driver.find_element(By.CSS_SELECTOR, '.ytp-play-button')
            pause_button.click()

    except Exception as e:
        pass

def subscribe_channel(driver):
    try:
        # Locate the subscribe button and click it if it's not already clicked
        subscribe_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="subscribe-button-shape"]/button')))
        
        # Check if already subscribed
        if 'Subscribed' not in subscribe_button.text:
            subscribe_button.click()
    except Exception as e:
        pass

def process_related_videos(driver, video_url, current_depth, max_depth, skip_first_recommendation=False):
    # Stop if we reached the maximum depth
    if current_depth > max_depth:
        return None

    watch_video(driver, video_url)

    # Extract top related videos of the current video
    top_related_videos = extract_top_related_video_urls(driver)

    # Create a TreeNode for the current video
    video_node = TreeNode(video_url)

    # Process the top related videos as children (with increased depth)
    for i, related_video in enumerate(top_related_videos):
        # Determine whether to skip the first recommendation based on the flag and video depth
        skip_first = skip_first_recommendation and current_depth == 1 and i == 0
        if skip_first:
            continue
        # Recursively process related videos and get their corresponding TreeNode
        child_node = process_related_videos(driver, related_video, current_depth + 1, max_depth, skip_first_recommendation=skip_first)
        # Add the child TreeNode to the current TreeNode
        if child_node:
            video_node.add_child(child_node)

    return video_node


def extract_top_related_video_urls(driver):
    related_video_urls = []
    related_videos_dic = {}

    # Wait for the element containing the related videos section to be present on the page
    wait = WebDriverWait(driver, 10)
    related_videos_section = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="secondary"]')))

    # Find all elements containing the related videos' thumbnails
    thumbnail_elements = related_videos_section.find_elements(By.CSS_SELECTOR, 'ytd-thumbnail')

    # Skip the first video recommendation (usually the currently playing video)
    thumbnail_elements = thumbnail_elements[1:]

    # Extract the video URLs from the related videos
    for thumbnail_element in thumbnail_elements:
        try:
            video_url_element = thumbnail_element.find_element(By.CSS_SELECTOR, 'a#thumbnail')
            video_url = video_url_element.get_attribute('href')
            related_video_urls.append(video_url)

            # Stop getting related video URLs once we have 3
            if len(related_video_urls) == 3:
                break
        except Exception as e:
            print("Error extracting related video URL:", e)

    # Validate YouTube URLs with regex
    yt_regex = re.compile(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*')

    # Creating a dictionary of the videos
    for values in related_video_urls:
        if yt_regex.search(values):
            try:
                related_videos_dic[YouTube(values).title] = values
            except (VideoUnavailable, RegexMatchError) as e:
                print(f"Error with video URL {values}: {e}")
        else:
            print(f"Invalid YouTube URL: {values}")

    # Print the dictionary of related videos
    print(related_videos_dic)
    return related_video_urls

def save_tree_to_json(root_node, filename):
    tree_dict = root_node.to_dict()
    with open(filename, 'w') as json_file:
        json.dump(tree_dict, json_file)
        
def main():
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--mute-audio")  # Mute the entire browser

    with Chrome(options=options) as driver:
        driver.get("https://www.youtube.com")

        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@aria-label="Sign in"]')))
            login_button.click()
            time.sleep(3)

            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]')))
            username_input.send_keys("2023comp480")

            next_button = driver.find_element(By.XPATH, '//*[@id="identifierNext"]/div/button/span')
            next_button.click()
            time.sleep(3)

            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input')))
            password_input.send_keys("Comp400research")

            login_button = driver.find_element(By.XPATH, '//*[@id="passwordNext"]/div/button/span')
            login_button.click()
            time.sleep(3)
            #for our purposes we will keep history to see if it influences the recommended videos
            #remove commenting to remove history for each scrapper session

        except:
            # If the "Sign in" button is not present, you might already be logged in or there is some other issue
            pass

        root_nodes = []
        #seed_videos = ['https://www.youtube.com/watch?v=N9EsiLE0dyQ&ab_channel=BrianTylerCohen']
        #seed_videos = ['https://www.youtube.com/watch?v=gcQ9sSa5Uhw']
        #seed_videos = ['https://www.youtube.com/watch?v=aaU0OMXWQ8s']
        #seed_videos = ['https://www.youtube.com/watch?v=mtjZ7Azk0OM']
        seed_videos = ['https://www.youtube.com/watch?v=7TovgP-I1X0']
        for seed_video in seed_videos:
            watch_video(driver, seed_video)
            # Process related videos as children with a depth limit of 2 and get their corresponding TreeNode
            root_node = process_related_videos(driver, seed_video, current_depth=0, max_depth=4)
            root_nodes.append(root_node)

        # Open a text file for writing
        with open('tree_structure.txt', 'w') as f:
            # Write the tree structure to the file
            for root_node in root_nodes:
                f.write(str(root_node) + '\n')

        # Save the tree structure to a JSON file
        for i, root_node in enumerate(root_nodes):
            save_tree_to_json(root_node, f'tree_{i}.json')

        # Explicitly quit the driver after watching the videos and saving related videos
        driver.quit()

if __name__ == "__main__":
    main()