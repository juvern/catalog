from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Category, Base, Item, User

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy users
user1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://randomuser.me/api/portraits/thumb/men/60.jpg')
session.add(user1)
session.commit()

user2 = User(name="Terri Nguyen", email="terri.nguyen43@example.com",
             picture='https://randomuser.me/api/portraits/thumb/women/62.jpg')
session.add(user2)
session.commit()

# Add categories
cat1 = Category(name="American Football")
session.add(cat1)
session.commit()

cat2 = Category(name="Aqua Fitness")
session.add(cat2)
session.commit()

cat3 = Category(name="Archery")
session.add(cat3)
session.commit()

cat4 = Category(name="Athletics")
session.add(cat4)
session.commit()

cat5 = Category(name="Badminton")
session.add(cat5)
session.commit()

# Add items to categories
item1 = Item(name="Badminton Racket",
             description='''Beginner badminton player who plays
             badminton occasionally wiith their friends during
             the weekend and vacation. This racket gives you an easy,
             fun and affordable way of getting into badminton.''',
             category_id=5, user_id=1)
session.add(item1)
session.commit()


item2 = Item(name="Bows",
             description='''Are you looking to give archery a go?
             We developed the Adult Disco 100 bow just for you.
             It is suitable for both right and left-hander
             thanks to its central sight grip.''',
             category_id=3, user_id=1)
session.add(item2)
session.commit()

item3 = Item(name="Targets",
             description='''We designed this target face
             to get the measure of your performance
             thanks to its 80 cm x 80 cm target.''',
             category_id=3, user_id=1)
session.add(item3)
session.commit()

item4 = Item(name="Shuttlecocks",
             description='''This single shuttle will
             provide you with stable trajectories thanks
             to its plastic skirt. A small touch of colour
             keeps the shuttle nicely visible while in play.''',
             category_id=5, user_id=2)
session.add(item4)
session.commit()

item5 = Item(name="Badminton Strings",
             description='''Designed for badminton players
             looking for strings with a good balance between
             durability, power and control. This effective badminton
             string is powerful and controlled, as well as
             being the most durable in our range.''',
             category_id=5, user_id=2)
session.add(item5)
session.commit()

print "added dummy data!"
