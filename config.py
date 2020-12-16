import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
    # General
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # File Upload
    IMAGE_UPLOAD_FOLDER = 's3://georgeleeh-blog/static/images/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif', 'gif'}
    # Flask S3 Stuff
    FLASKS3_BUCKET_NAME = os.environ.get('FLASKS3_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    FLASKS3_REGION = os.environ.get('FLASKS3_REGION')

    # This is used by micawber, which will attempt to generate rich media
    # embedded objects with maxwidth=800.
    SITE_WIDTH = 800
    # site map
    SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS=True
