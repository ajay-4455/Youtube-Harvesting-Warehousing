import os
import googleapiclient.discovery
import streamlit as st
import pandas as pd
import mysql.connector
import pymongo
from mongodb_connector import connect_to_mongodb
from mysql_connector import connect_to_mysql


# Set your Google API key here
API_KEY = "AIzaSyCjp6AtVx_hrQlPRZXF9SlBVcLrYPFCdG8"

# Function to fetch channel data using the YouTube Data API
def fetch_single_channel_data(channel_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

    # Fetch channel data
    channel_response = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    if not channel_response["items"]:
        return None

    channel_data = channel_response["items"][0]
    channel_name = channel_data["snippet"]["title"]
    subscribers = channel_data["statistics"]["subscriberCount"]
    total_videos = channel_data["statistics"]["videoCount"]

    # Fetch playlist data
    playlist_response = youtube.playlists().list(
        part="snippet",
        channelId=channel_id,
        maxResults=10
    ).execute()

    playlist_ids = [item["id"] for item in playlist_response["items"]]

    # Fetch video data for each playlist
    videos_data = []
    for playlist_id in playlist_ids:
        playlist_items_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=10
        ).execute()

        video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_items_response["items"]]

        for video_id in video_ids:
            try:
                video_response = youtube.videos().list(
                    part="snippet,statistics",
                    id=video_id
                ).execute()
            except googleapiclient.errors.HttpError as e:
                if e.resp.status == 403 and "commentsDisabled" in str(e.content):
                    # Video has disabled comments, skip it
                    continue
                else:
                    # Unexpected error, raise it
                    raise

            if video_response["items"]:
                video_data = video_response["items"][0]
                video_title = video_data["snippet"]["title"]
                video_likes = video_data["statistics"].get("likeCount", 0)
                video_dislikes = video_data["statistics"].get("dislikeCount", 0)

                # Fetch comments for each video (if not disabled)
                comments = []
                try:
                    comments_response = youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id,
                        maxResults=50
                    ).execute()

                    comments = [item["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for item in comments_response["items"]]
                except googleapiclient.errors.HttpError as e:
                    if e.resp.status == 403 and "commentsDisabled" in str(e.content):
                        # Video has disabled comments, skip fetching comments
                        pass
                    else:
                        # Unexpected error, raise it
                        raise

                videos_data.append({
                    "Playlist ID": playlist_id,
                    "Video ID": video_id,
                    "Video Title": video_title,
                    "Likes": video_likes,
                    "Dislikes": video_dislikes,
                    "Comments": comments
                })

    result = {
        "Channel Name": channel_name,
        "Channel ID": channel_id,
        "Subscribers": subscribers,
        "Total Video Count": total_videos,
        "Videos Data": videos_data
    }

    return result

def fetch_multi_channel_data(channel_ids):
    result_list = []
    for channel_id in channel_ids:
        result = fetch_single_channel_data(channel_id)
        if result:
            result_list.append(result)
    return result_list


def main():
    st.title("YouTube Channel Data App")
    st.sidebar.title("Navigation")
    pages = ["Single Channel", "Multi-Channel"]
    page = st.sidebar.radio("Go to", pages)
    
    results = []  # Define the results variable outside the 'if' blocks

    if page == "Single Channel":
        st.header("Single Channel Page")
        channel_id = st.text_input("Enter Channel ID:")
        if st.button("Fetch Data"):
            result = fetch_single_channel_data(channel_id)
            if result:
                st.write("Channel Name:", result["Channel Name"])
                st.write("Channel ID:", result["Channel ID"])
                st.write("Subscribers:", result["Subscribers"])
                st.write("Total Video Count:", result["Total Video Count"])
                # Display other data as needed
            else:
                st.write("No data found for the given channel ID.")

    elif page == "Multi-Channel":
        st.header("Multi-Channel Page")
        channel_ids_input = st.text_area("Enter Channel IDs (separated by commas):")
        channel_ids_list = [channel_id.strip() for channel_id in channel_ids_input.split(",")]

        if st.button("Fetch Data"):
            results = fetch_multi_channel_data(channel_ids_list)
            if results:
                for result in results:
                    st.write("Channel Name:", result["Channel Name"])
                    st.write("Channel ID:", result["Channel ID"])
                    st.write("Subscribers:", result["Subscribers"])
                    st.write("Total Video Count:", result["Total Video Count"])

                    # Display Video Data
                    for video_data in result["Videos Data"]:
                        st.write("Playlist ID:", video_data["Playlist ID"])
                        st.write("Video ID:", video_data["Video ID"])
                        st.write("Video Title:", video_data["Video Title"])
                        st.write("Likes:", video_data["Likes"])
                        st.write("Dislikes:", video_data["Dislikes"])
                        st.write("Comments:", video_data["Comments"])

                    st.write("---")

            else:
                st.write("No data found for the given channel IDs.")

              # Additional buttons for uploading to MongoDB and MySQL
            if st.button("Upload to MongoDB"):
                try:
                    if results:  # Check if results list is not empty
                        mongo_collection = connect_to_mongodb()
                        mongo_collection.insert_many(results)
                        st.write("Data uploaded to MongoDB successfully!")
                    else:
                        st.write("No data to upload to MongoDB.")
                except Exception as e:
                    st.write("Error uploading data to MongoDB:", e)

            if st.button("Upload to MySQL"):
                try:
                    if results:  # Check if results list is not empty
                        mysql_conn = connect_to_mysql()
                        cursor = mysql_conn.cursor()

                        query = """
                        INSERT INTO your_mysql_table
                        (channel_name, channel_id, subscribers, total_videos, video_title, video_id, likes, dislikes, comments)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                        for result in results:
                             for video_data in result["Videos Data"]:
                                values = (
                                    result["Channel Name"],
                                    result["Channel ID"],
                                    result["Subscribers"],
                                    result["Total Video Count"],
                                    video_data["Video Title"],
                                    video_data["Video ID"],
                                    video_data["Likes"],
                                    video_data["Dislikes"],
                                    "\n".join(video_data["Comments"]),
                                )

                        cursor.execute(query, values)

                        mysql_conn.commit()
                        st.write("Data uploaded to MySQL database successfully!")
                except Exception as e:
                    st.write("Error uploading data to MySQL:", e)
                finally:
                    if mysql_conn.is_connected():
                        cursor.close()
                        mysql_conn.close()


if __name__ == "__main__":
    main()