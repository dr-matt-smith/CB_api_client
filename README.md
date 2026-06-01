# Celbridge-hub-api-client

Client to connect to Celbridge-hub API for ZIPed package upload and download
- (see **celbridge-hub** package API server: https://github.com/celbridge-org/celbridge-hub)

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

### top-level menu

```bash
    % python menu.py
    
    === Packages API ===
      1 - Packages    (list / show / register / delete)
      2 - Versions    (list / detail / upload / download / tombstone)
      3 - Aliases     (list / set / remove)
      4 - History     (full / as-of-version)
      5 - Download latest version        (GET  /api/packages/{name}/latest)
      6 - Upload a package               (POST /api/packages/{name}/versions)
      0 - Exit
    
    Select option: 
```

### example session exploring menu options


```bash
    % python menu.py 
    
    === Packages API ===
      1 - Packages    (list / show / register / delete)
      2 - Versions    (list / detail / upload / download / tombstone)
      3 - Aliases     (list / set / remove)
      4 - History     (full / as-of-version)
      5 - Download latest version        (GET  /api/packages/{name}/latest)
      6 - Upload a package               (POST /api/packages/{name}/versions)
      0 - Exit
    
    Select option: 1
    
    --- Packages ---
      1 - List all packages              (GET    /api/packages)
      2 - Show package metadata          (GET    /api/packages/{name})
      3 - Register a new (empty) package (POST   /api/packages)
      4 - Delete entire package          (DELETE /api/packages/{name})
      0 - Back
    
    Select option: 1
      GET https://drmattsmith.pythonanywhere.com/api/packages/
    
    Name                           Type        Latest  Author               Uploaded
    ------------------------------------------------------------------------------------------
    fred-chess                     page             2  popeye               2026-05-09 14:19:01
    space-chess24                  page             1  chris                2026-05-09 14:22:26
    
    
    --- Packages ---
      1 - List all packages              (GET    /api/packages)
      2 - Show package metadata          (GET    /api/packages/{name})
      3 - Register a new (empty) package (POST   /api/packages)
      4 - Delete entire package          (DELETE /api/packages/{name})
      0 - Back
    
    Select option: 2
      GET https://drmattsmith.pythonanywhere.com/api/packages/
    
      1. fred-chess (latest v2)
      2. space-chess24 (latest v1)
    
    Enter number (or press Enter to cancel): 1
      GET https://drmattsmith.pythonanywhere.com/api/packages/fred-chess/
    
    Package: fred-chess
    Type:    page
    
     Ver  Author               Uploaded               Tomb  Summary
    ------------------------------------------------------------------------------------------
       2  popeye               2026-05-09 14:19:01          added feature - should become version 2
       1  mattilda             2026-05-09 14:11:38          forked to create new package fred-chess
    
    
    --- Packages ---
      1 - List all packages              (GET    /api/packages)
      2 - Show package metadata          (GET    /api/packages/{name})
      3 - Register a new (empty) package (POST   /api/packages)
      4 - Delete entire package          (DELETE /api/packages/{name})
      0 - Back
    
    Select option: 0
    
    === Packages API ===
      1 - Packages    (list / show / register / delete)
      2 - Versions    (list / detail / upload / download / tombstone)
      3 - Aliases     (list / set / remove)
      4 - History     (full / as-of-version)
      5 - Download latest version        (GET  /api/packages/{name}/latest)
      6 - Upload a package               (POST /api/packages/{name}/versions)
      0 - Exit
    
    Select option: 4
    
    --- History ---
      1 - Show full package history      (GET /api/packages/{name}/history)
      2 - Show history as-of a version   (GET /api/packages/{name}/versions/{n}/history)
      0 - Back
    
    Select option: 1
      GET https://drmattsmith.pythonanywhere.com/api/packages/
    
      1. fred-chess (latest v2)
      2. space-chess24 (latest v1)
    
    Enter number (or press Enter to cancel): 1
      GET https://drmattsmith.pythonanywhere.com/api/packages/fred-chess/history/
    
    # Package History: fred-chess
    
    > Authoritative copy lives on the server. This file is a snapshot at publish time.
    
    ## Versions
    
    ### Version 2
    
    - **Author:** popeye
    - **Date:** 2026-05-09T14:19:01Z
    - **Hash:** sha256:e5bcd8581062c95a72fe63ab4f850040abb9d90d0467a33e75e687f7769bc474
    - **Message:** added feature - should become version 2
    
    ### Version 1
    
    - **Author:** mattilda
    - **Date:** 2026-05-09T14:11:38Z
    - **Hash:** sha256:36d431fba38dc200339b889f90145ff5ca83f134635a6de4d810640d031a9db7
    - **Message:** forked to create new package fred-chess

```

