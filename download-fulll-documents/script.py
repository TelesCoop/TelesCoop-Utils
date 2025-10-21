import requests
import os
from typing import Optional, Dict, Any, List

class FulllAPIClient:
    """Client for interacting with the Fulll API"""

    def __init__(self, token: str, refresh_token: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.base_url = "https://api.fulll.io" # "https://api-fulll.fulll.house"
        self.token = token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }

    def _request(self, url: str) -> Dict[str, Any]:
        """Make a request with auto-renewal on 401"""
        response = requests.get(url, headers=self._headers())

        if response.status_code == 401:
            self.renew_token()
            response = requests.get(url, headers=self._headers())

        return response.json()

    def renew_token(self) -> Dict[str, Any]:
        """Renew the access token using the refresh token"""
        url = f"{self.base_url}/cred/oauth2/token"

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }

        response = requests.post(url, data=data)
        token_data = response.json()

        self.token = token_data.get('access_token')
        if 'refresh_token' in token_data:
            self.refresh_token = token_data['refresh_token']

        return token_data

    def list_documents(self, slug: str, all_pages: bool = True) -> List[Dict[str, Any]]:
        """
        List documents for a given slug

        Args:
            slug: The document slug/identifier
            all_pages: If True, fetch all pages. If False, return only first page

        Returns:
            List of documents with added document_number field
        """
        url = f"{self.base_url}/document/v1/files/{slug}/list.json?date_from=2020-01-01&limit=1000"
        data = self._request(url)

        all_items = data.get('items', [])

        # Fetch all pages if requested
        if all_pages and data.get('metadata', {}).get('pages', 1) > 1:
            total_pages = data['metadata']['pages']

            for page in range(2, total_pages + 1):
                page_url = f"{url}?page={page}"
                page_data = self._request(page_url)
                all_items.extend(page_data.get('items', []))

        # Add document_number to each item
        for item in all_items:
            document_number = None
            for metadata in item.get('metadatas', []):
                if not isinstance(metadata, dict):
                    continue
                if metadata.get('key') == 'number':
                    document_number = metadata.get('value')
                    break
            item['document_number'] = document_number

        return all_items

    def list_document_types(self) -> Dict[str, Any]:
        """List all document types"""
        url = f"{self.base_url}/document/v1/company/types.json"
        return self._request(url)


# Usage
if __name__ == "__main__":
    client = FulllAPIClient(
        token=os.getenv('FULLL_API_TOKEN'),
        refresh_token=os.getenv('FULLL_REFRESH_TOKEN'),
        client_id=os.getenv('FULLL_CLIENT_ID'),
        client_secret=os.getenv('FULLL_CLIENT_SECRET')
    )

    # List all documents across all pages
    documents = client.list_documents("sales_and_customers")

    # Print document numbers
    for doc in documents:
        print(f"ID: {doc['id']}, Document Number: {doc['document_number']}, Name: {doc['name']}")

    print(f"\nTotal documents: {len(documents)}")