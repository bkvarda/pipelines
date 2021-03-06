from flask import Flask, request, abort
from flask_cors import CORS
import json
import os

from kfservingdeployer import deploy_model

app = Flask(__name__)
CORS(app)


@app.route('/deploy-model', methods=['POST'])
def deploy_model_post():
    if not request.json:
        abort(400)
    return json.dumps(deploy_model(
                action=request.json['action'],
                model_name=request.json['model_name'],
                default_model_uri=request.json['default_model_uri'],
                canary_model_uri=request.json['canary_model_uri'],
                canary_model_traffic=request.json['canary_model_traffic'],
                namespace=request.json['namespace'],
                framework=request.json['framework'],
                default_custom_model_spec=request.json['default_custom_model_spec'],
                canary_custom_model_spec=request.json['canary_custom_model_spec'],
                autoscaling_target=request.json['autoscaling_target']
                ))


@app.route('/', methods=['GET'])
def root_get():
    return 200


@app.route('/', methods=['OPTIONS'])
def root_options():
    return "200"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
