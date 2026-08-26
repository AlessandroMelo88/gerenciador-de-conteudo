#!/usr/bin/env python3
import json, sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = '/app/youtube/token-hacker-libertario.json'
VIDEO_IDS = ['POVgeYAtpwo','qqXgCx4SY78','0C5d0AAQCeE','0j_oKfOb75s','7Kyq_iYqMN0','rU7c03-51y8','dO6x2Q6l13U']

with open(TOKEN_FILE) as f:
    data = json.load(f)

print('Scopes:', data.get('scopes'))

creds = Credentials(
    token=data['token'],
    refresh_token=data['refresh_token'],
    token_uri=data['token_uri'],
    client_id=data['client_id'],
    client_secret=data['client_secret'],
    scopes=data.get('scopes', ['https://www.googleapis.com/auth/youtube.upload']),
)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    print('Token refreshed')
    data['token'] = creds.token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=2)

youtube = build('youtube', 'v3', credentials=creds)

for vid in VIDEO_IDS:
    try:
        resp = youtube.videos().list(part='status', id=vid).execute()
        if not resp.get('items'):
            print(f'{vid}: NOT FOUND')
            continue
        privacy = resp['items'][0]['status']['privacyStatus']
        print(f'{vid}: {privacy}')
        if privacy != 'public':
            r = youtube.videos().update(
                part='status',
                body={'id': vid, 'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}}
            ).execute()
            print(f'  -> {r["status"]["privacyStatus"]}')
    except Exception as e:
        print(f'{vid}: ERROR - {type(e).__name__}: {e}', file=sys.stderr)
