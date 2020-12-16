from flask import Flask
from config import Config

import boto3
from flask_s3 import FlaskS3

from micawber import bootstrap_basic
from micawber.cache import Cache as OEmbedCache

from flask_sitemap import Sitemap


app = Flask(__name__)
app.config.from_object(Config)

s3 = FlaskS3(app)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
db_posts = dynamodb.Table('georgeleeh_blog_posts')
db_tags = dynamodb.Table('georgeleeh_blog_tags')

s3 = boto3.client('s3')

# Configure micawber with the default OEmbed providers (YouTube, Flickr, etc).
# We'll use a simple in-memory cache so that multiple requests for the same
# video don't require multiple network requests.
oembed_providers = bootstrap_basic(OEmbedCache())

ext = Sitemap(app=app)

from app import routes