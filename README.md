# What is this application for
This is an example application to store information on items in stock for a sports retail outlet. 

# Features
The application is only limited to storing variables such as name, description and the user who has created the item.

The application uses Google OAuth 2.0 for users to sign in and create an account.

After logging in, a user has the ability to add, update, or delete item information. Users can only modify those items that they themselves have created.

The application also provides a JSON endpoints.
* For all items - `/catalog.json`
* For a specific item - `/catalog/<category_name>/<item_name>/json`. For example `/catalog/Archery/Bows/json`

# Dependencies
* python
* Flask
* SQLAlchemy
* Google API Server
* SQLite

# Running the application
To run the application, please follow the following steps;
1. Obtain a OAuth 2.0 Client ID from Google APIs & Services 
2. Download JSON format of the Client ID and rename the file `client_secrets.json` and save the file in the root directory. 
3. Load the datatabase by running the command `python models.py`
4. Populate the database with dummy data by running the command `python dummydata.py`
5. Run the application with the command `python catalog.py`






