import pymongo
import pymysql

# Connect to MongoDB
mongo_client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
mongo_db = mongo_client['youtube_data_db']
mongo_collection = mongo_db['channel_data']

# Connect to MySQL
mysql_connection = pymysql.connect(
    host='localhost',
    user='root',
    password='12345',
    database='youtube_database'
)

# Create MySQL table
create_table_query = """
CREATE TABLE IF NOT EXISTS youtube_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    channel_name VARCHAR(255) NOT NULL,
    subscribers INT NOT NULL,
    total_video_count INT NOT NULL,
    playlist_id VARCHAR(255) NOT NULL,
    video_id VARCHAR(255) NOT NULL,
    likes INT NOT NULL,
    dislikes INT NOT NULL,
    comments INT NOT NULL
)
"""

with mysql_connection.cursor() as cursor:
    cursor.execute(create_table_query)

# Migrate data from MongoDB to MySQL
for document in mongo_collection.find():
    channel_name = document['channel_name']
    subscribers = int(document['subscribers'])
    total_video_count = int(document['total_videos'])
    playlist_id = document['playlist_id']

    for video_info in document['video_data']:
        video_id = video_info['Video ID']
        likes = int(video_info['Likes'])
        dislikes = int(video_info['Dislikes'])
        comments = int(video_info['Comments'])

        insert_query = """
        INSERT INTO youtube_data (channel_name, subscribers, total_video_count, playlist_id, video_id, likes, dislikes, comments)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        with mysql_connection.cursor() as cursor:
            values = (channel_name, subscribers, total_video_count, playlist_id, video_id, likes, dislikes, comments)
            cursor.execute(insert_query, values)

        mysql_connection.commit()

print("Data migration to MySQL completed.")
