# Concurrency happens at the cross-instance/load-balancer level :/

from flask import Flask, jsonify, request
import os
import math
import psycopg2
import re
import config

app = Flask(__name__)

# Regex space escaper
space_re = re.compile(r"(\w)\s(\w)")

# Connect to database
ira_conn = psycopg2.connect(dbname=os.environ.get("PG_DBNAME"), user=os.environ.get(
    "PG_USERNAME"), password=os.environ.get("PG_PASSWORD"), host=os.environ.get("PG_HOST"))

cached_total = None


def __search(query, page=1):
    processed_query = space_re.sub(r"\1 <-> \2", query)
    cursor = ira_conn.cursor()
    offset = (page - 1) * 100
    cursor.execute("SELECT count(*) FROM search_index WHERE document @@ to_tsquery(%s);", (processed_query,))
    total = cursor.fetchone()[0]
    cursor.execute("SELECT tweetid, tweet_text, user_screen_name, user_reported_location, follower_count, tweet_language, like_count, retweet_count FROM search_index WHERE document @@ to_tsquery(%s) limit 100 offset %s;", (processed_query, offset))
    values = cursor.fetchall()
    results = [
        {
            "id": value[0],
            "text": value[1],
            "screen_name": value[2],
            "location": value[3],
            "followers": int(value[4]),
            "language": value[5],
            "likes": int(value[6]),
            "retweets": int(value[7])
        } for value in values
    ]
    return {
        "total": total,
        "results": results,
        "pages": math.ceil(total / 100.0),
        "page": page
    }

def __total_ira():
    global cached_total
    if cached_total == None:
        cursor = ira_conn.cursor()
        cursor.execute("SELECT count(*) FROM tweets;")
        cached_total = cursor.fetchone()[0]
    return cached_total


@app.route('/v1/info', methods=['GET'])
def info():
    return jsonify({
        "total_items": __total_ira()
    })


@app.route('/v1/search', methods=['GET'])
def search():
    query = request.args.get("query")
    page = int(request.args.get("page", 1))
    return jsonify(__search(query, page))


if __name__ == '__main__':
    app.run()