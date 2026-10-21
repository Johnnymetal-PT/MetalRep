# PG Product Update - OneDrive Configuration

This module syncs product data from a OneDrive folder before processing it. To enable the OneDrive integration, set the following environment variables:

```
ONEDRIVE_CLIENT_ID=<your client id>
ONEDRIVE_CLIENT_SECRET=<your client secret>
ONEDRIVE_TENANT_ID=<your tenant id>
ONEDRIVE_DRIVE_ID=<drive id>
ONEDRIVE_ROOT_PATH=<folder path>
```

When these variables are present, the module downloads the contents of `ONEDRIVE_ROOT_PATH` from the specified drive into a temporary directory for processing. If they are not set, the module falls back to reading from `/mnt/partilha_geral/PRODUTOS`.

Example values provided by the user:

```
export ONEDRIVE_CLIENT_ID="9eae2510-40b9-49b4-a95e-3fe633684fe9"
export ONEDRIVE_CLIENT_SECRET="RPc8Q~qtk.iYPP8-HwAQc3Qci~o9ncEtzk9YwcC3"
export ONEDRIVE_TENANT_ID="b681312c-3365-4515-837e-af39ea3f25c4"
export ONEDRIVE_DRIVE_ID="1646a2df-ac76-4d2d-8baa-f1423f9f6b0b"
export ONEDRIVE_ROOT_PATH="Documents/PRODUTOS"
```

Optionally, set `DELETE_LOCAL_FILES_AFTER_UPLOAD` to `True` if you want the script to remove local files after they have been uploaded to Odoo.
