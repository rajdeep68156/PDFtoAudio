import os
import re
from google.cloud import vision
from google.cloud import storage
from google.protobuf import json_format
from pydub import AudioSegment

path="sonia-project-1-5a96037450a4.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=path

def async_detect_document(gcs_source_uri, gcs_destination_uri):

    mime_type = 'application/pdf'

    batch_size = 100

    client = vision.ImageAnnotatorClient()

    feature = vision.types.Feature(type=vision.enums.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.types.GcsSource(uri=gcs_source_uri)
    input_config = vision.types.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.types.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.types.OutputConfig(gcs_destination=gcs_destination, batch_size=batch_size)

    async_request = vision.types.AsyncAnnotateFileRequest(features=[feature], input_config=input_config, output_config=output_config)

    operation = client.async_batch_annotate_files(requests=[async_request])

    print('Waiting for the operation to finish.')
    operation.result(timeout=420)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client()

    #Destination
    match = re.match(r'gs://([^/]+)/(.+)', gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)

    #Source
    match = re.match(r'gs://([^/]+)/(.+)', gcs_source_uri)
    bucket_name_source = match.group(1)
    prefix_source = match.group(2)

    bucket = storage_client.get_bucket(bucket_name)
    blob_list = list(bucket.list_blobs(prefix=prefix))
    # print('Output files:')
    # for blob in blob_list:
    #     print(blob.name)

    output = blob_list[0]
    json_string = output.download_as_string()
    response = json_format.Parse(json_string, vision.types.AnnotateFileResponse())
    num_of_pages = len(response.responses)

    for i in range(len(response.responses)):
        full_text=''
        page_response=response.responses[i]
        annotation=page_response.full_text_annotation
        full_text=full_text+annotation.text
        print('Page {}:/n {}'.format(i, full_text))
        synthesize_text(full_text, prefix_source, i, num_of_pages)

def synthesize_text(text, audiofile_blob_name, page_index, num_of_pages):
    from google.cloud import texttospeech

    storage_client = storage.Client()
    bucket_name = 'vision-result-audiofiles'
    bucket = storage_client.get_bucket(bucket_name)

    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.types.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.types.VoiceSelectionParams(language_code='en-US', ssml_gender=texttospeech.enums.SsmlVoiceGender.MALE)
    audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)
    response = client.synthesize_speech(input_text, voice, audio_config)

    destination_blob_name = audiofile_blob_name.split('.')[0]
    blob = bucket.blob(destination_blob_name+'.mp3') #add timestamp later

    # The response's audio_content is binary.
    with open(destination_blob_name+"_"+str(page_index)+'.mp3', 'wb') as out:
        out.write(response.audio_content)
        print('Audio content written to file '+destination_blob_name+"_"+str(page_index)+'.mp3')

    full_audio_pdf=AudioSegment.from_mp3(destination_blob_name+"_"+str(0)+'.mp3')
    if page_index == num_of_pages-1:
        for i in range(1, num_of_pages):
            sound_1 = AudioSegment.from_mp3(destination_blob_name+"_"+str(i)+'.mp3')
            full_audio_pdf=full_audio_pdf+sound_1

        full_audio_pdf.export(destination_blob_name+'.mp3', format="mp3")
        blob.upload_from_filename(destination_blob_name+'.mp3')
        print("Full Audio Written To GCS bucket.")

    # https://storage.googleapis.com/vision-result-audiofiles/SoniaResume.mp3

if __name__ == "__main__":
    async_detect_document("gs://vision-source/3-pages.pdf", "gs://vision-destination/destination")
