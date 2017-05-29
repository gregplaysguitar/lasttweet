#!/usr/bin/env python

import re

import tweepy
from flask import Flask, jsonify, abort, request
from flask_cache import Cache


app = Flask(__name__)

app.config.from_object('config')


cache = Cache(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache'})


auth = tweepy.OAuthHandler(app.config['CONSUMER_KEY'],
                           app.config['CONSUMER_SECRET'])
auth.set_access_token(app.config['ACCESS_TOKEN'],
                      app.config['ACCESS_TOKEN_SECRET'])
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())


@app.route('/')
def index():
    url = '%s://%s/timkelleher' % (request.scheme, request.host)
    return "<h1>Last tweet</h1>" \
           "<p>Fetch a user's last tweet in json format. Example:<br><br> " \
           "<a href='%s'>%s</a></p>" % (url, url)


@cache.cached(timeout=60 * 15)
def get_timeline(username):
    """Return user's timeline as dict, or None if user not found. """

    try:
        return api.user_timeline(username, count=20)
    except tweepy.error.TweepError as e:
        if e.api_code == 34:
            return None
        if e.reason == 'Not authorized.':
            # not sure why this has no code
            return None
        raise


@app.route('/<username>')
def fetch(username):
    if not re.search('^[\w\d_]+$', username):
        abort(404)

    statuses = get_timeline(username)

    # user not found
    if statuses is None:
        abort(404)

    # return first status, excluding retweets and replies
    for status in statuses:
        if not status['retweeted'] and not status['in_reply_to_status_id']:
            return jsonify(status)

    # no valid statuses found
    abort(404)


if __name__ == "__main__":
    app.run()
