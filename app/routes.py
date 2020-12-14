from app import app, db

from flask import Flask

from botocore.exceptions import ClientError



def get_blog_post(timestamp, dynamodb=db):
    try:
        response = dynamodb.get_item(TableName='georgeleeh_blog_posts', Key={'timestamp': {'N': str(timestamp)}})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']



@app.route('/')
def hello_world():
    response = get_blog_post(1234)
    print(response)
    return '<h1>Yeah, that is Zappa! Zappa! Zap! Zap!</h1>'