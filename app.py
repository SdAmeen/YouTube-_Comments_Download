from flask import Flask, render_template, request, send_file
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError 
import os
import string

app = Flask(__name__)

# API key directly inserted into the backend code
API_KEY = 'your api key'

# Function to get comments from YouTube video
def get_comments(video_id, api_key, max_comments=30000):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            textFormat='plainText'
        )
        response = request.execute()

        while response:
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)
                if len(comments) >= max_comments:
                    break
            if 'nextPageToken' in response and len(comments) < max_comments:
                request = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    pageToken=response['nextPageToken'],
                    maxResults=100,
                    textFormat='plainText'
                )
                response = request.execute()
            else:
                break
                
    except HttpError as e:
        if e.resp.status == 404:
            print(f"Video with ID '{video_id}' not found. Skipping...")
        elif e.resp.status == 400:
            print(f"Error 400: Invalid request for video ID '{video_id}'. Skipping...")
        else:
            print(f"An error occurred for video ID '{video_id}': {e}")
    
    except Exception as e:
        print(f"An unexpected error occurred for video ID '{video_id}': {e}")
    
    return comments

# Function to sanitize comments
def sanitize_comment(comment):
    # Remove non-printable characters
    printable = set(string.printable)
    comment = ''.join(filter(lambda x: x in printable, comment))

    return comment

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_comments', methods=['POST'])
def download_comments():
    # channel_name = request.form['channel_name']
    video_url = request.form['video_url']
    
    video_id = video_url.split('v=')[1].split('&')[0]  # Extract video ID
    
    comments = get_comments(video_id, API_KEY)
    
    # Sanitize and save comments
    comments_list = [{'Comment': sanitize_comment(comment)} for comment in comments]
    comments_df = pd.DataFrame(comments_list)
    
    output_dir = 'downloads'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, f'{video_id}_comments.xlsx')
    comments_df.to_excel(output_file, index=False)
    
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
