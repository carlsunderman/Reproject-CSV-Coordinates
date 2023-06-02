from flask import Flask, render_template, request, send_file
import pandas as pd
import geopandas as gpd
import os
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if os.path.exists('Downloaded_data.csv'):
        try:
            os.remove('Downloaded_data.csv')
        except Exception as e:
            print (e)
    else:
        print ("no")

    if 'file' not in request.files:
        return 'No file uploaded'

    file = request.files['file']
    if file.filename == '':
        return 'No file selected'

    if file:
        dataframe = pd.read_csv(file)
        dataframe_html = dataframe.to_html()
        columns = dataframe.columns.tolist()
        return render_template('index.html', dataframe_html=dataframe_html, columns=columns)

    return 'Error reading file'

@app.route('/download', methods=['POST'])
def download():
    dataframe_html = request.form['dataframe_html']
    df = pd.read_html(dataframe_html)[0]

    long_col = request.form['long']
    srcEPSG = request.form['srcEPSG']

    lat_col = request.form['lat']
    destEPSG = request.form['newEPSG']

    # outputFilename = request.form['outputFilename']

    df_xy = df[[long_col, lat_col]]

    geometry = gpd.points_from_xy(df_xy[long_col], df_xy[lat_col], crs=f"EPSG:{srcEPSG}")
    geodataframe = gpd.GeoDataFrame(df, geometry=geometry)

    new_geodataframe = geodataframe.to_crs(f"EPSG:{destEPSG}")

    new_geodataframe[f'X_{destEPSG}'] = new_geodataframe.geometry.x
    new_geodataframe[f'Y_{destEPSG}'] = new_geodataframe.geometry.y
    new_geodataframe.drop(columns=['geometry'], inplace=True)

    file_name = 'Downloaded_data.csv'
    
    new_geodataframe.to_csv(file_name, index=False)

    return send_file(file_name, as_attachment=True)
    # return render_template('conversion_complete.html', output_file = file_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
