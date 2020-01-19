from flask import Flask, request, jsonify
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

app = Flask(__name__)

app.config.from_object("config.Config")

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

    r = requests.get('https://api.carbonintensity.org.uk/regional/intensity/%sT%sZ/fw48h/postcode/%s'%(read_time.strftime("%Y-%m-%d"),read_time.strftime("%H:%M:%S") , postcode), params={}, headers=headers)
    m = r.json()
    intensity_forecast = [(m['data']['data'][i]['from'],m['data']['data'][i]['intensity']['forecast']) for i in range(len(m['data']['data']))]

    if(threshold == 0):
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


    intervals_to_charge = time*2
    intervals_available = window*2


    bins = [360,260,160,60,0]
    if(demo):
        if (datetime.now() - update_time > timedelta(0, 10)):
            previous_time = current_time
            current_time = current_time + timedelta(minutes=30)
    else:
        previous_time = current_time
        current_time = datetime.now()
    if(current_time - previous_time >= timedelta(minutes=30)):
        intervals_available -= 1
        val_list = get_charging_list()
        if val_list[0][0]>"%sT%sZ"%(current_time.strftime("%Y-%m-%d"),current_time.strftime("%H:%M:%S")):
            #previous_state = current_state;
            current_state = 0
            return current_state
        else:
            intervals_to_charge -= 1
            #previous_state = current_state;
            current_state = [5-i for i in range(len(bins)) if int(val_list[0][1])>=bins[i]][0]
            return jsonify({'state': current_state})
    else:
        return jsonify({'state': current_state})





if __name__ == '__main__':
    app.run()
