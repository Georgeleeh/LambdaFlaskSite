from flask import Flask
from config import Config

import boto3
from flask_s3 import FlaskS3


app = Flask(__name__)
app.config.from_object(Config)

s3 = FlaskS3(app)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
db_posts = dynamodb.Table('georgeleeh_blog_posts')
db_tags = dynamodb.Table('georgeleeh_blog_tags')

s3 = boto3.client('s3')

from app import routes