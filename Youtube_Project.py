# Libraries  imported

#web application
import streamlit as st

#for data manipulation
import pandas as pd

#for data visualization
import matplotlib.pyplot as plt
import seaborn as sns

#YouTube Python libraries
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Loading JSON data Library
import json

# MongoDB libraries
from pymongo import MongoClient
from pymongo.server_api import ServerApi

#importing other file
from Connections import *

# Import the FuncFormatter class from matplotlib.ticker
from matplotlib.ticker import FuncFormatter

# Set up YouTube Data API credentials
API_KEY = 'AIzaSyBnww_pgc2RxLdkH2bDsOWtO5goIRLFMZA'

#YouTube Data API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Streamlit page configuration
st.set_page_config(layout='wide')

# Function for getting channel_id from channel_name
def get_channel_id(search_query):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        search_response = youtube.search().list(
            q=search_query,
            part='id',
            type='channel',
            maxResults=1
        ).execute()
        items = search_response.get('items', [])
        if items:
            channel_id = items[0]['id']['channelId']
            return channel_id
        else:
            error_message = 'No channel ID found for the channel name: {}'.format(search_query)
            return error_message
    except HttpError as e:
        st.error('An HTTP error occurred:')
        st.error(e)
    return None

def get_channel_status(_youtube, channel_ids):
    all_data = []

    for channel_id in channel_ids:
        try:
            channel_response = youtube.channels().list(
                id=channel_id,
                part='snippet,statistics,contentDetails,status'
            ).execute()

            channel_items = channel_response.get('items', [])

            if len(channel_items) == 0:
                st.error(f"No channel found for ID: {channel_id}")
                continue

            channel_data = channel_response['items'][0]['snippet']
            channel = channel_response['items'][0]
            channel_statistics = channel_response['items'][0]['statistics']
            channel_description = channel_data['description']
            playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # channel information dictionary
            channel_info = {
                "Channel_Name": channel_data['title'],
                "Channel_Id": channel_id,
                "Subscription_Count": int(channel_statistics['subscriberCount']),
                "Video_Count": int(channel_statistics['videoCount']),
                "Channel_Views": int(channel_statistics['viewCount']),
                "Channel_Description": channel_description,
                "Channel_Status": channel['status']['privacyStatus'],
                "Playlist_Name": channel_data['title'] + " Playlist",
                "Playlist_Id": playlist_id,
                "Videos": []
            }

            # Initial request to fetch the first page of videos
            video_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=100  # Fetch more videos in each request
            ).execute()

            # Check if there's a nextPageToken
            next_page_token = video_response.get('nextPageToken', None)

            # List to store all videos
            all_videos = video_response['items']

            # Fetch more pages of videos if nextPageToken exists
            while next_page_token:
                video_response = youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=100,  # Fetch more videos in each request
                    pageToken=next_page_token
                ).execute()

                # Append the videos from the current page to the list
                all_videos.extend(video_response['items'])

                # Check for the next page
                next_page_token = video_response.get('nextPageToken', None)

            video_items = all_videos

            # Before the loop, initialize a counter
            video_counter = 1

            for index, video_item in enumerate(video_items):
                video_data = video_item['snippet']
                video_id = video_data['resourceId']['videoId']

                # Fetch video statistics
                video_stats_response = youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=video_id
                ).execute()

                video_stats_data = video_stats_response['items'][0]
                video_stats = video_stats_data['statistics']

                # Check if comments are disabled for the video
                if 'commentCount' not in video_stats or int(video_stats['commentCount']) == 0:
                    continue

                # Inside the loop, use the counter to create the correct key
                video_info = {
                    f"Video_Id_{video_counter}": video_id,
                    "Video_Name": video_data['title'],
                    "Video_Description": video_data['description'],
                    "PublishedAt": video_data['publishedAt'],
                    "View_Count": int(video_stats['viewCount']),
                    "Like_Count": int(video_stats.get('likeCount', 0)),
                    "Dislike_Count": int(video_stats.get('dislikeCount', 0)),
                    "Favorite_Count": int(video_stats.get('favoriteCount', 0)),
                    "Comment_Count": int(video_stats.get('commentCount', 0)),
                    "Duration": video_stats_data['contentDetails']['duration'],
                    "Thumbnail": video_data['thumbnails']['default']['url'],
                    "Caption_Status": video_stats_data['contentDetails']['caption'],
                    "Comments": {},
                }

                # Increment the counter for the next video
                video_counter += 1

                # Fetch comment information
                try:
                    comment_response = youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=3
                    ).execute()

                    comment_items = comment_response['items']
                    comments = {}

                    for index, comment_item in enumerate(comment_items, start=1):
                        comment_snippet = comment_item['snippet']['topLevelComment']['snippet']
                        comment_id = comment_item['snippet']['topLevelComment']['id']
                        comment_info = {
                            f"Comment_Id_{index}": comment_id,
                            "Comment_Text": comment_snippet['textDisplay'],
                            "Comment_Author": comment_snippet['authorDisplayName'],
                            "Comment_PublishedAt": comment_snippet['publishedAt']
                        }
                        comments[comment_id] = comment_info

                    video_info["Comments"] = comments

                except Exception as e:
                    continue

                # Append video information to the channel's videos list
                channel_info["Videos"].append(video_info)

            all_data.append(channel_info)
        except HttpError as e:
            if e.resp.status == 403:
                st.error("Access to channel data is forbidden. Please check your API credentials")
            else:
                st.error(f"Error fetching channel data for ID: {channel_id}")
                st.error(e)

    return all_data

# Get the channel IDs from session state or initialize an empty list
channel_ids = st.session_state.get('channel_ids', [])

def Introduction():
    st.markdown(f'<p style = "font-size : 50px; font-weight : bold; text-align : center;">Introduction</p>',unsafe_allow_html=True)

    st.subheader("Project Introduction")
    st.write("Welcome to YouTube Channel Analysis project. This project is designed to analyze YouTube channels' data, "
             "including channel details, videos, comments, and more. You can fetch data from YouTube, store it in MongoDB and SQL, "
             "and perform various data analysis tasks")
    st.write("")


    st.subheader("How to Use")
    st.write("To get started, visit the 'Fetch Channel Data' page and enter the YouTube channel IDs you want to analyze. You can fetch data "
             "from YouTube by clicking the 'Fetch YouTube Data' button. After fetching the data, you can click on 'Display Youtube Channel Data' and display channel's information "
             "and perform data analysis tasks")
    st.write("")

    st.subheader("Data Analysis")
    st.write("Our project allows you to answer various questions related to YouTube channels, such as finding channels with the most "
             "subscribers, the most viewed videos, or channels that published videos in a specific year. You can select a question from "
             "the dropdown in the 'Channel Data' page to get insights into the data")

    st.subheader("Data Visualization")
    st.write("Our project provides data visualization capabilities to help you gain insights from the data. You can visualize the following aspects of the YouTube channel data using bar plots and pie charts:")

    st.write("1) Distribution of Subscribers: Visualize the distribution of subscribers among different YouTube channels")
    st.write("2) Total Number of Videos: Gain insights into the total number of videos published by each channel")
    st.write("3) Total Channel Views: Explore the distribution of views across different channels")
    
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.markdown(f'<p style="color: red; font-size: 18px; font-weight : bold">Note : If you are not Aware of the Channel ID, You can Convert  Channel name to  Channel ID  in  Channel Name Converter Page !!! </p>', unsafe_allow_html=True)

# Page for Channel name to channel_id
def Channel_Name_Converter():
    st.markdown(f'<p style = "font-size : 45px; font-weight:bold;">Converts Channel Name  to Channel_ID</p>',unsafe_allow_html=True)
    
    # Input channel name
    channel_name = st.text_input('Enter YouTube Channel Name')

    if st.button('Get Channel ID'):
        if channel_name:
            try:
                channel_id = get_channel_id(channel_name)

                if channel_id:
                    st.success(f'The channel ID for {channel_name} is: {channel_id}')
                else:
                    st.error(f'No channel ID found for the channel name: {channel_name}')
            except HttpError as e:
                if e.resp.status == 403:
                    st.error("Access to channel data is forbidden, Please check your API credentials")
                else:
                    st.error(f"Error fetching channel data: {str(e)}")
        else:
            st.warning('Please enter a YouTube channel name')

# Function for inserting data into MongoDB Atlas
def insert_data_to_mongodb(channel_data_multiselect):
    # new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['youtube_data_database']
    collection = db['channel_data_collection']
    channel_data_multiselect = get_channel_status(youtube, channel_ids)
    data = [d for d in channel_data_multiselect if isinstance(d, dict)]
    if data:
        collection.insert_many(data)
    client.close()


# Channel's Data page for selecting multiple channel_id's
def Channel_Data():
    st.markdown(
    f'<p style="color: red; text-align: center; font-size: 50px; font-weight: bold;">YouTube Channel Analysis</p>',
    unsafe_allow_html=True
)

    # Take channel_ids as input from the user
    channel_ids_multiselect = st.text_input("Enter Channel IDs (separated by comma)")
    channel_data_multiselect = None  # Define the variable outside the if block

    col1, col2 = st.columns(2)

    with col1:
        if st.button('Fetch Youtube Data'):
            if channel_ids_multiselect:
                channel_ids = [channel_id.strip() for channel_id in channel_ids_multiselect.split(",")]

                st.session_state['channel_ids'] = channel_ids
                try:
                    channel_data_multiselect = get_channel_status(youtube, channel_ids)
                    if channel_data_multiselect:
                        st.session_state['channel_data_multiselect'] = channel_data_multiselect
                        st.success("YouTube data fetched successfully!")
                except Exception as e:
                    if "quota" in str(e):
                        st.warning("Request limit exceeded, Please try again tomorrow")
                    else:
                        st.error(f"Error fetching YouTube data: {str(e)}")
            else:
                st.error("Please enter valid channel_ids")

    with col2:
        if st.button('Display YouTube Channel Data'):
            channel_data_multiselect = st.session_state.get('channel_data_multiselect')
            if channel_data_multiselect:
                # Display YouTube Channel Data
                for channel_info in channel_data_multiselect:
                    # Display selected channel information directly in Streamlit
                    st.subheader(f"Channel Name: {channel_info['Channel_Name']}")
                    st.write(f"Channel ID: {channel_info['Channel_Id']}")
                    st.write(f"Channel Views: {channel_info['Channel_Views']}")
                    st.write(f"Subscribers: {channel_info['Subscription_Count']}")
                    st.write(f"Total Videos: {channel_info['Video_Count']}")
                    st.write(f"Channel Status: {channel_info['Channel_Status']}")
                    st.write(f"Playlist ID: {channel_info['Playlist_Id']}")
                    st.write(f"Playlist Name: {channel_info['Playlist_Name']}")

                    # Display video details for each video
                    for i, video_info in enumerate(channel_info["Videos"], 1):
                        st.subheader(f"Video {i}: {video_info['Video_Name']}")
                        video_id = video_info.get(f'Video_Id_{i}', 'N/A')
                        st.write(f"Video ID: {video_id}")
                        st.write(f"Likes: {video_info['Like_Count']}")
                        st.write(f"Dislikes: {video_info['Dislike_Count']}")
                        st.write(f"Comments Count: {video_info['Comment_Count']}")
                        st.write(f"Duration: {video_info['Duration']}")
                        st.image(video_info['Thumbnail'], caption='Thumbnail URL')
    
    st.markdown(f'<p style = "font-size:35px; font-weight : bold; ">Insert Fetched Data into MongoDB</p>', unsafe_allow_html=True)
   

    col3, col4 = st.columns(2)

    # Button to upload data
    with col3:
        if st.button("Upload Data to MongoDB"):
            channel_data_multiselect = st.session_state.get('channel_data_multiselect')

            if channel_data_multiselect:
                # Extract dictionaries from the list
                data = [d for d in channel_data_multiselect if isinstance(d, dict)]

                if data:
                    insert_data_to_mongodb(data)

                    # Display success message
                    st.success("Data inserted into MongoDB successfully!")
                else:
                    st.warning("No data found ,Please check the provided channel ID(s)")

    st.markdown(f'<p style = "font-size:35px; font-weight:bold; ">Migrate Data to SQL Database</p>', unsafe_allow_html=True)


    if 'data_uploaded' not in st.session_state:
        st.session_state['data_uploaded'] = False

    if st.button('Insert Data into SQL'):
        update_data()
        st.session_state['data_uploaded'] = True
        st.success('Data inserted into SQL successfully!')

    # Question selection dropdown (visible only after data is uploaded)
    if st.session_state['data_uploaded']:
        conn = sqlite3.connect('channels_data.db')  
        cursor = conn.cursor()

        # Dropdown to select question and display answer
        selected_question = st.selectbox('Select a question', options=[
                                                '1.What are the names of all the videos and their corresponding channels?', 
                                                '2.Which channels have the most number of videos, and how many videos do they have?', 
                                                '3.What are the top 10 most viewed videos and their respective channels?', 
                                                '4.How many comments were made on each video, and what are their corresponding video names?', 
                                                '5.Which videos have the highest number of likes, and what are their corresponding channel names?', 
                                                '6.What is the total number of likes and dislikes for each video, and what are their corresponding video names?', 
                                                '7.What is the total number of views for each channel, and what are their corresponding channel names?', 
                                                '8.What are the names of all the channels that have published videos in the year 2022?', 
                                                '9.What is the average duration of all videos in each channel, and what are their corresponding channel names?', 
                                                '10.Which videos have the highest number of comments, and what are their corresponding channel names?'])

        # Query and display data based on the selected question
        if selected_question:
            result = execute_query(selected_question)
            if not result.empty:
                # result_df = pd.DataFrame(result, columns=[desc[0] for desc in cursor.description])
                st.table(result)
            else:
                st.write('No data available for the selected question')

        conn.close()

        # Function to delete all collections in MongoDB
        def delete_mongodb_collections():
            # Get the list of collection names
            collections = db.list_collection_names()
            
            if not collections:
                st.warning("No collection to delete")
            else:
                for collection_name in collections:
                    collection = db.get_collection(collection_name)
                    collection.delete_many({})  # Delete all documents in the collection
                st.success("All collection Data have been deleted from MongoDB")

        # Streamlit app
        st.title("Delete MongoDB Collection Data")

        if st.button("Delete MongoDB Collection Data"):
            delete_mongodb_collections()






#function to format y-axis labels in thousands (K)
def thousands(x, pos):
    if x >= 1000:
        value = int(x) / 1000
        return f"{value:.0f}K"
    else:
        return int(x)
    



def Channel_Data_Visualization():
    st.markdown('''<p style="font-size: 55px; font-weight: bold; text-align: center;">Channel's Data Visualization</p>''', unsafe_allow_html=True)

    
    # Get the channel data from session state
    channel_data_multiselect = st.session_state.get('channel_data_multiselect')

    if channel_data_multiselect:
        # DataFrame from the channel data
        df = pd.DataFrame(channel_data_multiselect)
        
        # subplots for bar plots
        fig, axes = plt.subplots(3, 1, figsize=(6, 10))   # 3 subplots in a single column 

        # bar plots
        sns.barplot(data=df, x='Channel_Name', y='Subscription_Count', ax=axes[0])
        axes[0].set_title('Subscribers')

        # Set the y-axis formatter for the third subplot
        axes[0].yaxis.set_major_formatter(FuncFormatter(thousands))

        sns.barplot(data=df, x='Channel_Name', y='Video_Count', ax=axes[1])
        axes[1].set_title('Total Videos')

        sns.barplot(data=df, x='Channel_Name', y='Channel_Views', ax=axes[2])
        axes[2].set_title('Channel Views')
        
        # Set the y-axis formatter for the third subplot
        axes[2].yaxis.set_major_formatter(FuncFormatter(thousands))
        
        # Adjust the layout and provide space between subplots
        plt.tight_layout(h_pad=4.0)

        # Display the bar plots
        st.pyplot(fig)
        
        # new figure and axis for the pie chart
        fig_pie, ax_pie = plt.subplots(figsize=(3, 3))

        # Extracts channel statuses
        channel_statuses = df['Channel_Status'].value_counts()
        
        colors = ['gold', 'lightcoral', 'lightskyblue', 'lightgreen']

        # pie chart for channel statuses with custom colors
        ax_pie.pie(channel_statuses, labels=channel_statuses.index, autopct='%1.1f%%', startangle=90, colors=colors)

        ax_pie.set_title('Channel Status Distribution', fontsize=8)

        # Add a shadow effect to the pie chart
        ax_pie.set_box_aspect(1)
        ax_pie.axis('equal')

        # Display the pie chart separately
        st.pyplot(fig_pie)
       
        video_count_scale = 10  # Adjust this factor as needed
        df['Video_Count_Scaled'] = df['Video_Count'] * video_count_scale

        # bar plot for subscribers and scaled video counts for each channel
        fig, ax = plt.subplots(figsize=(12, 6))  # Increase plot size
        width = 0.35
        x = range(len(df))
        ax.bar(x, df['Subscription_Count'], width, label='Subscribers')
        ax.bar([i + width for i in x], df['Video_Count_Scaled'], width, label=f'Video Count ')

        ax.set_xticks([i + width / 2 for i in x])
        ax.set_xticklabels(df['Channel_Name'], rotation=90)
        ax.set_xlabel('Channels')
        ax.set_ylabel('Counts')
        ax.set_title('Subscribers vs Video Count for Each Channel')

        # Use FuncFormatter to format y-axis labels as integers
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:.0f}'.format(x)))
        ax.legend()

        # Show the bar plot
        st.pyplot(fig)



# Run the app
def main():
    # sidebar with page selection
    page = st.sidebar.selectbox("Select a Page", ["Introduction","Fetch Channel Data","Channel Name Converter", "Channel Data Visualization"])

    # Render the selected page
    if page == "Introduction":
        Introduction()
    elif page == "Fetch Channel Data":
        Channel_Data()
    elif page == "Channel Name Converter":
        Channel_Name_Converter()
    elif page == "Channel Data Visualization":
        Channel_Data_Visualization()



if __name__ == '__main__':
    main()
