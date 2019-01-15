import datetime

from peewee import *
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash 

# For home: 
DATABASE = MySQLDatabase(host='127.0.0.1', port=3303, database='social.db',
                         user='root', password='root')
# For work:
# DATABASE = MySQLDatabase(host='127.0.0.1', database='social.db',
#                         user='root', password='')

class User(UserMixin, Model):
    # Because we have not specified a primary key, 
    # peewee will automatically add
    # an auto-incrementing integer primary key field named *id*.
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)

    class Meta:
        database = DATABASE
        # order_by can take one or more fields to order records by by default.
        # we have to include the trailing comma
        # even if there's only one tuple member.
        order_by = ('-joined_at',)


    def get_posts(self):
        return Post.select().where(Post.user == self)
    
    def get_stream(self):
        return Post.select().where(
            (Post.user << self.following()) |
            (Post.user == self)
        )

    def following(self):
        """The users that we are following."""
        return (
            User.select().join(
                    Relationship, on=Relationship.to_user
               ).where(
                    Relationship.from_user == self
            )
        )
        

    def followers(self):
        """Get users following the current user."""
        return (
            User.select().join(
                Relationship, on=Relationship.from_user
            ).where(
                Relationship.to_user == self
            )
        )

    @classmethod
    def create_user(cls, username, email, password, admin=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin = admin
                )
        except IntegrityError:
            raise ValueError("User already exists")

class Post(Model):
    # For timestamp: note we only provide the function,
    # we do not actually call it.
    timestamp = DateTimeField(default=datetime.datetime.now)
    user=ForeignKeyField(
        User,
        # we can assign multiple posts to one user
        # so on the user end we have a "hidden" posts column
        backref='posts'
    )
    content = TextField()

    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)

class Relationship(Model):
    # Who are the people related to me?
    from_user = ForeignKeyField(User, backref="relationships")
    # Who are the people I'm related to?
    to_user = ForeignKeyField(User, backref="related_to")

    class Meta:
        database = DATABASE
        # Tell the DB how to find the data.
        # The "True" makes it so that you can't follow the same user twice
        indexes = (
            (('from_user', 'to_user'), True),
        )

def initialize():
    DATABASE.connect()
    # Set `safe` as True so we can bypass if the table exists.
    # If it does, we do not over-write it.
    DATABASE.create_tables([User, Post, Relationship], safe=True)
    DATABASE.close()
