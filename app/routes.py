from app import app, db

from flask import render_template

from botocore.exceptions import ClientError



def get_blog_post(timestamp, dynamodb=db):
    try:
        response = dynamodb.get_item(Key={'timestamp': timestamp})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        r = response['Item']
        return response['Item']



@app.route('/')
def home():
    response = get_blog_post(1234)
    print(response['timestamp'])
    return render_template('home.html')