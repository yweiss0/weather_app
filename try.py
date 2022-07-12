import io
import requests
from flask import Flask, render_template, request, send_file
import pandas as pd
from io import BytesIO



app = Flask(__name__)
app.config['DEBUG'] = True


def check_url(city):
    now_url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=ac7de2321284c97155cbbeef69525161'
    r = requests.get(now_url.format(city)).json()
    return (r)

def FrnttoCels(temp):
    new_temp = (temp - 32) * 0.5556
    return(int(new_temp))

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
    print(weather_data)

    #Get the historical weather of the city (last 5 days)

    historic_url = 'https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={}&lon={}&dt=1657472400&only_current=true&units=imperial&appid=ac7de2321284c97155cbbeef69525161'
    r2 = requests.get(historic_url.format(weather_data['lat'], weather_data['lon'])).json()
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

    return render_template('index.html',  weather_data=weather_data, historical_data=historical_data, r=r, r2=r2, celc_temp=celc_temp, historic_celc_temp=historic_celc_temp)

    

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

    #the writer has done its job
    writer.close()

    #go back to the start of the stream
    output.seek(0)

    #finally return the file
    return send_file(output, attachment_filename="weather_data.xlsx", as_attachment=True)


    