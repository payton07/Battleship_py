class Response:
    def __init__(self, success, message):
        self.success = success
        self.message = message

    def get_success(self):
        return self.success

    def get_message(self):
        return self.message
