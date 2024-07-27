This project allows Imgur to be used for generic file hosting.

## Inspiration

After doing a steganography project, I began to wonder... Hey!  Why not just host arbitrary files on free content hosting platforms (e.g. YouTube, Imgur, SoundCloud, etc.).

Well, such a thing is possible!

## Demo
A brief video demonstrating how to run this project can be found [here](https://youtu.be/-gCJzaH8p3E)!

## Overview
The functionality provided is pretty simple, on the upload side:
1. Specified file is loaded to bytes
2. Bytes are compressed
3. Bytes are AES encrypted
4. Bytes are reformatted as the pixels of an image
5. Steps 1-4 are repeated as needed
6. Log the results

In cases where multiple images are required, each subsequent image is encoded with bytes for the URL of the preceding image:

    - Img1 <- Img2 <- ... <- ImgN
    
On the download side, the above steps are just done in reverse.


## Setup
1. Create and activate conda environment via:
```
    conda env create -f environment.yml
    conda activate env_imgur_cloud
```

2.  Chromedriver Google Chrome:

The following are the steps used to set up Google Chrome and Chromedriver on a Windows machine.  Adjust the files downloaded, and update the code as needed for Linux and Mac.

- Set up Chromedriver:
  - Go to https://chromedriver.storage.googleapis.com/index.html?path=98.0.4758.80/
  - Download `chromedriver_win32.zip` to `browser`
  - Unzip `chromedriver_win32.zip`
- Set up Google Chrome:
  - Go to https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Win/948375/
  - Download `chrome-win.zip` to `browser`
  - Unzip `chrome-win.zip`

## Execution
1. Upload content with a command like:
```
python ImgurCloud.py upload "uploads/Dido - Thank You.mp3" this_is_a_password -n "This is an example of uploading an .mp3 file that is encoded to a single .png image"
```
2. Download content with a command like:
```
python ImgurCloud.py download this_is_an_imgur_url this_is_a_password -t "downloads/Dido - Thank You.mp3 (downloaded from Imgur)"
```
Note:  The `-n` and `-t` flags allow the user to specify notes for logging.

## Miscellaneous
- Images are sized to be 5 MB.  This is because images larger than 5 MB uploaded to Imgur are converted to .jpg files, which are lossy.
- Imgur has a rate limit of uploading no more than 50 images per hour.
- This repository uses a specific version of Chrome and Chromedriver.  This can be changed by the user as needed.


