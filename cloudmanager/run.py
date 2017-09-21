from flask import Flask, Blueprint, request
from werkzeug.contrib.fixers import ProxyFix
from flask_restplus import Api, Resource, abort, apidoc
from cloudmanager import cloud_manager


class CloudScaleAPI(Resource):
    def post(self):
        key = request.form['key']
        master_count = request.form['master_count']
        servant_count = request.form['servant_count']
        return {"key": key, "master_count": master_count, "servant_count": servant_count}
        try:
            data = cloud_manager.scale_cloud(key, master_count, servant_count)
        except:
            abort()
        return {"message": "success", "data": data}


url_prefix = ''
# Blueprint is needed to avoid swagger ui static assets 404 error
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
# register swagger ui static assets to avoid 404 error when use nginx
# as reverse proxy server with sub path
app.register_blueprint(apidoc.apidoc, url_prefix=url_prefix)
# blueprint for cloud manager rest api
blueprint = Blueprint('', __name__, url_prefix=url_prefix)
api = Api(blueprint, version='1.0', title='Cloud manager api',
          description='API for cloud manager', doc='/doc/')
api.add_resource(CloudScaleAPI, '/scale', endpoint='')
app.register_blueprint(blueprint)


@app.after_request
def after_request(response):
    """
    Handle CORS Requests
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')
