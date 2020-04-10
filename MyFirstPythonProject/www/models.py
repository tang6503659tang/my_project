import time,uuid
from orm import Model,StringField,BooleanField,FloatField,TextField

def next_id():
    return "%015d%s000" % (int(time.time),uuid.uuid4().hex)

class User(Model): #User for creating new users
    __table__='users'
    # set necessary information for users
    id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
    email= StringField(ddl="varchar(50)")
    passwd = StringField(ddl="varchar(50)")
    admin=BooleanField()
    name=StringField(ddl="varchar(50)")
    image=StringField(ddl='varchar(500)')
    created_at=FloatField(default=time.time)

class Blog(Model): # Blog for creating new blogs
    __table__="blogs"
    # set necessary information for blogs
    id=StringField(primary_key=True,default=next_id,ddl='varchar(50)')
    user_id=StringField(ddl='varchar(50)')
    user_name=StringField(ddl='varchar(50)')
    user_image=StringField(ddl='varchar(50)')
    name=StringField(ddl='varchar(50)')
    summary=StringField(ddl='varchar(200)')
    content=TextField()
    created_at=FloatField(default=time.time)

class Comment(Model): # Comment for creating new comment
    __table__="comments"
    # set necessary information for comments
    id=StringField(primary_key=True,default=next_id,ddl='varchar(50)')
    blog_id=StringField(ddl="varchar(50)")
    user_id=StringField(ddl='varchar(50)')
    user_name=StringField(ddl='varchar(50)')
    content=TextField()
    created_at=FloatField(default=time.time)

