from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

import json
from datetime import datetime, date, timedelta
import requests

current_time =  datetime.now()
print(current_time)

# if this is True, user sets a threshold on CO2 emission level manually
# if False, the times of charging
manual = False

# threshold of environmentally friendly CO2 emission levels to use as a limit for charging devices
threshold = 100

# what time the device needs to be fully charged
time = 2
intervals_to_charge = time*2 


# how much time is available for changing the device
window = 5
intervals_available = window*2

postcode = "CB2"

current_state = 0
charging_list = None
applied_time = None
intensity_forecast = []

app = Flask(__name__)
CORS(app, support_credentials=True)


# app.config.from_object("config.Config")

@app.route('/')
def hello():
  return "Hello"


@app.route('/get_graph_data', methods=['GET'])
#@cross_origin(supports_credentials=True)
def get_data():

    print('something works')
    # assign current date in ISO format
    today = datetime.now().replace(microsecond=0).isoformat()

    # get postcode
    postcode = request.args.get('postcode')

    if not postcode:
      return "Missing postcode."

    # get data
    past_24_data = requests.get('https://api.carbonintensity.org.uk/regional/intensity/'+today+'/pt24h/postcode/'+str(postcode),
                     params={}, headers = { 'Accept': 'application/json' })
    future_24_data = requests.get('https://api.carbonintensity.org.uk/regional/intensity/'+today+'/fw24h/postcode/'+str(postcode), 
                     params={}, headers = { 'Accept': 'application/json' })

    
    # array of 48 emission intensities data points in gCO2eq/kWh in chronological order
    emission_intensities_past24 = [past_24_data.json()['data']['data'][i]['intensity']['forecast'] for i in range(len(past_24_data.json()['data']['data']))]
    emission_intensities_future24 = [future_24_data.json()['data']['data'][i]['intensity']['forecast'] for i in range(len(future_24_data.json()['data']['data']))]

    dict_object = {"past_data": emission_intensities_past24,
                   "future_data": emission_intensities_future24}

    return jsonify(dict_object)

@app.route('/set_params', methods=['POST'])

def set_params():
    global current_time
    global manual
    global threshold
    global time
    global window  
    if request.form.get('manual') == None:
        return 'No data :('

    manual = request.form.get('manual')
    try:
        bool_manual = bool(manual)
    except ValueError:
        return('Input manual is not boolean.')

    str_threshold = request.form.get('threshold')
    print(threshold)
    print(request.form)

    try:
        threshold = int(str_threshold)
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

    global charging_list
    global applied_time
    applied_time = datetime.now()   
    charging_list = get_charging_list()

    smart_sum = sum(intensity for t, intensity in charging_list)
    if manual:
        dumb_sum = sum(intensity for t, intensity in intensity_forecast[:len(charging_list)])
    else:
        dumb_sum = sum(intensity for t, intensity in intensity_forecast[:int_time])
    return jsonify({'smart_sum': smart_sum, 'dumb_sum': dumb_sum})

"""
returns list of tuples below the threshold [('time_str', 200), ('time_str', 200)]
"""
@app.route('/get_charging_list', methods=['GET'])
def get_charging_list (read_time = current_time):
    global current_time
    global manual
    global threshold
    global time
    global window    
    
    intervals_to_charge = time*2
    intervals_available = window*2

    if(intervals_available<intervals_to_charge):
        return("Not enough to fully charge")
    headers = {
        'Accept': 'application/json'
    }

    r = requests.get('https://api.carbonintensity.org.uk/regional/intensity/%sT%sZ/fw24h/postcode/%s'%(read_time.strftime("%Y-%m-%d"),read_time.strftime("%H:%M:%S") , postcode), params={}, headers=headers)
    m = r.json()
    global intensity_forecast
    intensity_forecast = [(applied_time + timedelta(seconds=10*i), m['data']['data'][i]['intensity']['forecast']) for i in range(len(m['data']['data']))]

    if(manual == False):
        sorted_forecast = sorted(intensity_forecast[0:intervals_available], key=lambda tup: tup[1])
        sorted_time = sorted(sorted_forecast[0:(intervals_to_charge)], key=lambda tup: tup[0])
    else:
        sorted_time = [intensity_forecast[i] for i in range(len(intensity_forecast)) if intensity_forecast[i][1]<threshold]

    return(sorted_time)

@app.route('/get_charging_state', methods=['GET'])

def get_charging_state(demo=False):
    global current_time
    global manual
    global threshold
    global time
    global window
    global current_state

    bins = [360,260,160,60,0]
    # returns list of tuples below the threshold [('time_str', 200), ('time_str', 200)]
    charging_list = get_charging_list()
    current_state = 0
    current_intensity = "unknown"
    print(f"charging list: {charging_list}")
    for tuple_time, tuple_intensity in charging_list:
        if tuple_time < datetime.now() < tuple_time + timedelta(seconds=10):
            print(f"In if with {tuple_time}")
            current_state = [5-i for i in range(len(bins)) if int(tuple_intensity)>=bins[i]][0]
            current_intensity = tuple_intensity
            print(f"Current state {current_state}")
            
    return jsonify({'state': current_state, 'current_intensity': current_intensity})

if __name__ == '__main__':
    app.run()
