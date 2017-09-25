from flask import Flask, Blueprint
from werkzeug.contrib.fixers import ProxyFix
from flask_restplus import Api, Resource, abort, apidoc, reqparse
from cloudmanager import manager
from cloudmanager.exceptions import (CloudManagerException,
                                     MasterCountChangeError)


parser = reqparse.RequestParser()
parser.add_argument('key', type=str, help='Unique key, if not set this'
                    ' request will be traded as first request and key is'
                    ' generated by server. Whether key is provided it is'
                    ' promised to be returned for lately use',
                    location=('form', 'args'))
parser.add_argument(
    'master_count', type=int, help='If create a master vps as a swarm manager'
    ' otherwise use current as manager, only 0 and 1 is allowed', default=0,
    location=('form', 'args'))
parser.add_argument(
    'servant_count', type=int, help='How many servant vps should be created',
    default=0, location=('form', 'args'))

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


class CloudScaleAPI(Resource):
    @api.doc(parser=parser)
    @api.response(200, 'Success with key and master server ip returned')
    def post(self):
        args = parser.parse_args()
        key = args['key']
        master_count = 1 if args['master_count'] else 0
        servant_count = args['servant_count']
        if not key:
            key = manager.new_key()
        try:
            master_ip = manager.scale_cloud(key, master_count, servant_count)
        except MasterCountChangeError:
            # master server count is different and not accepted
            abort(message="Master server count required is different from"
                  " exist request and not accepted")
        except CloudManagerException:
            # request scheduled but failed this time
            abort(message="Request is scheduled but failed this time, "
                  "will retry later", key=key)
        except Exception:
            # unknown error
            abort()
        return {"message": "success", "key": key, "master_ip": master_ip}


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
    # TODO start background asyncio event loop
    app.run(host='0.0.0.0')
    # TODO tear down background thread
