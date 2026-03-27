# CB_api_client

Client to connect to PythonAnywhere API for ZIP file upload and download

## setup - create `.env`

Create a `.env` with the URL and upload user credentials.


## simplest use `upload.py`

**Usage**        
```commandline
  python upload.py /path/to/yourfile.zip   
```

here is it in action:

```bash
% python upload.py ./files_to_upload/routes.zip

  POST https://drmattsmith.pythonanywhere.com/api/upload/
Success: 'routes.zip' uploaded (ID: 4, 2393 bytes)
```


## CLI menu script

there is an interactive menu script to make it easy to list files available to download, and to upload files from the `files_to_upload` directory.

here is it in action:

```bash
    % python menu.py
    
    --- File Upload API ---
      1 - List all files
      2 - Download a file
      3 - Upload a file
      0 - Exit
    
    Select option: 1
      GET https://drmattsmith.pythonanywhere.com/api/files/
    
    ID           Size  Uploaded                Filename
    ----------------------------------------------------------------------
    1            2.4K  2026-03-27 10:29:31     Week12.zip
    2           10.4K  2026-03-27 10:34:10     06_data_cleaning.zip
    4            2.3K  2026-03-27 10:42:10     routes_ApIO4jL.zip
    
    
    --- File Upload API ---
      1 - List all files
      2 - Download a file
      3 - Upload a file
      0 - Exit
```
