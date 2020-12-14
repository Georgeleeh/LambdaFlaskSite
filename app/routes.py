from app import app, db

from flask import render_template

from botocore.exceptions import ClientError



def get_blog_post(timestamp, dynamodb=db):
    try:
        response = dynamodb.get_item(TableName='georgeleeh_blog_posts', Key={'timestamp': {'N': str(timestamp)}})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']



@app.route('/')
@app.route('/index')
def hello_world():
    response = get_blog_post(1234)
    print(response)
    user = {'username': 'Miguel'}
    return render_template('index.html', title='Home', user=user)