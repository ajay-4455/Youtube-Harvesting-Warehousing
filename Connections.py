

#SQL Library
import sqlite3

#Mongodb Library
import pymongo
from pymongo import MongoClient

#Data manipulation and webapplication Librarys
import pandas as pd
import streamlit as st


# MongoDB Connection details
uri = 'mongodb://127.0.0.1:27017/'
mongo_client = MongoClient(uri)
db = mongo_client['youtube_data_database']
collection = db['channel_data_collection']


#sqlite Connection details

# SQLite database file
sqlite_db_file = 'channels_data.db'

conn = sqlite3.connect(sqlite_db_file)
cursor = conn.cursor()


#defining the table schemas

#tables in SQLite
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Channel (
        Channel_Name VARCHAR(255),
        Channel_Id VARCHAR(255) PRIMARY KEY,
        Channel_Views INT,
        Video_Count INT,
        Channel_Description TEXT,
        Channel_Status VARCHAR(255)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Playlist (
        Playlist_Id VARCHAR(255) PRIMARY KEY,
        Channel_Id VARCHAR(255),
        Playlist_Name VARCHAR(255),
        FOREIGN KEY (Channel_Id) REFERENCES Channel (Channel_Id)
        
    )
''')

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Comment (
        Video_Id VARCHAR(255),
        Comment_Id VARCHAR(255) PRIMARY KEY,
        Comment_Text TEXT,
        Comment_Author VARCHAR(255),
        Comment_PublishedAt DATETIME,
        FOREIGN KEY (Video_Id) REFERENCES Video (Video_Id)
        )
    """)


cursor.execute('''
    CREATE TABLE IF NOT EXISTS Video (
        Playlist_Id VARCHAR(255),
        Video_Id VARCHAR(255) PRIMARY KEY,
        Video_Name VARCHAR(255),
        Video_Description TEXT,
        PublishedAt DATETIME,
        View_Count INT,
        Like_Count INT,
        Dislike_Count INT,
        Favorite_Count INT,
        Comment_Count INT,
        Duration INT,
        Thumbnail VARCHAR(255),
        Caption_Status VARCHAR(255),
        FOREIGN KEY (Playlist_Id) REFERENCES Playlist (Playlist_Id)
    )
''')


# Function to fetch data from MongoDB and update SQLite tables

def update_data():
    conn = sqlite3.connect('channels_data.db')  

    # columns you want to retrieve
    columns = ['Channel_Name', 'Channel_Id','Channel_Views', 'Video_Count','Channel_Description', 'Channel_Status']

    # Retrieves JSON channel data from MongoDB
    channel_data = list(collection.find({}, {column: 1 for column in columns}))

    # Update the channel table
    channel_df = pd.DataFrame(channel_data, columns=columns)
    channel_df.to_sql('Channel', conn, if_exists='replace', index=False)

    # columns  to retrieve
    columns_1 = ['Playlist_Id', 'Channel_Id','Playlist_Name']

    # Retrieves playlist data from MongoDB
    playlist_data = list(collection.find({}, {column: 1 for column in columns_1}))

    # Update Playlist table
    playlist_df = pd.DataFrame(playlist_data, columns=columns_1)
    playlist_df.to_sql('Playlist', conn, if_exists='replace', index=False)

    # Retrieves comment data from MongoDB
    comment_data = list(collection.find({}))

    # empty lists to store data
    video_ids = []
    comment_ids = []
    comment_texts = []
    comment_authors = []
    comment_published_dates = []

    # Iterate over the MongoDB data
    for doc in comment_data:
        videos = doc.get('Videos', [])  # Get the 'Videos' field, default to an empty list if not present

        for video in videos:
            video_id = video.get('Video_Id_1')  
            if video_id:
                comments = video.get('Comments', {})  #'Comments' field, default to an empty dict if not present

                for comment_id, comment in comments.items():
                    # Extract the desired fields from the comment
                    comment_text = comment.get('Comment_Text')
                    comment_author = comment.get('Comment_Author')
                    comment_published_at = comment.get('Comment_PublishedAt')

                    # Appending the extracted data to the respective lists
                    video_ids.append(video_id)
                    comment_ids.append(comment_id)
                    comment_texts.append(comment_text)
                    comment_authors.append(comment_author)
                    comment_published_dates.append(comment_published_at)

    # DataFrame from the extracted data
    comments_df = pd.DataFrame({
        'Video_Id': video_ids,
        'Comment_Id': comment_ids,
        'Comment_Text': comment_texts,
        'Comment_Author': comment_authors,
        'Comment_PublishedAt': comment_published_dates
    })

    comments_df.to_sql('Comment', conn, if_exists='replace', index=False)

    # Retrieves the videos data from MongoDB
    # Define the columns
    columns_2 = ['Playlist_Id', 'Video_Id', 'Video_Name', 'Video_Description', 'PublishedAt', 'View_Count', 'Like_Count', 'Dislike_Count', 'Favorite_Count', 'Comment_Count', 'Duration', 'Thumbnail', 'Caption_Status']
    video_data = list(collection.find({}, {'Playlist_Id': 1, 'Videos': 1}))
    data = {column: [] for column in columns_2}

    # Function to append video data to the data dictionary
    def append_video_data(video_id, playlist_id, video):
        data['Playlist_Id'].append(playlist_id)
        data['Video_Id'].append(video_id)
        data['Video_Name'].append(video.get('Video_Name'))
        data['Video_Description'].append(video.get('Video_Description'))
        data['PublishedAt'].append(video.get('PublishedAt'))
        data['View_Count'].append(video.get('View_Count'))
        data['Like_Count'].append(video.get('Like_Count'))
        data['Dislike_Count'].append(video.get('Dislike_Count'))
        data['Favorite_Count'].append(video.get('Favorite_Count'))
        data['Comment_Count'].append(video.get('Comment_Count'))
        data['Duration'].append(video.get('Duration'))
        data['Thumbnail'].append(video.get('Thumbnail'))
        data['Caption_Status'].append(video.get('Caption_Status'))

    # Iterate over the MongoDB data
    for doc in video_data:
        playlist_id = doc.get('Playlist_Id')
        videos = doc.get('Videos')

        for video in videos:
            for key, value in video.items():
                if key.startswith('Video_Id_'):
                    video_id = value
                    append_video_data(video_id, playlist_id, video)

    # DataFrame from the collected data
    video_df = pd.DataFrame(data)
    video_df.to_sql('Video', conn, if_exists='replace', index=False)

    conn.close()




# Function to execute the selected question's query
def execute_query(selected_question):
    conn = sqlite3.connect('channels_data.db')  
    cursor = conn.cursor()

    if selected_question =='1.What are the names of all the videos and their corresponding channels?':
        query='''
        SELECT v.Video_Name, c.Channel_Name
        FROM Video AS v
        JOIN Playlist AS p ON v.Playlist_Id = p.Playlist_Id
        JOIN Channel AS c ON p.Channel_Id = c.Channel_Id
        LIMIT 50;
        '''
        
        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Video_Name','Channel_Name'])
        
    
    elif selected_question=='2.Which channels have the most number of videos, and how many videos do they have?':

        query='''
        SELECT Channel_Name, Video_Count
        FROM Channel
        ORDER BY Video_Count DESC
        LIMIT 10;
        '''

        
        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Channel_Name','Video_Count'])

    elif selected_question=='3.What are the top 10 most viewed videos and their respective channels?':
        query = '''
        SELECT Video_Name,View_Count
        FROM Video 
        ORDER BY View_Count DESC
        LIMIT 10
        '''
        

        
        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Video_Name','View_Count'])

    elif selected_question=='4.How many comments were made on each video, and what are their corresponding video names?':
        query = '''
        SELECT v.Video_Name, v.Comment_Count
        FROM Video v;
        '''


        
        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Video_Name','Comment_Count'])

    elif selected_question=='5.Which videos have the highest number of likes, and what are their corresponding channel names?':
        query='''
        SELECT Video.Video_Name, Channel.Channel_Name, Video.Like_Count
        FROM Video
        JOIN Playlist ON Playlist.Playlist_Id=Video.Playlist_Id
        JOIN Channel ON Playlist.Channel_Id = Channel.Channel_Id
        ORDER BY Video.Like_Count DESC
        LIMIT 10;
        '''

        
        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Video_Name','Channel_Name','Like_Count'])

    elif selected_question=='6.What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
        query = '''
        SELECT Video.Video_Name, Channel.Channel_Name, SUM(Video.Like_Count) AS Total_Likes, SUM(Video.Dislike_Count) AS Total_Dislikes
        FROM Video
        JOIN Playlist ON Playlist.Playlist_Id=Video.Playlist_Id
        JOIN Channel ON Playlist.Channel_Id = Channel.Channel_Id
        GROUP BY Video.Video_Id
        ORDER BY Total_Likes DESC
        LIMIT 10;
        '''

        
        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Video_Name','Channel_Name','Total_Likes','Total_Dislikes'])

    elif selected_question=='7.What is the total number of views for each channel, and what are their corresponding channel names?':
        query='''
        SELECT Channel.Channel_Name, SUM(Video.View_Count) AS Total_Views
        FROM Video
        JOIN Playlist ON Playlist.Playlist_Id=Video.Playlist_Id
        JOIN Channel ON Playlist.Channel_Id = Channel.Channel_Id
        GROUP BY Channel.Channel_Id
        ORDER BY Total_Views DESC
        LIMIT 10;
        '''
       
        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Channel_Name','Total_Views'])

    elif selected_question=='8.What are the names of all the channels that have published videos in the year 2022?':
        query='''
        SELECT DISTINCT Channel.Channel_Name, Video.PublishedAt
        FROM Video
        JOIN Playlist ON Playlist.Playlist_Id=Video.Playlist_Id
        JOIN Channel ON Playlist.Channel_Id = Channel.Channel_Id
        WHERE strftime('%Y', datetime(Video.PublishedAt)) = '2022'
        GROUP BY Channel.Channel_Id;
        '''

        result = pd.DataFrame(cursor.execute(query).fetchall(),columns=['Channel_Name','PublishedAt'])

    elif selected_question=='9.What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        query = '''
        SELECT Channel.Channel_Name, AVG(
            SUBSTR(Video.Duration, 3, INSTR(Video.Duration, 'M') - 3) * 60 + 
            SUBSTR(Video.Duration, INSTR(Video.Duration, 'M') + 1, INSTR(Video.Duration, 'S') - INSTR(Video.Duration, 'M') - 1)
        ) AS Average_Duration
        FROM Video
        JOIN Playlist ON Playlist.Playlist_Id=Video.Playlist_Id
        JOIN Channel ON Playlist.Channel_Id = Channel.Channel_Id
        GROUP BY Channel.Channel_Id;
        '''

        result = pd.DataFrame(cursor.execute(query).fetchall(), columns=['Channel_Name', 'Average_Duration'])

    elif selected_question=='10.Which videos have the highest number of comments, and what are their corresponding channel names?':
        query = '''
        SELECT c.Channel_Name, v.Video_Name, v.Comment_Count
        FROM Video v
        JOIN Playlist p ON v.Playlist_Id = p.Playlist_Id
        JOIN Channel c ON p.Channel_Id = c.Channel_Id
        ORDER BY v.Comment_Count DESC
        LIMIT 10;
        '''

        result = pd.DataFrame(cursor.execute(query).fetchall(), columns=['Channel_Name', 'Video_Name','Comment_Count'])

            
    else:
        result = None

    conn.close()

    return result

    




















































































































