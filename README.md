# Tablo tools

This repository contains some simple python scripts for archiving recordings stored on a Tablo PVR.

The scripts maintain an index of the recordings stored on the PVR and the metadata associated with each recording. Recordings are streamed from the Tablo to a filesystem of the users choosing. (The filesystem must be mounted by the local system.)

These scripts are still very premature. In order to use them on your own you will have to make some modifications.

- There is a constant `base_url` defined at the beginning of `tablo/api.py` that defines the IP address of the server. You will need to update that variable to the IP address of your tablo device.
- You may want to update `default_recording_repository` in `tablo_util.py`, otherwise you will have to specify the repository path as a command line argument.
- Recordings are archived to the user specified path. The files are structured and formatted so that they can be recognized by Plex Media Server. If this format is not suitable you will have to update `tablo.api.get_recording_path` as needed.

There are two basic command available with the utility. There is a command to list the recordings in the library, and there is a command to archive new recordings.

##Archiving recordings

```
$ python tablo_util.py record new
```

This command retrieves the list of recordings from the Tablo REST server, updates the library and archives recordings that have not previously been archived. (Recordings are structured and formatted so they are recognized by Plex Media Server.) Run this command periodically to keep your archives up to date.

##Listing the library contents

```
$ python tablo_util.py library list
```

This command lists the contents of the library. By default a summary is listed for each recording. Specify `--full` to list more details about each recording.
