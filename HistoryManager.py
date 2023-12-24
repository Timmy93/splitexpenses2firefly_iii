import json
import datetime
import os

class HistoryManager:
    def __init__(self):
        self.path = "data"
        self.fileName = "last_export.json"
        self.file_path = os.path.join(self.path, self.fileName)
        self.firstRun = True
        self.lastRun = "2011-01-01"

    def loadHistory(self):
        """Read last export"""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                last_run_date = data.get('last_run', None)
                if last_run_date:
                    # Parse the date string to a datetime object
                    self.firstRun = False
                    last_run_date = datetime.datetime.strptime(last_run_date, '%Y-%m-%d')
                    self.lastRun = last_run_date.strftime('%Y-%m-%d')
                else:
                    self.firstRun = True
                    self.lastRun = "2011-01-01"
        else:
            self.firstRun = True
            self.lastRun = "2011-01-01"
        return self.lastRun

    def storeHistory(self):
        """Update the last export date"""
        self.firstRun = False
        self.lastRun = datetime.date.today().strftime('%Y-%m-%d')
        data = {'last_run': self.lastRun}
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=2)

    def getLastSplitwiseExport(self) -> str:
        return self.lastRun

    def isFirstExport(self) -> bool:
        return self.firstRun
