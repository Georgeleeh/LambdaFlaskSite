from app import app, db_posts, db_tags

from flask import render_template

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
        'timestamp' : timestamp,
        'title' : title,
        'content' : content,
        'tags' : tag_set
    }

    response = db_posts.put_item(Item=item)
    response_code = response['ResponseMetadata']['HTTPStatusCode']

    if response_code == 200:
        for tag in tag_set:
            db_tags.update_item(
                Key={'tag' : tag},
                UpdateExpression=f'ADD posts :p',
                ExpressionAttributeValues={':p' : set([timestamp])}
                )
    else:
        raise Exception(f'Failed to create post: {response}')

    return response



@app.route('/')
def home():
    response = put_blog_post(4321, 'Second Post', "He's back, putting posts again", 'test, put')
    print(response)
    return render_template('home.html')