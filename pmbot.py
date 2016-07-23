#!/usr/bin/python
import praw
import re
import os
import time
from config_bot import *
from models import *


def get_group(subreddit, keywords):
    groups = Group.select().where(Group.subreddit == subreddit)
    for g in groups:
        if set(k.name for k in g.keywords()) == set(keywords):
            return g
    return None


def create_group(subreddit, keywords):
    group = Group(subreddit=subreddit)
    group.save()
    for name in keywords:
        keyword, created = Keyword.get_or_create(name=name)
        KeywordGroup.create(
            keyword=keyword,
            group=group
        )
    return group


def get_or_create_group(subreddit, keywords):
    group = get_group(subreddit, keywords)
    if group is None:
        group = create_group(subreddit, keywords)
    return group


def get_words(text):
    words = re.sub("[^\w]", " ", text).split()
    words = [x.lower() for x in words]
    return words


def get_intersection(list1, list2):
    return [x for x in list1 if x in list2]


def is_message_send(intersection, username, group_id):
    if Message.select().where(Message.username == username).count():
        if Message.select().where((Message.username == username) & (Message.group == group_id)).count():
            return True
        if Message.select().join(KeywordMessage).join(Keyword).where((Message.username == username) &
                                                                             (Keyword.name << intersection)).count():
            return True
    return False


def save_message(username, group_id, intersection):
    message = Message(username=username, group_id=group_id)
    message.save()
    for name in intersection:
        keyword = Keyword.get(name=name)
        KeywordMessage.create(
            keyword=keyword,
            message=message
        )
    return message.id


def main():
    if not os.path.isfile("config_bot.py"):
        print "You must create a config file config_bot.py with your username and password."
        exit(1)

    keywords = [x.lower() for x in KEYWORDS]

    group = get_or_create_group(SUBREDDIT, keywords)
    print(group.id)

    user_agent = ("PM machine 0.1")
    r = praw.Reddit(user_agent=user_agent)
    r.login(REDDIT_USERNAME, REDDIT_PASS, disable_warning=True)

    subreddit = r.get_subreddit(group.subreddit)

    lastmsg_datetime = None

    for submission in subreddit.get_new(limit=10):
        if lastmsg_datetime is None:
            lastmsg_datetime = submission.created_utc
        if group.lastmsg_datetime and group.lastmsg_datetime >= submission.created_utc:
            print('Eto break')
            break
        intersection = get_intersection(keywords, get_words(submission.title))
        if intersection and not is_message_send(intersection, submission.author.name, group.id):
            print("Bot sending pm to : %s" % submission.author.name)
            if submission.author.name == 'napmany':
                r.send_message(submission.author, TITLE, MESSAGE)
            else:
                print("Bot sending pm to NOT ME!!!! : %s" % submission.author.name)
            save_message(submission.author, group.id, intersection)
            time.sleep(5)

    group.lastmsg_datetime = lastmsg_datetime
    group.save()


if __name__ == '__main__':
    main()
