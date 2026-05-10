from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from math import ceil

app = Flask(__name__)

app.secret_key = "foodai_secret_key"

# IMAGE UPLOAD

UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MONGODB

client = MongoClient("mongodb+srv://admin:admin123@cluster01.qmuuxio.mongodb.net/?retryWrites=true&w=majority&appName=Cluster01")

db = client["foodai_database"]

restaurant_collection = db["restaurants"]
user_collection = db["users"]
favorite_collection = db["favorites"]

# HOME PAGE

@app.route('/')
def home():

    query = request.args.get('query')
    budget = request.args.get('budget')
    top_rated = request.args.get('top_rated')

    page = int(request.args.get('page', 1))

    per_page = 12

    all_restaurants = list(restaurant_collection.find())

    filtered_restaurants = []

    for restaurant in all_restaurants:

        score = 0

        if query:

            if query.lower() in restaurant["food"].lower():
                score += 5

            if query.lower() in restaurant["cuisine"].lower():
                score += 4

            if query.lower() in restaurant["location"].lower():
                score += 3

        else:

            score += 1

        if budget:

            if restaurant["price"] <= int(budget):
                score += 5

        else:

            score += 1

        if top_rated:

            if restaurant["rating"] >= 4.8:
                score += 5

        score += restaurant["rating"]

        restaurant["score"] = score

        if score > 0:

            filtered_restaurants.append(restaurant)

    recommended_restaurants = sorted(

        filtered_restaurants,

        key=lambda x: x["score"],

        reverse=True

    )

    total_pages = ceil(len(recommended_restaurants) / per_page)

    start = (page - 1) * per_page

    end = start + per_page

    paginated_restaurants = recommended_restaurants[start:end]

    return render_template(

        'index.html',

        restaurants=paginated_restaurants,

        page=page,

        total_pages=total_pages,

        user=session.get("user")

    )

# REGISTER

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        existing_user = user_collection.find_one({

            "email": request.form.get('email')

        })

        if existing_user:

            return "User already exists"

        user_collection.insert_one({

            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password')

        })

        return redirect('/login')

    return render_template('login.html')

# LOGIN

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        user = user_collection.find_one({

            "email": request.form.get('email'),
            "password": request.form.get('password')

        })

        if user:

            session["user"] = user["name"]

            return redirect('/')

        else:

            return "Invalid Email or Password"

    return render_template('login.html')

# LOGOUT

@app.route('/logout')
def logout():

    session.pop("user", None)

    session.pop("admin", None)

    return redirect('/')

# FAVORITE

@app.route('/favorite/<id>')
def favorite(id):

    if "user" not in session:

        return redirect('/login')

    restaurant = restaurant_collection.find_one({

        "_id": ObjectId(id)

    })

    favorite_collection.insert_one({

        "user": session["user"],
        "restaurant_name": restaurant["name"],
        "food": restaurant["food"],
        "location": restaurant["location"],
        "image": restaurant["image"]

    })

    return redirect('/')

# FAVORITES

@app.route('/favorites')
def favorites():

    if "user" not in session:

        return redirect('/login')

    user_favorites = list(

        favorite_collection.find({

            "user": session["user"]

        })

    )

    return render_template(

        'favorites.html',

        favorites=user_favorites,

        user=session.get("user")

    )

# DETAILS PAGE

@app.route('/restaurant/<id>')
def details(id):

    restaurant = restaurant_collection.find_one({

        "_id": ObjectId(id)

    })

    return render_template(

        'details.html',

        restaurant=restaurant,

        user=session.get("user")

    )

# DELETE

@app.route('/delete/<id>')
def delete_restaurant(id):

    if "admin" not in session:

        return redirect('/admin-login')

    restaurant_collection.delete_one({

        "_id": ObjectId(id)

    })

    return redirect('/')

# UPDATE

@app.route('/update/<id>', methods=['GET', 'POST'])
def update_restaurant(id):

    if "admin" not in session:

        return redirect('/admin-login')

    restaurant = restaurant_collection.find_one({

        "_id": ObjectId(id)

    })

    if request.method == 'POST':

        restaurant_collection.update_one(

            {

                "_id": ObjectId(id)

            },

            {

                "$set": {

                    "name": request.form.get('name'),
                    "food": request.form.get('food'),
                    "cuisine": request.form.get('cuisine'),
                    "location": request.form.get('location'),
                    "price": int(request.form.get('price')),
                    "rating": float(request.form.get('rating')),
                    "description": request.form.get('description')

                }

            }

        )

        return redirect('/')

    return render_template(

        'update.html',

        restaurant=restaurant

    )

# ADMIN LOGIN

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin123":

            session["admin"] = True

            return redirect('/admin')

        else:

            return "Invalid Admin Credentials"

    return render_template('admin_login.html')

# ADMIN PANEL

@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if "admin" not in session:

        return redirect('/admin-login')

    if request.method == 'POST':

        image = request.files['image']

        image_path = ""

        if image:

            image_path = os.path.join(

                app.config['UPLOAD_FOLDER'],

                image.filename

            )

            image.save(image_path)

        restaurant_collection.insert_one({

            "name": request.form.get('name'),
            "food": request.form.get('food'),
            "cuisine": request.form.get('cuisine'),
            "location": request.form.get('location'),
            "price": int(request.form.get('price')),
            "rating": float(request.form.get('rating')),
            "description": request.form.get('description'),
            "image": "/" + image_path

        })

        return redirect('/')

    return render_template('admin.html')

# RUN

if __name__ == '__main__':
    app.run(debug=True)