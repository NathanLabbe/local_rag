import os
import logging
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from app.config import settings

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self._init_credentials()
        
    def _init_credentials(self):
        """Initialize Google Drive credentials"""
        creds = None
        
        # Check if token file exists
        if os.path.exists(settings.google_token_file):
            creds = Credentials.from_authorized_user_info(
                json.load(open(settings.google_token_file))
            )
            
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.google_credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
                
            # Save credentials for next run
            os.makedirs(os.path.dirname(settings.google_token_file), exist_ok=True)
            with open(settings.google_token_file, 'w') as token:
                token.write(creds.to_json())
                
        self.credentials = creds
        self.service = build('drive', 'v3', credentials=creds)
    
    async def fetch_files(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch files from Google Drive folder"""
        try:
            query = "'me' in owners"
            
            # If folder ID is provided, filter by that folder
            if folder_id:
                query += f" and '{folder_id}' in parents"
                
            # Only fetch text files, documents, etc.
            mime_types = [
                "text/plain",
                "application/pdf",
                "application/vnd.google-apps.document",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ]
            
            mime_type_query = " or ".join([f"mimeType='{mime}'" for mime in mime_types])
            query += f" and ({mime_type_query})"
            
            results = self.service.files().list(
                q=query,
                pageSize=50,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            logger.error(f"Error fetching files from Drive: {str(e)}")
            return []
    
    async def download_file(self, file_id: str) -> Optional[str]:
        """Download a file from Google Drive and return its content as text"""
        try:
            # Get file metadata to check mime type
            file_metadata = self.service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType')
            
            # For Google Docs, export as plain text
            if mime_type == 'application/vnd.google-apps.document':
                response = self.service.files().export(
                    fileId=file_id,
                    mimeType='text/plain'
                ).execute()
                
                return response.decode('utf-8')
            else:
                # For other files, download directly
                request = self.service.files().get_media(fileId=file_id)
                file = io.BytesIO()
                downloader = MediaIoBaseDownload(file, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                file.seek(0)
                return file.read().decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            return None

_drive_service = None

async def get_drive_service():
    global _drive_service
    if _drive_service is None:
        _drive_service = GoogleDriveService()
    return _drive_service