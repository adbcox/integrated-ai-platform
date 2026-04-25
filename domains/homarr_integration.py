class HomarrIntegration:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.api_token = api_token

    def _make_request(self, endpoint: str, method: str = 'GET', data: dict = None) -> dict:
        import requests
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = f"{self.api_url}/{endpoint}"
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError("Unsupported HTTP method")
        
        response.raise_for_status()
        return response.json()

    def get_widgets(self) -> list:
        return self._make_request('widgets')

    def add_widget(self, widget_data: dict) -> dict:
        return self._make_request('widgets', method='POST', data=widget_data)
