# we can also use it like normal db connector however we don't use it cause ORM
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import Session
# engine = create_engine('sqlite:///mydb.db',echo=True)
# conn = engine.connect()
# conn.execute(text('''CREATE TABLE IF NOT EXISTS posts (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     title TEXT NOT NULL,
#     content TEXT NOT NULL,
#     published BOOLEAN NOT NULL DEFAULT 1
# )'''))
# conn.commit()
# session = Session(engine)
# session.execute(text('''INSERT INTO posts (title, content, published) VALUES ('First Post', 'This is the content of the first post', 1)'''))
# session.commit()

from sqlalchemy import create_engine, Column, Integer, String, Boolean, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker

# engine = create_engine('sqlite:///./mydb.db', echo=True)
engine = create_engine(
    "mysql+pymysql://root:vanshtank@localhost:3306/FastAPI",
    echo=True
)
# metadata = MetaData()

# posts = Table(
#   'posts',
#   metadata,
#   Column('id', Integer, primary_key=True, autoincrement=True),
#   Column('title', String, nullable=False),
#   Column('content', String, nullable=False),
#   Column('published', Boolean, nullable=False, default=True)
# )
# metadata.create_all(engine)

# con = engine.connect()
# insert_statement = posts.insert().values(title='First Post', content='This is the content of the first post', published=True)
# con.execute(insert_statement)
# con.commit()

# update_statement = posts.update().where(posts.c.id == 1).values(title='Updated First Post')
# con.execute(update_statement)
# con.commit()

# insert_statement = posts.insert().values([
#   {'title': 'Second Post', 'content': 'This is the content of the second post', 'published': True},
#   {'title': 'Third Post', 'content': 'This is the content of the third post', 'published': False}
# ])
# con.execute(insert_statement)
# con.commit()

# select_statement = posts.select()
# result = con.execute(select_statement)

# for row in result.fetchall():
#   print(row)

base = declarative_base()
class Post(base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, nullable=False, default=True)

base.metadata.create_all(engine)

new_post = Post(title='First Post from ORM', content='This is the content of the first post', published=True)
# session.flush() # to get the id of the new post before commit
# use filter instead or were for this instance
# update takes dictionary 
Session = sessionmaker(bind=engine)
session = Session()
session.add(new_post)
session.commit()