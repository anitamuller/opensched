# OpenSched

Simple and open event scheduler and agenda builder app ~~engine~~ written on [Flask](http://flask.pocoo.org/)

# Under the hood:
- [Python](http://python.org/)
- [Flask](http://flask.pocoo.org/)
- [MongoDB](http://www.mongodb.org/)
- [Bootstrap 3](http://getbootstrap.com/)
- [jQuery](http://jquery.com)
- [Lightbox 2](https://github.com/lokesh/lightbox2)
- [Summernote](http://hackerwins.github.io/summernote/)


# What it can:
- create/preview/update/delete events;
- create/preview/update/delete talks;
- create/update/delete users;
- build your own agenda for an event

# It contains:
- WYSIWYG Summernote editor;
- [AddThis](http://www.addthis.com/) social buttons;
- [Gravatar](http://gravatar.com) for userpic.

# Installation:
`git clone https://github.com/vkmc/opensched.git`

`cd opensched`

`virtualenv --no-site-packages ./env`

`source ./env/bin/activate`

`pip install -r requirements.txt`

After this edit the `config.py` file

- Replace the `CONNECTION_STRING` variable with your own connection string;

- Replace the `DATABASE` variable to your own one;

- If you use this code on a production sever replace the `DEBUG` variable with `False`.

# Run:
When you in project dir with actived environment just type in terminal

`python web.py`

# Usage:
When you run the application for the first time the "Install" page appears. You need to create a user profile and set some display settings on this page.

If you have an account on [Gravatar](http://gravatar.com) and your logged-in email links to it, the userpic will display. It will be a random gravatar image if it doesn't.

All necessary MongoDB indexes will be created during the installation. A test text post will be created as well.

For deploying you can use [Heroku](http://heroku.com) and [mongolab](http://mongolab.com) for example.

# WYSIWYG editor:
WYSIWYG editor uses [Summernote](http://hackerwins.github.io/summernote/).

# Forked from flask project by dmaslov
