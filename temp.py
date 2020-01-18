import requests
import json
from datetime import date,datetime,timedelta
import time



time_until_stop = 6
time_to_charge = 6
treshold = 0
postcode = "CB2"
time_of_last_request=0;
today = date.today()
current_time =  datetime.now();
current_time = current_time.strftime("%H:%M")



def get_charging_list (time_until_stop, time_to_charge, read_time,postcode, treshold = 0):
    if(time_until_stop<time_to_charge):
        return("Not enough to fully charge")
    headers = {
        'Accept': 'application/json'
    }

    r = requests.get('https://api.carbonintensity.org.uk/regional/intensity/%sT%sZ/fw48h/postcode/%s'%(read_time.strftime("%Y-%m-%d"),read_time.strftime("%H:%M:%S") , postcode), params={}, headers=headers)
    m = r.json()
    intensity_forecast = [(m['data']['data'][i]['from'],m['data']['data'][i]['intensity']['forecast']) for i in range(len(m['data']['data']))]

    if(treshold == 0):
        print(intensity_forecast[0:time_until_stop])
        sorted_forecast = sorted(intensity_forecast[0:time_until_stop], key=lambda tup: tup[1])
        sorted_time = sorted(sorted_forecast[0:(time_to_charge)], key=lambda tup: tup[0])
    else:
        sorted_time = [intensity_forecast[i] for i in range(len(intensity_forecast)) if intensity_forecast[i][1]<treshold]

    return(sorted_time)

update_time = datetime.now()
time.sleep(1.2)
current_time =  datetime.now();
if (datetime.now() - update_time > timedelta(0, 1)):
    current_time = current_time + timedelta(minutes = 30)
    print(current_time)

def request_answer(demo=False):
    bins = [360,260,160,60,0]
    if(demo):
        if (datetime.now() - update_time > timedelta(0, 10)):
            current_time = current_time + timedelta(minutes=30)
            print(current_time)
    else:
        current_time = datetime.now()
    val_list = get_charging_list(time_until_stop,time_to_charge,current_time, "CB2")
    if val_list[0][0]>"%sT%sZ"%(current_time.strftime("%Y-%m-%d"),current_time.strftime("%H:%M:%S")):
        print(val_list[0], current_time)
        return 0
    else:
        return [5-i for i in range(len(bins)) if int(val_list[0][1])>=bins[i]][0]

print(request_answer())