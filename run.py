from flask import Flask, Blueprint
from werkzeug.contrib.fixers import ProxyFix
from flask_restplus import Api, Resource, abort, apidoc
from cloudmanager import cloud_manager


class CloudManagerAPI(Resource):
    def get(self, host):
        if host in ['vultr', 'digitalocean']:
            data = cloud_manager.list_machine()
            return {"message": data}
        else:
            abort(404)


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
api.add_resource(CloudManagerAPI, '/<host>/', endpoint='')
app.register_blueprint(blueprint)


@app.after_request
def after_request(response):
    """
    Handle CORS Requests
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


if __name__ == '__main__':
    app.run()
