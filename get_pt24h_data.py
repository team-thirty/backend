from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import datetime
import requests

app = Flask(__name__)
CORS(app, support_credentials=True)


@app.route('/')
def hello():
  return "Hello"

# if this is True, user sets a threshold on CO2 emission level manually
# if False, the times of charging
manual = False

# threshold of environmentally friendly CO2 emission levels to use as a limit for charging devices
threshold = 100

# what time the device needs to be fully charged
time = 2

# how much time is available for changing the device
window = 5


@app.route('/get_graph_data', methods=['GET'])
@cross_origin(supports_credentials=True)
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

    dict_object = {"data": emission_intensities}

    return jsonify(dict_object)

@app.route('/set_params', methods=['POST'])

def set_params():

        manual = request.form.get('manual')
        try:
                bool_manual = bool(manual)
        except ValueError:
                return('Input manual is not boolean.')

        threshold = request.form.get('threshold')

        try:
                int_threshold = int(threshold)
        except ValueError:
                return('Input threshold is not integer.')

        time = request.form.get('time')
        try:
                int_time = int(time)
        except ValueError:
                return('Input time is not integer.')

        window = request.form.get('window')
        try:
                int_window = int(window)
        except ValueError:
                return('Input window is not integer.')


@app.route('/get_charging_state', methods=['GET'])

def get_charging_status():
        return jsonify({'state': 0})

if __name__ == '__main__':
    app.run()
