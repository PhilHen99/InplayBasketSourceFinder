"""
Data Integration Service for Basketball Dashboard
Handles secure data fetching from SharePoint, Google Drive, and other cloud providers
"""

import os
import json
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO

# Cloud storage imports
try:
    import boto3
    from azure.storage.file import FileService
    from google.cloud import storage as gcs
    from google.oauth2.service_account import Credentials
    import requests
except ImportError as e:
    logging.warning(f"Some cloud dependencies not available: {e}")

# Make sure Credentials is always available
try:
    from google.oauth2.service_account import Credentials
except ImportError:
    Credentials = None

class DataIntegrationService:
    """
    Secure data integration service supporting multiple cloud providers
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_providers = ['sharepoint', 'google_drive', 'aws_s3', 'azure_files']
        
    def fetch_excel_data(self, provider: str, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch Excel data from specified cloud provider
        
        Args:
            provider: Cloud provider ('sharepoint', 'google_drive', 'aws_s3', 'azure_files')
            config: Provider-specific configuration
            
        Returns:
            pandas.DataFrame: Cleaned basketball teams data
        """
        if provider not in self.supported_providers:
            raise ValueError(f"Unsupported provider: {provider}")
            
        try:
            if provider == 'sharepoint':
                return self._fetch_from_sharepoint(config)
            elif provider == 'google_drive':
                return self._fetch_from_google_drive(config)
            elif provider == 'aws_s3':
                return self._fetch_from_s3(config)
            elif provider == 'azure_files':
                return self._fetch_from_azure(config)
        except Exception as e:
            self.logger.error(f"Error fetching data from {provider}: {str(e)}")
            raise
    
    def _fetch_from_sharepoint(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch Excel file from SharePoint Online
        
        Config should include:
        - site_url: SharePoint site URL
        - file_path: Path to Excel file
        - client_id: Application client ID
        - client_secret: Application client secret
        - tenant_id: Azure tenant ID
        """
        try:
            # Get access token
            token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            access_token = token_response.json()['access_token']
            
            # Download file from SharePoint
            headers = {'Authorization': f'Bearer {access_token}'}
            file_url = f"{config['site_url']}/_api/web/GetFileByServerRelativeUrl('{config['file_path']}')/\$value"
            
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()
            
            # Read Excel data
            df = pd.read_excel(BytesIO(response.content))
            return self._clean_data(df)
            
        except Exception as e:
            self.logger.error(f"SharePoint fetch error: {str(e)}")
            raise
    
    def _fetch_from_google_drive(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch Excel file from Google Drive
        
        Config should include:
        - file_id: Google Drive file ID
        - credentials_path: Path to service account JSON file
        """
        try:
            import requests
            from google.oauth2.service_account import Credentials
            from google.auth.transport.requests import Request
            
            # Authenticate with Google Drive
            credentials = Credentials.from_service_account_file(
                config['credentials_path'],
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            # Refresh credentials to get token
            credentials.refresh(Request())
            
            # Download file
            drive_url = f"https://www.googleapis.com/drive/v3/files/{config['file_id']}?alt=media"
            headers = {'Authorization': f'Bearer {credentials.token}'}
            
            response = requests.get(drive_url, headers=headers)
            response.raise_for_status()
            
            # Read Excel data
            df = pd.read_excel(BytesIO(response.content))
            return self._clean_data(df)
            
        except Exception as e:
            self.logger.error(f"Google Drive fetch error: {str(e)}")
            raise
    
    def _fetch_from_s3(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch Excel file from AWS S3
        
        Config should include:
        - bucket: S3 bucket name
        - key: S3 object key
        - aws_access_key_id: AWS access key (optional if using IAM roles)
        - aws_secret_access_key: AWS secret key (optional if using IAM roles)
        - region: AWS region
        """
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.get('aws_access_key_id'),
                aws_secret_access_key=config.get('aws_secret_access_key'),
                region_name=config.get('region', 'us-east-1')
            )
            
            # Download file from S3
            response = s3_client.get_object(
                Bucket=config['bucket'],
                Key=config['key']
            )
            
            # Read Excel data
            df = pd.read_excel(BytesIO(response['Body'].read()))
            return self._clean_data(df)
            
        except Exception as e:
            self.logger.error(f"S3 fetch error: {str(e)}")
            raise
    
    def _fetch_from_azure(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch Excel file from Azure File Storage
        
        Config should include:
        - account_name: Azure storage account name
        - account_key: Azure storage account key
        - share_name: File share name
        - file_path: Path to file within share
        """
        try:
            file_service = FileService(
                account_name=config['account_name'],
                account_key=config['account_key']
            )
            
            # Download file from Azure Files
            file_content = file_service.get_file_to_bytes(
                share_name=config['share_name'],
                directory_name='',
                file_name=config['file_path']
            )
            
            # Read Excel data
            df = pd.read_excel(BytesIO(file_content.content))
            return self._clean_data(df)
            
        except Exception as e:
            self.logger.error(f"Azure Files fetch error: {str(e)}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the basketball teams data
        
        Args:
            df: Raw DataFrame from Excel file
            
        Returns:
            pandas.DataFrame: Cleaned data
        """
        # Fill NaN values with empty strings
        df = df.fillna('')
        
        # Standardize column names if needed
        expected_columns = ['Team', 'Sports', 'Country', 'League', 'Twitter', 
                          'Facebook', 'Instagram', 'Official Page', 'Other Links']
        
        # Log data quality metrics
        self.logger.info(f"Loaded {len(df)} teams from {len(df['Country'].unique())} countries")
        
        return df
    
    def get_data_freshness(self, provider: str, config: Dict[str, Any]) -> datetime:
        """
        Get the last modified timestamp of the data source
        
        Args:
            provider: Cloud provider name
            config: Provider configuration
            
        Returns:
            datetime: Last modified timestamp
        """
        # Implementation would vary by provider
        # This is a placeholder that returns current time
        return datetime.now()
    
    def validate_connection(self, provider: str, config: Dict[str, Any]) -> bool:
        """
        Validate connection to the specified cloud provider
        
        Args:
            provider: Cloud provider name
            config: Provider configuration
            
        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            # Test connection without downloading full file
            if provider == 'sharepoint':
                # Test SharePoint connection
                token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
                token_data = {
                    'grant_type': 'client_credentials',
                    'client_id': config['client_id'],
                    'client_secret': config['client_secret'],
                    'scope': 'https://graph.microsoft.com/.default'
                }
                response = requests.post(token_url, data=token_data)
                return response.status_code == 200
                
            elif provider == 'google_drive':
                # Test Google Drive connection
                import requests
                from google.oauth2.service_account import Credentials
                from google.auth.transport.requests import Request
                credentials = Credentials.from_service_account_file(
                    config['credentials_path'],
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                credentials.refresh(Request())
                return credentials is not None
                
            elif provider == 'aws_s3':
                # Test S3 connection
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=config.get('aws_access_key_id'),
                    aws_secret_access_key=config.get('aws_secret_access_key'),
                    region_name=config.get('region', 'us-east-1')
                )
                s3_client.head_object(Bucket=config['bucket'], Key=config['key'])
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Connection validation failed for {provider}: {str(e)}")
            return False 