import pandas as pd
from pymongo import MongoClient

# CONNECT MONGODB

client = MongoClient("mongodb://localhost:27017/")

db = client["foodai_database"]

restaurant_collection = db["restaurants"]

# READ CSV FILE

df = pd.read_csv(

    "dataset/zomato.csv",

    encoding='latin1'

)

# CLEAN DATA

df = df.fillna("Not Available")

# LIMIT DATA

df = df.head(500)

# CREATE RESTAURANT LIST

restaurants = []

for index, row in df.iterrows():

    restaurant = {

        "name": str(row.get("name", "Unknown")),

        "food": str(row.get("cuisines", "Food")),

        "cuisine": str(row.get("cuisines", "Cuisine")),

        "location": str(row.get("location", "India")),

        "price": 300,

        "rating": 4.2,

        "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1200&auto=format&fit=crop",

        "description": "Real restaurant imported from dataset."

    }

    restaurants.append(restaurant)

# INSERT INTO MONGODB

if restaurants:

    restaurant_collection.insert_many(restaurants)

    print("✅ Dataset Imported Successfully")

else:

    print("❌ No Data Found")