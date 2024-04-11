import gzip
from datetime import datetime
import argparse
import yaml
from pymongo import MongoClient
import requests
from os import path, makedirs
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

CONFIG = {
    'db': {
        'host': 'MONGODBIP',
        'port': 0000,
    },
}

CSV_LINK = "https://nathan.bonnell.fr/public/tile_placements.csv"
FILES_PATH = './dataset/'

COLORS = {
    0: [255, 255, 255],
    1: [228, 228, 228],
    2: [136, 136, 136],
    3: [34, 34, 34],
    4: [255, 167, 209],
    5: [229, 0, 0],
    6: [229, 149, 0],
    7: [160, 106, 66],
    8: [229, 217, 0],
    9: [148, 224, 68],
    10: [2, 190, 1],
    11: [0, 229, 240],
    12: [0, 131, 199],
    13: [0, 0, 234],
    14: [224, 74, 255],
    15: [130, 0, 128]
}

def init_db() -> MongoClient:
    """Initiate DB connection

    Returns:
        MongoClient: MongoDB client
    """
    client = MongoClient(CONFIG['db']['host'], CONFIG['db']['port'])
    db = client['rplace']
    return db

def init_collection(db) -> MongoClient:
    """Initiate collection

    Args:
        db (MongoClient): MongoDB client

    Returns:
        MongoClient: MongoDB collection
    """
    return db['rplace_history_2017']

def download_file() -> None:
    """Download file from CSV_LINK
    """
    if not path.exists(FILES_PATH):
        makedirs(FILES_PATH)
    response = requests.get(CSV_LINK)
    with open(FILES_PATH + 'tile_placements.csv', 'wb') as f:
        f.write(response.content)

def load_data(files) -> list:
    """Load data from files

    Args:
        files (list): List of files

    Returns:
        list: List of dataframes
    """
    data = []
    for file in files:
        with gzip.open(file, 'rb') as f:
            df = pd.read_csv(f)
            data.append(df)
    return data

def load_data_to_db(files, collection) -> None:
    """Load data to MongoDB

    Args:
        files (list): List of files
        collection (MongoClient): MongoDB collection
    """
    collection.delete_many({})
    for file in files:
        with open(file, 'rb') as f:
            df = pd.read_csv(f)
            print(f"Loading data from file: {file} (this may take a while (again))")
            records = df.to_dict(orient='records')
            for record in records:
                try:
                    record['ts'] = datetime.fromtimestamp(record['ts'] / 1000)
                    record['x_coordinate'] = int(record['x_coordinate'])
                    record['y_coordinate'] = int(record['y_coordinate'])
                except Exception as e:
                    print(f"Error processing record: {record} with error: {e}")
                    continue
            collection.insert_many(records)
            print(f"Data from file: {file} loaded")

def get_data(collection, query) -> list:
    """Get data from MongoDB

    Args:
        collection (MongoClient): MongoDB collection
        query (dict): Query

    Returns:
        list: List of data
    """
    result = collection.find(query)
    return result

def get_distinct_users(collection) -> list:
    """Get distinct users from MongoDB

    Args:
        collection (MongoClient): MongoDB collection

    Returns:
        list: List of distinct users
    """
    pipeline = [
        {"$group": {"_id": "$user"}},
        {"$project": {"_id": 0, "user": "$_id"}}
    ]
    result = list(collection.aggregate(pipeline))
    return [doc['user'] for doc in result]

def get_bot_users(collection) -> list:
    """Get bot users from MongoDB (users with perfect 5min interval between pixel placements)

    Args:
        collection (MongoClient): MongoDB collection

    Returns:
        list: List of bot users
    """
    pipeline = [
        {"$sort": {"ts": 1}},
        {"$group": {
            "_id": "$user",
            "ts": {"$push": "$ts"}
        }},
        {"$project": {
            "_id": 0,
            "user": "$_id",
            "ts": 1
        }}
    ]
    result = list(collection.aggregate(pipeline))
    bot_users = []
    for doc in result:
        timestamps = doc['ts']
        for i in range(len(timestamps) - 1):
            if (timestamps[i + 1] - timestamps[i]).total_seconds() >= 300:
                break
        else:
            bot_users.append(doc['user'])
    return bot_users

def get_most_active_users(collection) -> list:
    """Get most active users from MongoDB

    Args:
        collection (MongoClient): MongoDB collection

    Returns:
        list: List of most active users
    """
    pipeline = [
        {"$group": {
            "_id": "$user",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {
            "_id": 0,
            "user": "$_id",
            "count": 1
        }}
    ]
    result = list(collection.aggregate(pipeline))
    return result

def get_most_modified_pixel(collection) -> dict:
    """Get most modified pixel from MongoDB

    Args:
        collection (MongoClient): MongoDB collection

    Returns:
        dict: Most modified pixel
    """
    pipeline = [
        {"$group": {
            "_id": {"x": "$x_coordinate", "y": "$y_coordinate"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 1},
        {"$project": {
            "_id": 0,
            "x": "$_id.x",
            "y": "$_id.y",
            "count": 1
        }}
    ]
    result = list(collection.aggregate(pipeline))
    return result[0]

def get_less_modified_pixel(collection) -> dict:
    """Get less modified pixel from MongoDB

    Args:
        collection (MongoClient): MongoDB collection

    Returns:
        dict: Less modified pixel
    """
    pipeline = [
        {"$group": {
            "_id": {"x": "$x_coordinate", "y": "$y_coordinate"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": 1}},
        {"$limit": 1},
        {"$project": {
            "_id": 0,
            "x": "$_id.x",
            "y": "$_id.y",
            "count": 1
        }}
    ]
    result = list(collection.aggregate(pipeline))
    return result[0]

def generate_image(data) -> None:
    """Generate image from data

    Args:
        data (list): List of data
    """
    canvas = np.zeros((1001, 1001, 3), dtype=np.uint8)
    for row in data:
        try:
            y = row['x_coordinate']
            x = row['y_coordinate']
            color = row['color']
            color = COLORS[color]
            canvas[x, y] = color
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue
    plt.imshow(canvas)
    plt.show()

def generate_heatmap(data) -> None:
    """Generate heatmap from data

    Args:
        data (list): List of data
    """
    canvas = np.zeros((1001, 1001), dtype=np.uint8)
    for row in data:
        try:
            y = row['x_coordinate']
            x = row['y_coordinate']
            canvas[x, y] += 1
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue
    plt.imshow(canvas, cmap='hot', interpolation='nearest')
    plt.axis(False)
    plt.show()

def generate_histogram(data) -> None:
    """Generate histogram from data

    Args:
        data (list): List of data
    """
    histogram_data = {}
    for row in data:
        try:
            timestamp = row['ts']
            timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            if timestamp in histogram_data:
                histogram_data[timestamp] += 1
            else:
                histogram_data[timestamp] = 1
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue
    _, ax = plt.subplots()
    ax.bar(histogram_data.keys(), histogram_data.values(), width=0.03)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval = 2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %Hh'))
    plt.xlabel('Hour')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.title('Histogram of R/Place 2017 Data')
    plt.show()

def generate_color_diagram(data) -> None:
    """Generate circular diagram of color usage from data

    Args:
        data (list): List of data
    """
    color_data = {}
    for row in data:
        try:
            color_id = row['color']
            if color_id in color_data:
                color_data[color_id] += 1
            else:
                color_data[color_id] = 1
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue
    colors = [COLORS[color_id] for color_id in color_data.keys()]
    colors = [[channel / 255 for channel in color] for color in colors]
    _, ax = plt.subplots()
    _, _, autotexts = ax.pie(color_data.values(), autopct='%1.1f%%', pctdistance=1.1, colors=colors)
    plt.setp(autotexts, size=8, weight="bold")
    ax.axis('equal')
    plt.title('Color Diagram of Data')
    plt.show()

def load_config() -> dict:
    """Load config from config.yaml

    Returns:
        dict: Config
    """
    with open('config.yaml') as f:
        # use safe_load instead load
        config = yaml.safe_load(f)
    return config

def parse_args() -> argparse.Namespace:
    """Parse arguments

    Returns:
        argparse.Namespace: Arguments
    """
    parser = argparse.ArgumentParser(description='R/Place 2017 Data Analysis')
    parser.add_argument('-i', '--init', action='store_true', help='Download file and initialize DB and load data')
    parser.add_argument('-g', '--generate', action='store_true', help='Generate image from data (pixel placement)')
    parser.add_argument('-hm', '--heatmap', action='store_true', help='Generate heatmap from data (placement count per pixel)')
    parser.add_argument('-hi', '--histogram', action='store_true', help='Generate histogram from data (pixel count per hour)')
    parser.add_argument('-co', '--color', action='store_true', help='Generate circlar diagram of color usage from data (color count)')
    parser.add_argument('-u', '--user', action='store_true', help='Get distinct users from data')
    parser.add_argument('-b', '--bots', action='store_true', help='Get bot users from data')
    parser.add_argument('-mu', '--mostuser', action='store_true', help='Get most active users from data')
    parser.add_argument('-mp', '--mostpixel', action='store_true', help='Get most modified pixel from data')
    parser.add_argument('-lp', '--lesspixel', action='store_true', help='Get less modified pixel from data')
    return parser.parse_args()

if __name__ == '__main__':
    CONFIG = load_config()
    args = parse_args()
    db = init_db()
    collection = init_collection(db)
    print("DB and collection initialized")
    if args.init:
        print("Initializing...", end='\r')
        print("Downloading file... (this may take a while)")
        download_file()
        files = [FILES_PATH + 'tile_placements.csv']
        print("File downloaded, loading data to DB...", end='\r')
        load_data_to_db([FILES_PATH + 'tile_placements.csv'], collection)
        print("Data loaded to DB, exiting program")
        exit(0)
    elif args.generate:
        print("Generating image...")
        data = get_data(collection, {})
        print("Data loaded, generating image... (this may take a while)")
        generate_image(data)
    elif args.heatmap:
        print("Generating heatmap...")
        data = get_data(collection, {})
        print("Data loaded, generating heatmap... (this may take a while)")
        generate_heatmap(data)
    elif args.histogram:
        print("Generating histogram...")
        data = get_data(collection, {})
        print("Data loaded, generating histogram... (this may take a while)")
        generate_histogram(data)
    elif args.color:
        print("Generating color diagram...")
        data = get_data(collection, {})
        print("Data loaded, generating color diagram... (this may take a while)")
        generate_color_diagram(data)
    elif args.user:
        print("Getting distinct users...")
        users = get_distinct_users(collection)
        print(f"Distinct users: {len(users)}")
    elif args.bots:
        print("Getting bot users...")
        users = get_bot_users(collection)
        print(f"Bot users: {len(users)}")
    elif args.mostuser:
        print("Getting most active users...")
        users = get_most_active_users(collection)
        for i, user in enumerate(users):
            print(f"{i + 1}. User: {user['user']}, Count: {user['count']}")
    elif args.mostpixel:
        print("Getting most modified pixel...")
        pixel = get_most_modified_pixel(collection)
        print(f"Most modified pixel: \n- Coordonnées : {pixel['x']}, {pixel['y']}\n- Nombre de modifications : {pixel['count']}")
    elif args.lesspixel:
        print("Getting less modified pixel...")
        pixel = get_less_modified_pixel(collection)
        print(f"Less modified pixel: \n- Coordonnées : {pixel['x']}, {pixel['y']}\n- Nombre de modifications : {pixel['count']}")
    else:
        print("Please provide an argument")
        exit(1)
