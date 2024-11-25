<h1 align="center">AutoMate</h1>

<div align="center">

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/OldManny/AutoMate/main.svg)](https://results.pre-commit.ci/latest/github/OldManny/AutoMate/main)

</div>

This tool is designed to automate various tasks such as organizing files, sending emails, and automating data entry. It is built using Python and PyQt5 for the user interface.

<p align="center">
  <img src="images/MainInterface.png" alt="Main Interface" />
</p>


# Table of Contents

- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
  - [Organize Files](#organize-files)
  - [Send Email](#send-emails)
  - [Data Entry](#automate-data-entry)
- [Undo Last Action](#undo-last-action)
- [Testing](#testing)
- [Attribution](#attribution)


## Features

- **File Organization**: Sort files by type, date, size, detect duplicates, rename, compress, and backup files.
- **Email Sending**: Easily send emails with attachments immediately or schedule them for later.
- **Data Entry Automation**: Automate data entry for CSV, Excel, and PDF files.
- **User-Friendly Interface**: Easy-to-use interface built with PyQt5.


## Setup

1. **Clone the repository**

    ```sh
    git clone https://github.com/OldManny/AutoMate.git
    cd AutoMate
    ```

2. **Create a virtual environment**

    ```sh
    python3 -m venv .venv
    ```

3. **Activate the virtual environment**

    ```sh
    source venv/bin/activate  # On Windows use `.\venv\Scripts\activate`
    ```

4. **Install the dependencies**

    ```sh
    pip install -r requirements.txt
    ```

5. **Set up environment variables**

    Create a `.env` file in the root directory and add your API credentials and the src folder path. More instructions to come, once the Email automation feature is implemented.



## Usage


### Organize Files (Under Development and NOT released yet)

1. Click on "Organize Files" to open the file organization customization dialog.

2. **Sort by Type**: Move files into directories based on their file type (e.g., images, documents).

3. **Sort by Date**: Organize files by their modification date.

4. **Sort by Size**: Group files into categories based on their size.

5. **Detect Duplicates**: Identify and move duplicate files to a "duplicates" directory.

6. **Rename Files**: Rename files based on a specific pattern.

7. **Compress Files**: Compress all files into a single ZIP archive.

8. **Backup Files**: Create a backup of all files.

<p align="center">
  <img src="images/OrganizeFiles.png" alt="Main Interface" />
</p>


### Send Email

**Under Development**


### Data Entry

**Under Development**


## Undo Last Action

Both the Organize Files and Automate Data Entry dialogs will include an "Undo Last Action" button. This feature allows reverting to the last operation performed. If something is done accidentally, it is easy to undo these actions and restore to the previous state.


## Testing

**Under Development**


## Attribution

- Photo by [Dariusz Sankowski](https://unsplash.com/@dariuszsankowski) on [Unsplash](https://unsplash.com/photos/3OiYMgDKJ6k)
- Icons from [Freepik](https://www.freepik.com/):
    - [Favourite folder icon](https://www.freepik.com/icon/favourite-folder_11471618#fromView=search&page=1&position=42&uuid=622cae6d-d6fe-404e-b11b-ecc936850666) by [juicy_fish](https://www.freepik.com/author/juicy-fish/icons)
    - [Folder icon](https://www.freepik.com/icon/folder_5656334#fromView=search&page=2&position=44&uuid=cdb3aadb-5903-44e2-9587-04d09fab2e19) by [Uniconlabs](https://www.freepik.com/author/batitok/icons)
