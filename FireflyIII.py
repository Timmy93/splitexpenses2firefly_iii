import requests


class FireflyIII:

    def __init__(self, url, token, logger):
        self.logging = logger
        if not url or not token:
            self.logging.warning('Invalid Firefly III URL or token')
            raise ValueError('Invalid Firefly III URL or token')
        self.url = url
        self.apiVersion = "v1"
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}
        self.userInfo = None
        self.user_id = None

    def login(self):
        try:
            self.userInfo = self.getCurrentUserInfo()
            self.user_id = self.userInfo['id']
        except requests.exceptions.RequestException as e:
            self.logging.warning(f"Error during login to Firefly {self.url}: {str(e)}")
            print(f"Error during login to Firefly {self.url}: {str(e)}")
            return None

    def getSystemInfo(self):
        """Returns general system information and versions of the (supporting) software."""
        api_url = f"{self.url}/api/{self.apiVersion}/about"
        return self.getRequest(api_url)

    def getCurrentUserInfo(self):
        """Returns the currently authenticated user."""
        api_url = f"{self.url}/api/{self.apiVersion}/about/user"
        return self.getRequest(api_url)

    def getAllTransactions(self):
        """This endpoint returns a list of all the transactions connected to the account."""
        if not self.user_id:
            self.login()
        api_url = f"{self.url}/api/{self.apiVersion}/accounts/{self.user_id}/transactions"
        return self.getRequest(api_url)

    def insertTransaction(self, date: str, amount: float, description: str, category: str, source: str, dest: str,
                          message: str, sw_id: int, tag: list, splitExpense: bool):
        """Insert a new transaction"""
        if not splitExpense:
            print("Skipping internal payment")
            return
        api_url = f"{self.url}/api/{self.apiVersion}/transactions"
        data = {
            "error_if_duplicate_hash": True,
            "apply_rules": True,
            "transactions": [
                {
                    "type": "withdrawal",
                    "date": date,
                    "amount": amount,
                    "description": description,
                    "category_name": category,
                    "source_name": source,
                    "destination_name": dest,
                    "tags": tag,
                    "notes": f"Import from Splitwise\n\n{message}",
                    "external_id": sw_id
                }
            ]
        }
        try:
            response = requests.post(api_url, headers=self.headers, json=data)
            content = response.content
            print(content)
            response.raise_for_status()
            return response.json()['data']
        except requests.exceptions.RequestException as e:
            self.logging.warning(f"Error contacting the API: {str(e)}")
            print(f"Error contacting the API: {e}")
            return None

    def listTransactionThisTag(self, tag: str, limit=50, page=1):
        """Search for all transaction of a given ID"""
        api_url = f"{self.url}/api/{self.apiVersion}/tags/{tag}/transactions?limit={limit}&page={page}"
        return self.getRequest(api_url)

    def searchTransaction(self, query: str, limit=1, page=1):
        """Search transaction. Used to validate if a certain transaction has already been inserted"""
        api_url = f"{self.url}/api/{self.apiVersion}/search/transactions?limit={limit}&page={page}&query={query}"
        return self.getRequest(api_url)

    def deleteTransactionsThisTag(self, defaultTags: list):
        """Delete all the transaction referred to this tag"""
        page = 1
        for tag in defaultTags:
            while True:
                transactions = self.listTransactionThisTag(tag, page=page)
                if not transactions:
                    break
                for transaction in transactions:
                    self.deleteTransaction(transaction)
                page += 1

    def deleteTransaction(self, transaction):
        """Delete the given transaction"""
        try:
            api_url = f"{self.url}/api/{self.apiVersion}/transactions/{transaction['id']}"
            response = requests.delete(api_url, headers=self.headers)
            response.raise_for_status()
            self.logging.info(f"Deleted this transaction {transaction['attributes']['transactions'][0]['description']}[{transaction['id']}]")
            print(f"Deleted this transaction {transaction['attributes']['transactions'][0]['description']}[{transaction['id']}]")
        except requests.exceptions.RequestException as e:
            self.logging.warning(f"Cannot delete this transaction {transaction['attributes']['transactions'][0]['description']}[{transaction['id']}]: {str(e)}")
            print(f"Cannot delete this transaction {transaction['attributes']['transactions'][0]['description']}[{transaction['id']}]: {e}")

    def updateTransaction(self, ff_id: int, date: str, amount: float, description: str, category: str, message: str, tag: list, splitExpense: bool):
        if not splitExpense:
            print("Skipping internal payment")
            return
        try:
            api_url = f"{self.url}/api/{self.apiVersion}/transactions/{ff_id}"
            data = {
                "transactions": [
                    {
                        "date": date,
                        "amount": amount,
                        "description": description,
                        "category_name": category,
                        "tags": tag,
                        "notes": f"Import from Splitwise\n\n{message}",
                    }
                ]
            }
            response = requests.put(api_url, headers=self.headers, json=data)
            content = response.content
            response.raise_for_status()
            self.logging.info(f"Transaction successfully updated [ID: {ff_id}]")
            print("Update successful")
            return response.json()['data']
        except requests.exceptions.RequestException as e:
            self.logging.warning(f"Cannot update this transaction [{ff_id}]: {str(e)}")
            print(f"Cannot update this transaction [{ff_id}]: {e}")

    def getRequest(self, api_url):
        try:
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()
            return response.json()['data']
        except requests.exceptions.RequestException as e:
            self.logging.warning(f"Error contacting the API: {str(e)}")
            print(f"Error contacting the API: {e}")
            return None
