import os
import firebase_admin
from firebase_admin import credentials, firestore

from dotenv import load_dotenv
load_dotenv()

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_recording_by_id(recording_id):
    try:
        doc_ref = db.collection('recordings').document(recording_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            print(f"No recording found with ID: {recording_id}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching the recording: {e}")
        return None
    
def add_recording(recording):
    db.collection('recordings').add(recording, recording["id"])

def add_video(video):
    video_data = {
        'edited_date': video['edited_date'],
        'id': video['id'],
        'player': video['player'],
        'title': video['title'],
        'uploaded': False
    }
    db.collection('videos').add(video_data, video['id'])

def update_recording_with_video_info(recording_id, video_id, video_sequence):
    recording_ref = db.collection('recordings').document(recording_id)
    recording_ref.update({
        'video_id': video_id,
        'video_sequence': video_sequence
    })

def get_video_by_id(video_id):
    try:
        doc_ref = db.collection('videos').document(video_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            print(f"No video found with ID: {video_id}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching the video: {e}")
        return None
    
def update_video_with_uploaded_status(video_id, uploaded):
    video_ref = db.collection('videos').document(video_id)
    video_ref.update({
        'uploaded': uploaded
    })