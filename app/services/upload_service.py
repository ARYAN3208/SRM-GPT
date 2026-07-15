class UploadService:

    def process_upload(
        self,
        filename: str
    ):

        result = {

            "filename":
            filename,

            "status":
            "stored"

        }

        return result