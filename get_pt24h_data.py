from flask import Flask, request
#from flask_cors import CORS, cross_origin
import datetime
import requests

app = Flask(__name__)
#CORS(app, support_credentials=True)


@app.route('/')
def hello():
  return "Hello"


@app.route('/get_graph_data', methods=['GET'])
#@cross_origin(supports_credentials=True)
def get_data():

    print('something works')
    # assign current date in ISO format
    today = datetime.datetime.now().replace(microsecond=0).isoformat()

    # get postcode
    postcode = request.args.get('postcode')

    if not postcode:
      return "Missing postcode."

    # get data
    r = requests.get('https://api.carbonintensity.org.uk/regional/intensity/'+today+'/pt24h/postcode/'+str(postcode),
                     params={}, headers = { 'Accept': 'application/json' })

    # array of 48 emission intensities data points in gCO2eq/kWh in chronological order
    emission_intensities = [r.json()['data']['data'][i]['intensity']['forecast'] for i in range(len(r.json()['data']['data']))]

    dict_object = {'data': emission_intensities}

    return str(dict_object)
if __name__ == '__main__':
    app.run()
