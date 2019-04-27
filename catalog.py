from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base, Category, Item, User

# Create secure login to generate unique session tokens
from flask import session as login_session
import random
import string  # from python libraries

# To handle callback method for login
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameters'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # Upgrade the authorisation code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        # Exchanges the authorisation object into a credentials object
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade authorisation code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            'Token user ID does not match the given user ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match the app"), 401)
        print("Token's client ID does not match the app")
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if the user is already logged in
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            "Current user already connected."), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # check if a user exists. otherwise, create a new user
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "style = "width: 300px; height: 300px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output

# Disconnect a user
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user
    access_token = login_session['access_token']
    print 'In gconnect access token is %s' % access_token
    print 'Username is'
    print login_session['username']
    if access_token is None:
        response = make_response(json.dumps(
            'Current user is not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Remove token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    # Store Google's response
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's session
        del login_session['access_token']
        del login_session['username']
        del login_session['picture']
        del login_session['email']
        response = make_response(json.dumps('You are now disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        print response
        return redirect('/')
    else:
        # For other reasons
        response = make_response(json.dumps('Failed to revoke the token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Takes the login session and creates a new user in the database
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Takes user id and returns the user object
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Takes an email address and returns the id
def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Show all items
@app.route('/')
def showAllItems():
    items = session.query(Item).join(Category).order_by(Category.name).all()
    return render_template('items.html', items=items)


# Show all items for a category
@app.route('/catalog/<category_name>/items')
def showItemsPerCategory(category_name):
    category_id = session.query(Category).filter_by(name=category_name).first()
    items = session.query(Item).filter_by(category_id=category_id.id).all()
    return render_template('items.html', items=items)


# Add an item
@app.route('/catalog/items/new', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    if request.method == 'POST':
        category_name = request.form['category']
        category_id = session.query(Category).filter_by(
            name=category_name).first()
        item = Item(name=request.form['name'],
                    description=request.form['description'],
                    category_id=category_id.id,
                    user_id=login_session['user_id'])
        session.add(item)
        session.commit()
        return redirect(url_for('showAllItems'))
    else:
        return render_template('new_item.html', categories=categories)

# Show an item
@app.route('/catalog/<category_name>/<item_name>')
def showItem(category_name, item_name):
    category_id = session.query(Category).filter_by(name=category_name).first()
    item = session.query(Item).filter_by(
        category_id=category_id.id, name=item_name).first()
    creator = getUserInfo(item.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('public_item.html', item=item, creator=creator)
    else:
        return render_template('item.html', item=item,  creator=creator)

# Edit an item
@app.route('/catalog/<item_name>/edit', methods=['GET', 'POST'])
def editItem(item_name):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(name=item_name).first()
    if item.user_id != login_session['user_id']:
        return """<script>function myFunction()
        {alert('You are not authorized to edit this item');}
        </script><body onload='myFunction()'>"""
    categories = session.query(Category).all()
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            # retrive the updated category
            editCategoryName = request.form['category']
            editCategory = session.query(Category).filter_by(
                name=editCategoryName).first()  # find the category
            # update the category id in the Item database
            item.category_id = editCategory.id
        session.add(item)
        session.commit()
        return redirect(url_for('showItem', item_name=item.name,
                                category_name=item.category.name))
    else:
        return render_template('edit_item.html', item=item,
                               categories=categories)


# Delete an item
@app.route('/catalog/<item_name>/delete', methods=['GET', 'POST'])
def deleteItem(item_name):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(name=item_name).first()
    if itemToDelete.user_id != login_session['user_id']:
        return """<script>function myFunction()
        {alert('You are not authorized to edit this item');}
        </script><body onload='myFunction()'>"""
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showAllItems'))
    else:
        return render_template('delete_item.html', item=itemToDelete)


# JSON endpoint for all items in the catalog
@app.route('/catalog.json')
def catalogJSON():
    items = session.query(Item).all()
    return jsonify(items=[i.serialize for i in items])

# JSON endpont for an item in the catalog
@app.route('/catalog/<category_name>/<item_name>/json')
def itemJSON(category_name, item_name):
    category_id = session.query(Category).filter_by(name=category_name).first()
    item = session.query(Item).filter_by(category_id=category_id.id,
                                         name=item_name).first()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'  # required for Flask Session
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
