import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Create a connection to the MySQL database
engine = create_engine("mysql+pymysql://root:12345@localhost/youtube_database")

# Function to execute SQL queries and retrieve data
def execute_query(connection, query):
    with connection.connect() as conn:
        result = conn.execute(text(query))  # Use text() to create a SQLAlchemy text object
        data = pd.DataFrame(result.fetchall(), columns=result.keys())
    return data

# Streamlit App
def main(connection):
    st.title("YouTube Data Analysis")
    st.write("Query and analyze data from the MySQL data warehouse.")

    # Display options to query data
    query_option = st.selectbox("Select Query Option", [
        "What are the names of all the videos and their corresponding channels?",
        "Which channels have the most number of videos, and how many videos do they have?",
        "What are the top 10 most viewed videos and their respective channels?",
        "How many comments were made on each video, and what are their corresponding video IDs?",
        "Which videos have the highest number of likes, and what are their corresponding channel names?",
        "What is the total number of likes and dislikes for each video, and what are their corresponding video IDs?",
        "What is the total number of views for each channel, and what are their corresponding channel names?",
        "What are the names of all the channels that have published videos in the year 2022?",
        "What is the average duration of all videos in each channel, and what are their corresponding channel names?",
        "Which videos have the highest number of comments, and what are their corresponding channel names?"
    ])

    if query_option == "What are the names of all the videos and their corresponding channels?":
        query = "SELECT video_id, channel_name FROM youtube_data"
        data = execute_query(connection, query)
        st.dataframe(data)

    elif query_option == "Which channels have the most number of videos, and how many videos do they have?":
        query = "SELECT channel_name, COUNT(*) AS video_count FROM youtube_data GROUP BY channel_name ORDER BY video_count DESC"
        data = execute_query(connection, query)
        st.dataframe(data)

    elif query_option == "What are the top 10 most viewed videos and their respective channels?":
        query = "SELECT video_id, channel_name, views FROM youtube_data ORDER BY views DESC LIMIT 10"
        data = execute_query(connection, query)
        st.dataframe(data)

    elif query_option == "How many comments were made on each video, and what are their corresponding video names?":
        # SQL query to find comments count for each video
        query = "SELECT video_id, COUNT(*) AS comments_count FROM youtube_data GROUP BY video_id"
        data = execute_query(query)
        st.dataframe(data)

    elif query_option == "Which videos have the highest number of likes, and what are their corresponding channel names?":
        # SQL query to find videos with the highest number of likes
        query = "SELECT video_id, channel_name, likes FROM youtube_data ORDER BY likes DESC LIMIT 10"
        data = execute_query(query)
        st.dataframe(data)

    elif query_option == "What is the total number of likes and dislikes for each video, and what are their corresponding video names?":
        # SQL query to find total likes and dislikes for each video
        query = "SELECT video_id, SUM(likes) AS total_likes, SUM(dislikes) AS total_dislikes FROM youtube_data GROUP BY video_id"
        data = execute_query(query)
        st.dataframe(data)

    elif query_option == "What is the total number of views for each channel, and what are their corresponding channel names?":
        # SQL query to find total views for each channel
        query = "SELECT channel_name, SUM(views) AS total_views FROM youtube_data GROUP BY channel_name"
        data = execute_query(query)
        st.dataframe(data)

    elif query_option == "What are the names of all the channels that have published videos in the year 2022?":
        # SQL query to find channels with videos published in 2022
        query = "SELECT DISTINCT channel_name FROM youtube_data WHERE YEAR(publish_date) = 2022"
        data = execute_query(query)
        st.dataframe(data)

    elif query_option == "What is the average duration of all videos in each channel, and what are their corresponding channel names?":
        # SQL query to find average duration of videos in each channel
        query = "SELECT channel_name, AVG(duration) AS average_duration FROM youtube_data GROUP BY channel_name"
        data = execute_query(query)
        st.dataframe(data)

    elif query_option == "Which videos have the highest number of comments, and what are their corresponding channel names?":
        # SQL query to find videos with the highest number of comments
        query = "SELECT video_id, channel_name, COUNT(*) AS comments_count FROM youtube_data GROUP BY video_id, channel_name ORDER BY comments_count DESC LIMIT 10"
        data = execute_query(query)
        st.dataframe(data)

if __name__ == "__main__":
    main(engine)
