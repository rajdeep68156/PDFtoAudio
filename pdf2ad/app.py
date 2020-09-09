from google.cloud import storage
from flask import Flask, render_template, request
import requests
import os
import pdftoad

path="sonia-project-1-5a96037450a4.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=path
os.environ['PROJECT_ID']='sonia-project-1'

storage_client = storage.Client()
bucket_name = 'vision-source'
bucket = storage_client.get_bucket(bucket_name)

import datetime;
ts = datetime.datetime.now().timestamp()

app = Flask(__name__)
@app.route('/')
def MainPage():
    return render_template('main_page.html')

@app.route('/getFiles', methods=["POST"])
def getFileNames():
    if request.method == 'POST':
        if 'pdf' in request.files:
            pdf = request.files['pdf']
            if pdf.filename != '':
                destination_blob_name = pdf.filename.replace(" ", "_").replace("(", "_").replace(")", "_")
                blob = bucket.blob(destination_blob_name)
                blob.upload_from_file(pdf)
                pdftoad.async_detect_document("gs://vision-source/"+destination_blob_name, "gs://vision-destination/destination"+str(ts))
                name=destination_blob_name
                print("name:", name)
                audio_file=name.split('.')[0]
                download_link="https://storage.googleapis.com/vision-result-audiofiles/"+audio_file+'.mp3'
        # return "Your file is being processed. Here is the download link. "+ download_link
        return render_template('download-link_page.html', download_link=download_link)
    else:
        return '{"resp": "no response"}'

if __name__ == "__main__":
    app.run()
