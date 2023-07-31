import streamlit as st
from googleapiclient.discovery import build
from pymongo import MongoClient

# Function to fetch YouTube channel data
def get_youtube_channel_data(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    response = youtube.channels().list(
        part='snippet,statistics,contentDetails',
        id=channel_id
    ).execute()

    channel_data = response['items'][0]
    return channel_data

# Function to fetch video data for a given playlist
def get_playlist_video_data(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    next_page_token = None

    while True:
        response = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        videos.extend(response['items'])
        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    video_data = []
    for video in videos:
        video_id = video['snippet']['resourceId']['videoId']

        # Fetch actual likes, dislikes, and comments data using separate API calls
        video_response = youtube.videos().list(
            part='statistics',
            id=video_id
        ).execute()

        if video_response['items']:
            statistics = video_response['items'][0]['statistics']
            likes = int(statistics.get('likeCount', 0))
            dislikes = int(statistics.get('dislikeCount', 0))
            comments = int(statistics.get('commentCount', 0))
        else:
            likes = dislikes = comments = 0

        video_info = {
            'Video ID': video_id,
            'Title': video['snippet']['title'],
            'Likes': likes,
            'Dislikes': dislikes,
            'Comments': comments
        }
        video_data.append(video_info)

    return video_data

# Set up MongoDB connection
def get_mongo_client(connection_string):
    return MongoClient(connection_string)

# Function to store data in MongoDB
def store_data_in_mongodb(collection, data):
    collection.insert_one(data)


# Main function to run the Streamlit app
def main():
    st.title('YouTube Channel Data Analyzer')
    api_key = 'AIzaSyCjp6AtVx_hrQlPRZXF9SlBVcLrYPFCdG8'  
    mongodb_connection_string = 'mongodb://127.0.0.1:27017/'  

    # Connect to MongoDB
    mongo_client = get_mongo_client(mongodb_connection_string)
    db = mongo_client['youtube_data_db']  
    collection = db['channel_data']  

    # Set up Streamlit layout
    channel_id = st.text_input('Enter YouTube Channel ID:')
    store_button = st.button('Fetch Data and Store in MongoDB')

    if store_button:
        channel_data = get_youtube_channel_data(api_key, channel_id)
        if channel_data:
            st.write('Channel Name:', channel_data['snippet']['title'])
            st.write('Subscribers:', channel_data['statistics']['subscriberCount'])
            st.write('Total Videos:', channel_data['statistics']['videoCount'])

            playlist_id = channel_data['contentDetails']['relatedPlaylists']['uploads']
            video_data = get_playlist_video_data(api_key, playlist_id)

            if video_data:
                # Store data in MongoDB
                data_to_store = {
                    'channel_name': channel_data['snippet']['title'],
                    'channel_id': channel_id,
                    'subscribers': int(channel_data['statistics']['subscriberCount']),
                    'total_videos': int(channel_data['statistics']['videoCount']),
                    'playlist_id': playlist_id,
                    'video_data': video_data
                }
                store_data_in_mongodb(collection, data_to_store)
                st.success('Data successfully stored in MongoDB.')
            else:
                st.error('No video data found for the channel.')
        else:
            st.error('Invalid YouTube Channel ID.')

if __name__ == '__main__':
    main()