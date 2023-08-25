import csv
from googleapiclient.discovery import build
import os


def get_channel_id(api_key, channel_name):
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Fetch the channel ID using the channel name
    request = youtube.search().list(
        part='snippet',
        q=channel_name,
        type='channel',
        maxResults=1
    )
    response = request.execute()
    if 'items' in response and len(response['items']) > 0:
        return response['items'][0]['id']['channelId']
    else:
        raise ValueError("Channel not found.")

def get_latest_video_info(channel_id, api_key, political_affiliation):
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Fetch the latest videos from the specified channel
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        order='date',
        maxResults=100
    )
    response = request.execute()

    video_data = []
    for item in response['items']:
        title = item['snippet']['title']
        description = item['snippet']['description']
        video_data.append((title, description, political_affiliation))

    return video_data


def save_to_csv(file_path, data):
    # Check if file exists to determine if header is needed
    file_exists = os.path.isfile(file_path)

    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header only if file didn't exist
        if not file_exists:
            csv_writer.writerow(['Channel Name', 'Title', 'Description', 'Political Affiliation'])
        csv_writer.writerows(data)


if __name__ == "__main__":
    api_key = 'API_KEY'

    # List of lists with channel names and political affiliations
    # format ['Channel name', 'Political Affiliation']
    channels_info = [
    ]

    try:
        for channel_info in channels_info:
            channel_name, political_affiliation = channel_info
            channel_id = get_channel_id(api_key, channel_name)
            data = get_latest_video_info(channel_id, api_key, political_affiliation)

            # Add the channel_name to each row in the data
            data_with_channel = [(channel_name,) + row for row in data]

            save_to_csv('latest_videos.csv', data_with_channel)

        print("CSV file created successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

