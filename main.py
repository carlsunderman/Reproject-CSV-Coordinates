from flask import Flask, render_template, request, send_file
import pandas as pd
import geopandas as gpd
import os
import io
import uuid
import datetime

app = Flask(__name__)

basename = "reprojected_file"
suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

allowed_extensions = ['csv']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():

    if request.method == 'POST' and 'file' in request.files:
        f = request.files['file']
        if f.filename != '' and allowed_file(f.filename):

            file = request.files['file']
            if file.filename == '':
                return 'No file selected'

            if file:
                dataframe = pd.read_csv(file)
                dataframe_html = dataframe.to_html()
                columns = dataframe.columns.tolist()
                return render_template('index.html', dataframe_html=dataframe_html, columns=columns)

            return 'Error reading file'
        else:
            return 'Incorrect or no file uploaded'

@app.route('/download', methods=['POST'])
def download():
    dataframe_html = request.form['dataframe_html']
    
    df = pd.read_html(dataframe_html)[0]

    long_col = request.form['long']
    srcEPSG = request.form['srcEPSG']

    lat_col = request.form['lat']
    destEPSG = request.form['newEPSG']

    df_xy = df[[long_col, lat_col]]

    geometry = gpd.points_from_xy(df_xy[long_col], df_xy[lat_col], crs=f"EPSG:{srcEPSG}")
    geodataframe = gpd.GeoDataFrame(df, geometry=geometry)

    new_geodataframe = geodataframe.to_crs(f"EPSG:{destEPSG}")

    new_geodataframe[f'X_{destEPSG}'] = new_geodataframe.geometry.x
    new_geodataframe[f'Y_{destEPSG}'] = new_geodataframe.geometry.y
    new_geodataframe.drop(columns=['geometry'], inplace=True)

    file_name = f'{str(uuid.uuid4())}.csv'
    # file_name = f'/tmp/{str(uuid.uuid4())}.csv'
        
    new_geodataframe.to_csv(file_name, index=False)

    return_data = io.BytesIO()
    with open(file_name, 'rb') as fo:
        return_data.write(fo.read())

    return_data.seek(0)

    os.remove(file_name)

    return send_file(return_data, mimetype='application/csv',
                     download_name =f'{"_".join([basename, suffix])}.csv')

if __name__ == '__main__':
    app.run()
