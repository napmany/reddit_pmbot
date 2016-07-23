from peewee import *

db = SqliteDatabase('reddit_pmbot.db')


class Group(Model):
    subreddit = CharField()
    lastmsg_datetime = IntegerField(null=True)

    class Meta:
        database = db

    def keywords(self):
        return Keyword.select().join(KeywordGroup).join(Group).where(Group.id == self.id)


class Keyword(Model):
    name = CharField(unique=True)

    class Meta:
        database = db


class Message(Model):
    username = CharField()
    group = ForeignKeyField(Group, related_name='messages')

    class Meta:
        database = db


class KeywordGroup(Model):
    keyword = ForeignKeyField(Keyword)
    group = ForeignKeyField(Group)

    class Meta:
        database = db
        indexes = (
            (('keyword', 'group'), True),
        )


class KeywordMessage(Model):
    keyword = ForeignKeyField(Keyword)
    message = ForeignKeyField(Message)

    class Meta:
        database = db
        indexes = (
            (('keyword', 'message'), True),
        )


def create_tables():
    db.connect()
    db.create_tables([Group, Keyword, Message, KeywordGroup, KeywordMessage])


if __name__ == '__main__':
    create_tables()
