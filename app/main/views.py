from flask import render_template

from . import main


@main.route('/')
def index():
    import urllib2
    from json import loads
    result = urllib2.urlopen('http://api.giphy.com/v1/gifs/random?api_key=dc6zaTOxFJmzC&tag=cat').read()
    json_data = loads(result)
    gif_url = json_data['data']['image_original_url']
    return render_template('index.html', gif_url=gif_url)
