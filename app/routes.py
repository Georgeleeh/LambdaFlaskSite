from app import app, db_posts, db_tags
import boto3
from datetime import datetime
from flask import render_template, url_for, request, session, flash, redirect

from botocore.exceptions import ClientError


def get_blog_post(timestamp):
    try:
        response = db_posts.get_item(Key={'timestamp': timestamp})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']


def put_blog_post(timestamp, title, content, tags):
    tag_set = set([t.strip() for t in tags.split(',')])
    print(tag_set)
    item = {
        'timestamp': timestamp,
        'title': title,
        'content': content,
        'tags': tag_set
    }

    response = db_posts.put_item(Item=item)
    response_code = response['ResponseMetadata']['HTTPStatusCode']

    if response_code == 200:
        for tag in tag_set:
            db_tags.update_item(
                Key={'tag': tag},
                UpdateExpression=f'ADD posts :p',
                ExpressionAttributeValues={':p': set([timestamp])}
            )
    else:
        raise Exception(f'Failed to create post: {response}')

@app.template_filter('stampdate')
def stampdate(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y at %H:%M')

@app.route('/blog/')
def blog():
    # get all blog posts
    # check if user is logged in
    # if logged in, show all posts
    # else, only show published posts

    posts = []

    if session.get('logged_in'):
        r = db_posts.scan(FilterExpression='published = :b', ExpressionAttributeValues = {":b":True } )
        posts = r['Items']
    else:
        r = db_posts.scan()
        posts = r['Items']

    return render_template('blog.html', entry_list=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or request.form.get('next')
    if request.method == 'POST' and request.form.get('password'):
        password = request.form.get('password')
        # TODO: If using a one-way hash, you would also hash the user-submitted
        # password and do the comparison on the hashed versions.
        if password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session.permanent = True  # Use cookie to store session.
            flash('You are now logged in.', 'success')
            return redirect(next_url or url_for('home'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('login.html', next_url=next_url)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))
    return render_template('logout.html')

@app.route('/')
def home():
    r = db_posts.scan(FilterExpression='published = :b AND featured = :b', ExpressionAttributeValues = {":b":True } )
    posts = r['Items']

    return render_template('home.html', featured=posts, len=len(posts))
