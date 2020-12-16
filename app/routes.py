from app import app, db_posts, db_tags, s3
import boto3
import os, re
import functools
from datetime import datetime
from flask import render_template, url_for, request, session, flash, redirect
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError

def login_required(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner

def get_blog_post(timestamp):
    try:
        response = db_posts.get_item(Key={'timestamp': timestamp})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

@app.template_filter('stampdate')
def stampdate(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y at %H:%M')

@app.route('/')
def home():
    r = db_posts.scan(FilterExpression='published = :b AND featured = :b', ExpressionAttributeValues = {":b":True } )
    posts = r['Items']

    if len(posts) > 3:
        posts = posts[:2]

    return render_template('home.html', featured=posts, len=len(posts))

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

@app.route('/blog/')
def blog():
    # TODO implement search
    # TODO check if posts are sorted?
    r = db_posts.scan(FilterExpression='published = :b', ExpressionAttributeValues = {":b":True } )
    posts = r['Items']

    return render_template('blog.html', post_list=posts)

def put_blog_post(post):
    # TODO add HTML content as well as content
    # check old models.py for this
    response = db_posts.put_item(Item=post)
    response_code = response['ResponseMetadata']['HTTPStatusCode']

    if response_code == 200:
        for tag in post['tags']:
            db_tags.update_item(
                Key={'tag': tag},
                UpdateExpression=f'ADD posts :p',
                ExpressionAttributeValues={':p': set([post['timestamp']])}
            )
    else:
        raise Exception(f'Failed to create post: {response}')

def _create_or_edit(post, template):
    if request.method == 'POST':
        button_value = request.form.get('button')
        if button_value == 'save':
            post['title'] = request.form.get('title') or ''
            post['one_liner'] = request.form.get('one_liner') or ''
            post['featured_image'] = request.form.get('featured_image') or ''
            post['content'] = request.form.get('content') or ''
            post['published'] = True if request.form.get('published') == 'y' else False
            post['featured'] = True if request.form.get('featured') == 'y' else False
            post['slug'] = re.sub(r'[^\w]+', '-', post['title'].lower()).strip('-')
            post['tags'] = set([t.strip().title() for t in request.form.get('tags').split(',')])

            if request.form.get('posted') != "":
                try:
                    post['timestamp'] = int(datetime.strptime(request.form.get('posted'), '%d/%m/%Y at %H:%M').timestamp())
                except:
                    flash('Poorly Formatted time. Should be %d/%m/%Y at %H:%M or blank', 'danger')
            else:
                post['timestamp'] = int(datetime.now().timestamp())

            if not (post['title'] and post['content']):
                flash('Title and Content are required.', 'danger')
            else:

                put_blog_post(post)

                flash('Post saved successfully.', 'success')

                if post['published']:
                    return redirect(url_for('detail', slug=post['slug']))
                else:
                    return redirect(url_for('edit', slug=post['slug']))

        elif button_value == 'delete':
            # TODO delete post, remove post from associated entries for tags and check for loner tags
            flash('Post deleted.', 'danger')
            return redirect(url_for('home'))

    return render_template(template, post=post, images=get_upload_images())

@app.route('/create/', methods=['GET', 'POST'])
@login_required
def create():
    return _create_or_edit({}, 'create.html')

@app.route('/blog/<slug>/')
def detail(slug):
    r = db_posts.scan(FilterExpression='published = :b AND slug = :s', ExpressionAttributeValues = {":b":True, ":s" : slug} )

    if len(r) > 0:
        post = r['Items'][0]

        return render_template('detail.html', post=post)
    else:
        flash('Post not found.', 'danger')
        return redirect(url_for('home'))


@app.route('/blog/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit(slug):
    r = db_posts.scan(FilterExpression='slug = :s', ExpressionAttributeValues = {":s" : slug} )
    post = r['Items'][0]
    return _create_or_edit(post, 'edit.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_tag_posts(tag_name):
    tag_name = tag_name.title()

    try:
        response = db_tags.get_item(Key={'tag': tag_name})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        try:
            tag = response['Item']
        except KeyError:
            flash(f'No posts found tagged with {tag_name}', 'danger')
            return redirect(url_for('home'))
    
    return tag['posts']

@app.route('/blog/tags/<tag>')
def tags(tag):
    timestamps = get_tag_posts(tag)
    posts = [get_blog_post(t) for t in timestamps if get_blog_post(t)['published'] is True]
        
    return render_template('blog.html', post_list=posts)

@app.route('/drafts/')
@login_required
def drafts():
    r = db_posts.scan(FilterExpression='published = :b', ExpressionAttributeValues = {":b":False } )
    posts = r['Items']

    return render_template('blog.html', post_list=posts)

@app.route('/image-gallery/')
@login_required
def image_gallery():
    # TODO
    images = get_upload_images()
    return render_template('image_gallery.html', images=images)


@app.route('/upload-image/', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file,', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # check if file exists
            if file.filename in [filepath.split('/')[-1] for filepath in get_upload_images()]:
                flash('Filename exists,', 'danger')
                return redirect(request.url)
            else:
                filename = secure_filename(file.filename)

                filepath = os.path.join('/tmp', filename)
                file.save(filepath)
                s3.put_object(ACL='public-read', Body=open(filepath, 'rb') , Bucket='georgeleeh-blog', Key='static/images/uploads/'+filename )

                flash('Image uploaded successfully.', 'success')
                return redirect(url_for('home'))
    return render_template('upload_image.html')

def get_upload_images():
    r = s3.list_objects(Bucket='georgeleeh-blog', Prefix='static/images/uploads')['Contents']

    prefix = 'https://georgeleeh-blog.s3.eu-west-2.amazonaws.com/'
    return [prefix + c['Key'] for c in r]