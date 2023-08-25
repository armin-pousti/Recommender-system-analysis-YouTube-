import time
import pandas as pd
from random import choice
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import html
from SVM import predict_political_affiliation, train_model
import csv
from collections import Counter
from csv import DictWriter
import os


clf, vectorizer, scaler, _, _, _, _ = train_model()
with open('right_videos.csv', 'r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    right_video_titles = [row['Title'] for row in reader]


def remove_non_bmp_characters(text):
    return ''.join([c for c in text if ord(c) < 0x10000])


def check_and_record_recommendations(driver):
    recommendations = []
    political_affiliation_counts = Counter()
    try:
        video_elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "yt-formatted-string#video-title"))
        )

        with open('watched_videos.txt', 'a', encoding='utf-8') as file:
            file.write("---- Homepage Recommendations ----\n")

        for index, video in enumerate(video_elements):
            title = video.text.strip()
            if not title:
                continue

            political_affiliation = predict_political_affiliation(title, title, clf, vectorizer, scaler)
            political_affiliation_counts[political_affiliation] += 1

            print(f"Video title {index + 1}: {title} (Political Affiliation: {political_affiliation})")

            with open('watched_videos.txt', 'a', encoding='utf-8') as file:
                file.write(f"{title} (Political Affiliation: {political_affiliation})\n")

            recommendation = {
                "Title": title,
                "Political Affiliation": political_affiliation
            }
            recommendations.append(recommendation)

        print("Number of videos for each Political Affiliation:")
        for affiliation, count in political_affiliation_counts.items():
            print(f"{affiliation}: {count}")

        # Save the counts to a CSV file
        with open('numbers.csv', 'a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Left", "Right", "Non-political"])
            csv_writer.writerow([
                political_affiliation_counts["Left"],
                political_affiliation_counts["Right"],
                political_affiliation_counts["Non-political"]
            ])

    except Exception as e:
        print("Error while collecting recommendations:", e)

    return recommendations, political_affiliation_counts


def get_video_description(driver, video_title):
    # Open new tab
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])

    # Navigate to YouTube
    driver.get("https://www.youtube.com")

    # Search for video
    search_box = driver.find_element(By.CSS_SELECTOR, 'input#search')
    search_box.send_keys(video_title)
    search_box.send_keys(Keys.RETURN)
    time.sleep(2)

    # Attempt to get the video description
    try:
        video_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer.ytd-item-section-renderer"))
        )
        video_element.click()
        time.sleep(2)

        description_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "yt-formatted-string.content.style-scope.ytd-video-secondary-info-renderer"))
        )

        description = description_element.text
    except TimeoutException:
        description = ""
        print(f"TimeoutException: Could not retrieve description for video {video_title}")
    except Exception as e:
        description = ""
        print(f"An error occurred while retrieving description for video {video_title}: {e}")

    # Close the tab and switch back to the original tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return description


def watch_video(driver, video_title, channel_name):
    video_title = html.unescape(video_title)  # decode HTML entities
    video_title = remove_non_bmp_characters(video_title)
    channel_name = remove_non_bmp_characters(channel_name)
    try:
        # Clear the search bar if there is any existing text
        search_box = driver.find_element(By.CSS_SELECTOR, 'input#search')
        driver.execute_script("arguments[0].value = '';", search_box)  # Clear using JavaScript

        # Search for the video using its title and channel name
        search_query = f"{channel_name} {video_title}"
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)

        # Find the video elements with a matching title
        video_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytd-video-renderer.ytd-item-section-renderer")))

        matched_video = None
        for i, video_element in enumerate(video_elements[:2]):  # Compare against the first 2 videos
            title_element = video_element.find_element(By.CSS_SELECTOR, "#video-title")
            if video_title.lower() in title_element.text.lower():
                matched_video = video_element
                break

        if matched_video:
            matched_video.click()
        else:
            print(f"Video not found: {video_title} by {channel_name}")

        # Skip ad if present
        skip_ad(driver)

        # Watch video for 10 minutes
        time.sleep(600)

        # Pause the video
        pause_button = driver.find_element(By.CSS_SELECTOR, '.ytp-play-button')
        pause_button.click()
    except Exception as e:
        print("Error watching video:", e)


def skip_ad(driver):
    try:
        skip_ad_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-ad-skip-button")))
        skip_ad_button.click()
    except TimeoutException:
        pass


def login_and_clear_history(driver):
    try:
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@aria-label="Sign in"]')))
        login_button.click()
        time.sleep(3)

        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]')))
        username_input.send_keys("EMAIL")

        next_button = driver.find_element(By.XPATH, '//*[@id="identifierNext"]/div/button/span')
        next_button.click()
        time.sleep(3)

        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input')))
        password_input.send_keys("PASSWORD")

        login_button = driver.find_element(By.XPATH, '//*[@id="passwordNext"]/div/button/span')
        login_button.click()
        time.sleep(3)

        history_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[text()="History"]')))
        driver.execute_script("arguments[0].click();", history_button)
        time.sleep(3)

        clear_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[text()="Clear all watch history"]')))
        driver.execute_script("arguments[0].click();", clear_button)

        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[text()="Clear watch history"]')))
        driver.execute_script("arguments[0].click();", confirm_button)

    except Exception as e:
        print("Error:", e)


def sample_videos(df, n):
    left_sample = df[df["Political Affiliation"] == "Left"].sample(n * 8 // 10)
    right_sample = df[df["Political Affiliation"] == "Right"].sample(n // 10)
    non_political_sample = df[df["Political Affiliation"] == "Non-political"].sample(n // 10)
    sampled_videos = pd.concat([left_sample, right_sample, non_political_sample])
    return sampled_videos.sample(frac=1)


def record_title_to_file(title):
    with open('watched_videos.txt', 'a', encoding='utf-8') as file:
        file.write(title + '\n')


def watch_recommended_video(driver, recommendations, right_video_titles, target_affiliation='Right'):
    for video in recommendations:
        if video['Political Affiliation'] == target_affiliation:
            watch_video(driver, video['Title'], video['Channel Name'])
            return

    print(f"No video with affiliation {target_affiliation} found in recommendations.")
    random_right_video = choice(right_video_titles)
    print(f"Suggested video from Right dataset: {random_right_video}")
    watch_video(driver, random_right_video, '')


def main():
    # Initialize ChromeOptions
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--mute-audio")

    # Initialize CSV file for counts only if it doesn't exist
    for csv_file_path in ['affiliation_counts.csv', 'numbers.csv']:
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = DictWriter(csv_file, fieldnames=['Left', 'Right', 'Non-political'])
                csv_writer.writeheader()

    with Chrome(options=options) as driver:
        # Navigate to YouTube and login
        driver.get("https://www.youtube.com")
        login_and_clear_history(driver)

        # Read the DataFrame
        df = pd.read_csv("latest_videos.csv")
        n = 100  # Number of videos to establish bias
        sampled_videos = sample_videos(df, n)

        # Step 1: Establish Bias
        for _, row in sampled_videos.iterrows():
            decoded_title = html.unescape(row["Title"])
            watch_video(driver, decoded_title, row["Channel Name"])
            record_title_to_file(decoded_title)

        i = 0
        while i <= 100:
            i += 1

            # Step 2: First Check
            driver.get("https://www.youtube.com")
            time.sleep(3)
            recommendations, counts = check_and_record_recommendations(driver)

            # Append counts to CSV
            with open('affiliation_counts.csv', 'a', newline='', encoding='utf-8') as csv_file:
                csv_writer = DictWriter(csv_file, fieldnames=['Left', 'Right', 'Non-political'])
                # No header writing here
                csv_writer.writerow({
                    'Left': counts.get('Left', 0),
                    'Right': counts.get('Right', 0),
                    'Non-political': counts.get('Non-political', 0)
                })

            # Step 3: Refresh Mechanism
            found_opposing_view = False
            # Refresh up to 3 times
            for _ in range(3):
                opposing_video = next((video for video in recommendations if video['Political Affiliation'] == 'Right'), None)
                if opposing_video:
                    found_opposing_view = True
                    break
                else:
                    driver.refresh()
                    time.sleep(2)
                    recommendations, _ = check_and_record_recommendations(driver)

            # Step 4: Iterative View & Check
            if found_opposing_view:
                print(f"Found opposing view: {opposing_video['Title']}")
                watch_video(driver, opposing_video.get('Title', ''), opposing_video.get('Channel Name', ''))

            else:
                # Step 5: Active Search
                print("No opposing view found. Actively searching...")
                random_left_video = choice(right_video_titles)
                watch_video(driver, random_left_video, '')


if __name__ == "__main__":
    main()


