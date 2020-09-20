#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(db.String(500))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    site_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', passive_deletes=True, lazy=True)


class Artist(db.Model):
    __tablename__ = 'Artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    site_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', passive_deletes=True, lazy=True)


class Show(db.Model):
    __tablename__ = 'Shows'
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venues.id', ondelete='CASCADE'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artists.id', ondelete='CASCADE'), nullable=False)
    
   


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
      
    data = []
    
    for location in Venue.query.distinct('city','state').all():
        d = {'city': location.city, 'state': location.state}
        venues =[]
        for venue in Venue.query.filter_by(city=d['city']).filter_by(state=d['state']).all():
            v = {'id': venue.id, 'name': venue.name}
            v['num_upcoming_shows'] = Show.query.filter_by(venue_id=v['id']).filter(Show.datetime >= datetime.now()).count()
            venues.append(v)
        d['venues'] = venues
        
        data.append(d)

    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search = request.form.get('search_term', '')
    response = {}
    
    query = Venue.query.filter(func.lower(Venue.name).contains(func.lower(search)))

    response['count'] = query.count()
    

    response['data']=[]
    for venue in query.all():
        item = {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows' : Show.query.filter_by(venue_id=venue.id).filter(Show.datetime >= datetime.now()).count()
        }
        response['data'].append(item)

    return render_template('pages/search_venues.html', results=response, search_term=search)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    
    query = Venue.query.get(venue_id)
     
    data = {
            'id': query.id,
            'name': query.name,
            'genres': query.genres.split(','),
            'address': query.address,
            'city': query.city,
            'state': query.state,
            'phone': query.phone,
            'website': query.site_link,
            'facebook_link': query.facebook_link,
            'seekiing_talent': query.seeking,
            'seeking_description': query.seeking_description,
            'image_link': query.image_link,
            'past_shows': [],
            'upcoming_shows': [],
            'past_shows_count': 0,
            'upcoming_shows_count': 0
            }
     
    for show in query.shows:
        s = {
                'artist_id': show.artist_id,
                'artist_name': show.artist.name,
                'artist_image_link': show.artist.image_link,
                'start_time': show.datetime.isoformat()
                }
        if show.datetime >= datetime.now():
            data['upcoming_shows'].append(s)
            data['upcoming_shows_count'] += 1
        else:
            data['past_shows'].append(s)
            data['past_shows_count'] += 1

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    success = True
    try:
        f = request.form
        venue = Venue()
        venue.name = f.get('name')
        venue.city = f.get('city')
        venue.state = f.get('state')
        venue.address = f.get('address')
        venue.phone = f.get('phone')
        venue.genres = ','.join(f.getlist('genres')) 
        
        venue.facebook_link = f.get('facebook_link')
        db.session.add(venue)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occured. Venue ' + request.form['name']  + ' could not be listed!')
        success = False
    finally:
        db.session.close()

    if success: flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
        
@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
    q = Venue.query.filter_by(id=venue_id)
    name = q.first().name
    success = True
    try:
        q.delete()
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occured. Venue ' + Venue.query.get(venue_id).name  + ' could not be deleted!')
        success = False
    finally:
        db.session.close()
    if success: flash('Venue ' + name + ' was successfully deleted!')
    return redirect(url_for('index'))
    


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
   
    data=[]
    for artist in Artist.query.all():
        data.append({"id": artist.id, "name": artist.name})

    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search = request.form.get('search_term', '')
    response = {}
    
    query = Artist.query.filter(func.lower(Artist.name).contains(func.lower(search)))

    response['count'] = query.count()
    

    response['data']=[]
    for artist in query.all():
        item = {
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows' : Show.query.filter(Show.artist_id == artist.id).filter(Show.datetime >= datetime.now()).count()
        }
        response['data'].append(item)

    return render_template('pages/search_artists.html', results=response, search_term=search)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    
    artist = Artist.query.get(artist_id)


    data={
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres.split(','),
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.site_link,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "upcoming_shows": [],
            "past_shows": [],
            "upcoming_shows_count": 0,
            "past_shows_count": 0
            }
    for show in artist.shows:
        s = {
                'venue_id': show.venue_id,
                'venue_name': show.venue.name,
                'venue_image_link': show.venue.image_link,
                'start_time': show.datetime.isoformat()
                }
        if show.datetime >= datetime.now():
            data['upcoming_shows'].append(s)
            data['upcoming_shows_count'] += 1
        else:
            data['past_shows'].append(s)
            data['past_shows_count'] += 1

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    a = Artist.query.get(artist_id)
    form = ArtistForm() 
    
    artist={
            "id": a.id,
            "name": a.name,
            "genres": a.genres.split(','),
            "city": a.city,
            "state": a.state,
            "phone": a.phone,
            "website": a.site_link,
            "facebook_link": a.facebook_link,
            "seeking_venue": a.seeking,
            "seeking_description": a.seeking_description,
            "image_link": a.image_link
            }

    form.name.data = artist['name'] 
    form.city.data = artist['city']
    form.state.data = artist['state']
    form.phone.data = artist['phone']
    form.genres.data = artist['genres']
    form.facebook_link.data = artist['facebook_link']
    
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id): 
    data = request.form

    success = True
    try:
        f = request.form
        artist = Artist.query.get(artist_id)
        artist.name = f.get('name')
        artist.city = f.get('city')
        artist.state = f.get('state')
        artist.phone = f.get('phone')
        artist.genres = ','.join(f.getlist('genres')) 
        artist.facebook_link = f.get('facebook_link')
        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occured. Artist ' + request.form['name']  + ' could not be updated!')
        success = False
    finally:
        db.session.close()

    if success: flash('Artist ' + request.form['name'] + ' was successfully updated!')
    
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    v = Venue.query.get(venue_id)
    form = VenueForm() 

    venue={
            "id": v.id,
            "name": v.name,
            "genres": v.genres.split(','),
            "city": v.city,
            "state": v.state,
            "address": v.address,
            "phone": v.phone,
            "website": v.site_link,
            "facebook_link": v.facebook_link,
            "seeking_venue": v.seeking,
            "seeking_description": v.seeking_description,
            "image_link": v.image_link
            }

    form.name.data = venue['name'] 
    form.city.data = venue['city']
    form.address.data = venue['address']
    form.state.data = venue['state']
    form.phone.data = venue['phone']
    form.genres.data = venue['genres']
    form.facebook_link.data = venue['facebook_link']

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    data = request.form

    success = True
    try:
        f = request.form
        venue = Venue.query.get(venue_id)
        venue.name = f.get('name')
        venue.city = f.get('city')
        venue.state = f.get('state')
        venue.address = f.get('address')
        venue.phone = f.get('phone')
        venue.genres = ','.join(f.getlist('genres')) 
        venue.facebook_link = f.get('facebook_link')
        db.session.add(venue)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occured. Venue ' + request.form['name']  + ' could not be updated!')
        success = False
    finally:
        db.session.close()

    if success: flash('Venue ' + request.form['name'] + ' was successfully updated!')
    
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    success = True
    try:
        f = request.form
        artist = Artist()
        artist.name = f.get('name')
        artist.city = f.get('city')
        artist.state = f.get('state')
        artist.address = f.get('address')
        artist.phone = f.get('phone')
        artist.genres = ','.join(f.getlist('genres'))
        artist.facebook_link = f.get('facebook_link')
        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occured. Artist ' + request.form['name']  + ' could not be listed!')
        success = False
    finally:
        db.session.close()

    if success: flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data=[]
    shows = Show.query.filter(Show.datetime >= datetime.now()).all()
    for show in shows:
        s = {
                "venue_id" : show.venue.id,
                "venue_name" : show.venue.name,
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.datetime.isoformat()
                }
        data.append(s)
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    
    success = True
    try:
        f = request.form
        show = Show()
        show.artist_id = f.get('artist_id')
        show.venue_id = f.get('venue_id')
        show.datetime = f.get('start_time')
        db.session.add(show)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occured. Show could not be listed!')
        success = False
    finally:
        db.session.close()

    if success: flash('Show was successfully listed!')

    return render_template('pages/home.html')

    
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
