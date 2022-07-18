import io
import requests
from flask import Flask, render_template, request, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta



app = Flask(__name__)
app.config['DEBUG'] = True

#function that pulls the data of current temp from the API
def check_url(city):
    now_url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=ac7de2321284c97155cbbeef69525161'
    r = requests.get(now_url.format(city)).json()
    return (r)

#function that convert temprature in fahrenheit to celsius
def FrnttoCels(temp):
    new_temp = (temp - 32) * 0.5556
    return(int(new_temp))

#function that get the date of 5 days ago and convert it to unix time
def GetHistoricDate():
    yesterday = datetime.now() - timedelta(5) 
    yesterday = str(datetime.strftime(yesterday, '%Y/%m/%d'))
    unix_date_url = 'https://showcase.api.linx.twenty57.net/UnixTime/tounix?date={} 16:00:00'
    r_unix = requests.get(unix_date_url.format(yesterday))
    FiveDago = (r_unix.text.replace('"',''))
    return FiveDago





@app.route('/', methods = ['GET', 'POST'])
def index():
    city = 'Boston' #This is the default city to show

    #This is the part that get the user input for other cities

    if request.method == 'POST':
        city = request.form.get('city')
        r = (check_url(city))
        #if user enter not existing city we will show him Boston weather instead
        if r['cod'] == '404':
            city = 'Boston'
                

    #if there is no POST req (first time the web page load we need to make request)
    r = check_url(city)
    print(r)
    #get the relevant data to show on the web page

    weather_data = {
        'city' : city,
        'temp' : r['main']['temp'],
        'main_weather' : r['weather'][0]['main'],
        'description' : r['weather'][0]['description'],
        'icon' : r['weather'][0]['icon'],
        'lat': r['coord']['lat'],
        'lon' : r['coord']['lon']
    }
    global lat
    global lon
    lat = weather_data['lat']
    lon = weather_data['lon']

    print(weather_data)

    #Get the historical weather of the city (last 5 days)

    FiveDago_unix = GetHistoricDate()
    historic_url = 'https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={}&lon={}&dt={}&only_current=true&units=imperial&appid=ac7de2321284c97155cbbeef69525161'
    r2 = requests.get(historic_url.format(weather_data['lat'], weather_data['lon'], FiveDago_unix)).json()
    print(r2)

    historical_data = {
        'city' : city,
        'temp' : r2['current']['temp'],
        'main_weather' : r2['current']['weather'][0]['main'],
        'description' : r2['current']['weather'][0]['description'],
        'icon' : r2['current']['weather'][0]['icon']
    }

    print(historical_data)

    global df
    df = pd.DataFrame({city:['Temp', 'Main Weather', 'Weather Description'], 'Now': [r['main']['temp'],r['weather'][0]['main'], r['weather'][0]['description']],
                    '5 Days Ago': [r2['current']['temp'], r2['current']['weather'][0]['main'],r2['current']['weather'][0]['description']]})
    

    print(df)
    raw_data = r
    print (raw_data)

    celc_temp = FrnttoCels( r['main']['temp'])
    historic_celc_temp = FrnttoCels( r2['current']['temp'])

    print(celc_temp)

    
    
    #return the final page
    return render_template('index.html',  weather_data=weather_data, historical_data=historical_data, r=r, r2=r2, celc_temp=celc_temp, historic_celc_temp=historic_celc_temp)

    
#this route will handle the weather data download file
@app.route('/download', methods = ['GET'])
def download_data():
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    df.to_excel(writer, startrow = 0, merge_cells = False, sheet_name = "Sheet_1")
    workbook = writer.book
    worksheet = writer.sheets["Sheet_1"]
    format = workbook.add_format()
    format.set_align('center')
    format.set_align('vcenter')
    worksheet.set_column('A:D',15, format)
    writer.close()
    output.seek(0)

    #return the file
    return send_file(output, attachment_filename="weather_data.xlsx", as_attachment=True)



#this route will handle the 5 days avg process
@app.route('/avg', methods = ['GET', 'POST'])
def five_day_unix_date():
    five_day_dates = []
    five_day_unix = []
    for i in range(1,6):
        yesterday = datetime.now() - timedelta(i) 
        five_day_dates.append(str(datetime.strftime(yesterday, '%Y/%m/%d')))

    #convert regular date to unix date with showcase API
    for i2 in five_day_dates:
        unix_date_url = 'https://showcase.api.linx.twenty57.net/UnixTime/tounix?date={} 16:00:00'
        r3 = requests.get(unix_date_url.format(i2))
        five_day_unix.append(r3.text.replace('"',''))

    global temp_avg
    temp_lst =[]

    #loop through the unix date and get the temp of every day in the last 5 days from openweathermap API
    for i4 in five_day_unix:
        url = 'https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={}&lon={}&dt={}&only_current=true&units=imperial&appid=ac7de2321284c97155cbbeef69525161'
        r4 = requests.get(url.format(lat, lon, i4)).json()
        temp_lst.append(r4['current']['temp'])
    temp_avg = sum(temp_lst) / len(temp_lst)
    #print(temp_avg)

    #return the page with the avg temp
    return render_template('avg.html',  temp_avg=temp_avg)



