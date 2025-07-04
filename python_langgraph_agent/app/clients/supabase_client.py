import os
from supabase import create_client, Client
from typing import Optional, Tuple
import uuid

class SupabaseService:
    """
    A wrapper class for the Supabase client to handle interactions with Supabase Storage.
    """
    _client: Optional[Client] = None
    _url: Optional[str] = None
    _key: Optional[str] = None # This should be the service_role_key for admin operations

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initializes the SupabaseService.
        It can be initialized with URL and key directly, or it will load them
        from SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.

        Args:
            url: Optional Supabase project URL.
            key: Optional Supabase service role key.
        """
        self._url = url or os.getenv("SUPABASE_URL")
        self._key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Use service role for uploads

        if not self._url or not self._key:
            print("WARN: SupabaseService initialized without URL or key. Operations will fail.")
            self._client = None
        else:
            try:
                self._client = create_client(self.url, self.key)
                print("DEBUG: Supabase client initialized.")
            except Exception as e:
                print(f"ERROR: Failed to initialize Supabase client: {e}")
                self._client = None

    @property
    def url(self) -> Optional[str]: # Make properties read-only from outside after init
        return self._url

    @property
    def key(self) -> Optional[str]:
        return self._key

    def _get_client(self) -> Client:
        """
        Ensures the client is initialized.
        Raises:
            ValueError: If URL or key is not set.
        """
        if self._client is None:
            if not self.url or not self.key: # Re-check in case set post-init, though not typical for this pattern
                self._url = self._url or os.getenv("SUPABASE_URL")
                self._key = self._key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            if not self.url or not self.key:
                raise ValueError("Supabase URL or key is not set. Please set environment variables or provide during init.")

            self._client = create_client(self.url, self.key)
            print("DEBUG: Supabase client lazy initialized.")
        return self._client

    def upload_image_from_buffer(
        self,
        file_buffer: bytes,
        bucket_name: str,
        destination_path: Optional[str] = None, # e.g., "public/my_image.png" or just "my_image.png"
        content_type: str = "image/png", # Default, but should be accurate
        upsert: bool = False
    ) -> Optional[str]:
        """
        Uploads an image from an in-memory buffer to a Supabase storage bucket.

        Args:
            file_buffer: The image file as bytes.
            bucket_name: The name of the Supabase storage bucket (e.g., "images").
            destination_path: Optional. The path and filename in the bucket. If None, a UUID-based name is generated.
            content_type: The MIME type of the file.
            upsert: Whether to overwrite the file if it already exists. Defaults to False.

        Returns:
            The public URL of the uploaded image, or None if an error occurs.
        """
        client = self._get_client()
        if not client:
            return None

        if not destination_path:
            file_extension = content_type.split('/')[-1] if '/' in content_type else 'png'
            destination_path = f"{uuid.uuid4()}.{file_extension}"

        try:
            print(f"DEBUG: Uploading image buffer to Supabase bucket '{bucket_name}' at path '{destination_path}'")
            # The `upload` method expects a file-like object or bytes.
            # For bytes, we need to specify the content type.
            # The supabase-py library's `upload` method takes `file: Union[bytes, BinaryIO]`
            # and `file_options` for `content_type` and `upsert`.

            # Supabase-py's storage `upload` method:
            # client.storage.from_(bucket_name).upload(path=destination_path, file=file_buffer, file_options={"content-type": content_type, "upsert": str(upsert).lower()})
            # Note: `upsert` in supabase-py file_options is often a string "true" or "false".

            # Let's use a slightly more direct way if available or construct file_options
            # The method signature for upload is: upload(self, path: str, file: Union[FileTypes, Path], file_options: Optional[FileOptions] = None) -> Dict[str, Any]
            # FileTypes = Union[bytes, BinaryIO, BufferedReader, BufferedWriter, TextIOWrapper, SpooledTemporaryFile]
            # FileOptions = TypedDict("FileOptions", {"cache-control": str, "content-type": str, "upsert": bool, "duplex": str}, total=False)

            response = client.storage.from_(bucket_name).upload(
                path=destination_path,
                file=file_buffer,
                file_options={"content-type": content_type, "upsert": upsert}
            )
            # response typically doesn't directly contain the public URL in its immediate return for upload.
            # We need to construct it or use get_public_url.

            if response.status_code == 200: # Or check based on actual supabase-py success indication
                public_url_response = client.storage.from_(bucket_name).get_public_url(destination_path)
                print(f"DEBUG: Supabase - Image uploaded successfully. Public URL: {public_url_response}")
                return public_url_response # This is the direct public URL string
            else:
                print(f"ERROR: Supabase - Failed to upload image. Status: {response.status_code}, Message: {response.json()}")
                return None
        except Exception as e:
            print(f"ERROR: Supabase - Exception during image buffer upload: {e}")
            return None

    def get_public_url(self, bucket_name: str, path: str) -> Optional[str]:
        """Gets the public URL for a file in a bucket."""
        client = self._get_client()
        if not client: return None
        try:
            return client.storage.from_(bucket_name).get_public_url(path)
        except Exception as e:
            print(f"Error getting public URL for {bucket_name}/{path}: {e}")
            return None


# Singleton instance pattern
_supabase_service_instance: Optional[SupabaseService] = None

def get_supabase_service() -> SupabaseService:
    """
    Provides a singleton instance of the SupabaseService.
    """
    global _supabase_service_instance
    if _supabase_service_instance is None:
        _supabase_service_instance = SupabaseService()
    return _supabase_service_instance

if __name__ == '__main__':
    from dotenv import load_dotenv
    import pathlib

    env_path_project_root = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
    env_path_agent_root = pathlib.Path(__file__).resolve().parent.parent / '.env'

    if env_path_project_root.exists(): load_dotenv(dotenv_path=env_path_project_root)
    elif env_path_agent_root.exists(): load_dotenv(dotenv_path=env_path_agent_root)

    if not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY")):
        print("SKIPPING Supabase client test: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set.")
    else:
        service = get_supabase_service()

        # Create a dummy image buffer (e.g., a small transparent PNG)
        # This is a 1x1 transparent PNG in bytes
        dummy_png_buffer = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        bucket = "images" # As per project description
        file_name = f"test_upload_{uuid.uuid4()}.png"

        print(f"\nAttempting to upload dummy PNG buffer to bucket '{bucket}' as '{file_name}'...")
        public_url = service.upload_image_from_buffer(
            file_buffer=dummy_png_buffer,
            bucket_name=bucket,
            destination_path=file_name, # Explicit path
            content_type="image/png"
        )

        if public_url:
            print(f"Upload successful! Public URL: {public_url}")
            # You can try accessing this URL in a browser if your bucket is public.
        else:
            print("Upload failed.")

        print("\nAttempting to upload again with upsert=True (should work)")
        public_url_upsert = service.upload_image_from_buffer(
            file_buffer=dummy_png_buffer, # Same buffer
            bucket_name=bucket,
            destination_path=file_name, # Same path
            content_type="image/png",
            upsert=True
        )
        if public_url_upsert:
            print(f"Upsert successful! Public URL: {public_url_upsert}")
            assert public_url_upsert == public_url
        else:
            print("Upsert failed.")

        # Test get_public_url separately
        if public_url: # if first upload was successful
            retrieved_url = service.get_public_url(bucket, file_name)
            print(f"Retrieved public URL via get_public_url: {retrieved_url}")
            assert retrieved_url == public_url
        else:
            print("Skipping get_public_url test as initial upload failed.")
