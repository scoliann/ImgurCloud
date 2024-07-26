

# Do imports
import argparse
import numpy as np
import pandas as pd
import cv2
import hashlib
import os
import time
from datetime import datetime
import tempfile
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request


# Do local imports
import transformations.byte_transformations as bt
import transformations.compression_transformations as cpt
import transformations.cryptographic_transformations as cgt


class ImgurCloud:

    def __init__(self,
                 t_img_shape=(1287, 1295, 3),
                 i_img_metadata_pad_default=1000,
                 fn_encompress=None, 
                 fn_decompress=None,
                 d_encompress_args={}, 
                 d_decompress_args={},
                 fn_encrypt=None, 
                 fn_decrypt=None,
                 d_encrypt_args={},
                 d_decrypt_args={},
                 s_upload_log='upload_log.csv',
                 s_timestamp_log='timestamp_log.csv',):

        # Define class variables
        self.t_img_shape = t_img_shape
        self.i_img_metadata_pad_default = i_img_metadata_pad_default
        self.fn_encompress = fn_encompress
        self.fn_decompress = fn_decompress
        self.d_encompress_args = d_encompress_args
        self.d_decompress_args = d_decompress_args
        self.fn_encrypt = fn_encrypt
        self.fn_decrypt = fn_decrypt
        self.d_encrypt_args = d_encrypt_args
        self.d_decrypt_args = d_decrypt_args
        self.s_upload_log = s_upload_log
        self.s_timestamp_log = s_timestamp_log

        # Calculate class variables
        self.i_payload_bytes_per_img = np.prod(self.t_img_shape) - self.i_img_metadata_pad_default


    def _upload(self, s_img_w_payload_subset_path, b_headless):

        # Define key variables
        s_upload_url = 'https://imgur.com/upload'

        # Set webdriver parameters
        o_option = webdriver.ChromeOptions()
        o_option.binary_location = 'browser\Win_948375_chrome-win\chrome-win\chrome.exe'
        o_option.add_experimental_option("excludeSwitches", ["enable-automation"])
        o_option.add_experimental_option('useAutomationExtension', False)
        o_option.add_argument('--disable-blink-features=AutomationControlled')
        if b_headless:
            o_option.headless = True

        # Initialize driver
        o_driver = webdriver.Chrome(executable_path='browser\chromedriver_win32\chromedriver', options=o_option)
        o_driver.maximize_window()

        # Open page
        o_driver.get(s_upload_url)

        # Upload file
        WebDriverWait(o_driver, 30).until(EC.presence_of_element_located((By.ID, 'file-input')))
        o_driver.find_element(By.ID, 'file-input').send_keys(s_img_w_payload_subset_path)

        # Get url for uploaded file
        WebDriverWait(o_driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'PostContent-imageWrapper-rounded')))
        s_img_url = ''
        f_time_slept = 0.0
        while '.png' not in s_img_url:
            s_img_url = o_driver.find_element(By.CLASS_NAME, 'PostContent-imageWrapper-rounded').find_element(By.TAG_NAME, 'img').get_attribute('src')
            time.sleep(0.1)
            f_time_slept += 0.1
            assert f_time_slept <= 30.0, \
                '\nError:\tImage url could not be found'

        # Close page
        o_driver.quit()

        # Return url for uploaded file
        return s_img_url


    def upload(self, s_payload_path, s_note, s_img_w_payload_file='file_as_image.png', b_headless=False):

        # Read in payload to bytes
        lo_payload_bytes = bt.file_to_bytes(s_payload_path)
        
        # Determine number of images required
        i_imgs_required = int(np.ceil(len(lo_payload_bytes) / float(self.i_payload_bytes_per_img)))

        # Determine number of images uploaded in current hour
        if os.path.isfile(self.s_timestamp_log):
            dt_timestamp = datetime.utcnow()
            df_timestamp_log = pd.read_csv(self.s_timestamp_log, index_col='index')
            ts_timestamps = pd.to_datetime(df_timestamp_log['upload_timestamp'])
            i_uploads_this_hour = ts_timestamps.apply(lambda x: dt_timestamp.replace(minute=0, second=0, microsecond=0) == x.replace(minute=0, second=0, microsecond=0)).sum()
            i_uploads_this_hour_remaining = 50 - i_uploads_this_hour
            assert i_uploads_this_hour_remaining >= i_imgs_required, \
                f'\nError:\t{i_uploads_this_hour} images uploaded this hour, {i_uploads_this_hour_remaining} remaining, {i_imgs_required} required'

        # Setup temp dir
        o_temp_dir = tempfile.TemporaryDirectory()

        # Parse bytes to images
        s_prior_img_url = ''
        o_tqdm = tqdm(range(i_imgs_required))
        o_tqdm.set_description('Uploading')
        for i_subset_img_idx in o_tqdm:

            # Get payload bytes subset
            lo_payload_bytes_subset_ORIG = lo_payload_bytes[i_subset_img_idx * self.i_payload_bytes_per_img: (i_subset_img_idx + 1) * self.i_payload_bytes_per_img]

            # Append prior image url bytes
            lo_prior_img_url_bytes = s_prior_img_url.encode()
            lo_payload_bytes_subset_WURL = lo_payload_bytes_subset_ORIG + lo_prior_img_url_bytes

            # Compress bytes
            lo_payload_bytes_subset_COMPRESS = self.fn_encompress(lo_payload_bytes_subset_WURL, **self.d_encompress_args)

            # Encrypt bytes
            lo_payload_bytes_subset_ENCRYPT = self.fn_encrypt(lo_payload_bytes_subset_COMPRESS, **self.d_encrypt_args)

            # Add padding
            na_payload_bytes_subset = np.frombuffer(lo_payload_bytes_subset_ENCRYPT, dtype=np.uint8)
            i_rand_pad_size_baseten = np.prod(self.t_img_shape) - len(na_payload_bytes_subset) - 6
            na_rand_pad = np.random.randint(0, 256, i_rand_pad_size_baseten, dtype=np.uint8)
            i_prior_img_url_pad_size_baseten = len(lo_prior_img_url_bytes)
            i_rand_pad_size_binary = format(i_rand_pad_size_baseten, '024b')
            na_rand_pad_size_pixel = np.array([int(i_rand_pad_size_binary[i * 8: (i + 1) * 8], base=2) for i in range(3)], dtype=np.uint8)
            na_payload_bytes_subset_w_pad = np.concatenate(
                (na_payload_bytes_subset, na_rand_pad, np.array([i_prior_img_url_pad_size_baseten]), na_rand_pad_size_pixel, np.array([i_subset_img_idx]), np.array([i_imgs_required])))
         
            # Shape into an image and save
            s_img_w_payload_subset_path = os.path.join(o_temp_dir.name, f'{i_subset_img_idx}_{s_img_w_payload_file}')
            na_img = np.reshape(na_payload_bytes_subset_w_pad, self.t_img_shape)
            cv2.imwrite(s_img_w_payload_subset_path, na_img)

            # Upload image and get url
            s_prior_img_url = self._upload(s_img_w_payload_subset_path, b_headless=False)

            # Record upload timestamp
            dt_timestamp = datetime.utcnow()
            if not os.path.isfile(self.s_timestamp_log):
                df_timestamp_log = pd.DataFrame({'upload_timestamp': [dt_timestamp], 
                                                 'payload_file': [s_payload_path], 
                                                 'image_file': [s_img_w_payload_subset_path], 
                                                 'image_url': [s_prior_img_url]})
                df_timestamp_log.index.name = 'index'
                df_timestamp_log.to_csv(self.s_timestamp_log)
            else:
                df_timestamp_log = pd.read_csv(self.s_timestamp_log, index_col='index')
                df_timestamp_log = df_timestamp_log.append({'upload_timestamp': dt_timestamp, 
                                                            'payload_file': s_payload_path, 
                                                            'image_file': s_img_w_payload_subset_path,
                                                            'image_url': s_prior_img_url}, 
                                                            ignore_index=True)
                df_timestamp_log.index.name = 'index'
                df_timestamp_log.to_csv(self.s_timestamp_log)

        # Tear down temp dir
        o_temp_dir.cleanup()

        # Record file uploaded to imgur url
        if not os.path.isfile(self.s_upload_log):
            df_upload_log = pd.DataFrame({'file': [s_payload_path], 'url': [s_prior_img_url], 'note': [s_note]})
            df_upload_log.index.name = 'index'
            df_upload_log.to_csv(self.s_upload_log)
        else:
            df_upload_log = pd.read_csv(self.s_upload_log, index_col='index')
            df_upload_log = df_upload_log.append({'file': s_payload_path, 'url': s_prior_img_url, 'note': s_note}, ignore_index=True)
            df_upload_log.index.name = 'index'
            df_upload_log.to_csv(self.s_upload_log)

        # Return url
        return s_prior_img_url


    def _download(self, s_url, s_save_path):

        # Create a Request object with the defined headers
        d_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }
        o_req = urllib.request.Request(s_url, headers=d_headers)
        
        # Open the URL and read the response
        try:
            with urllib.request.urlopen(o_req) as response:
                o_contents = response.read()
            with open(s_save_path, 'wb') as file:
                file.write(o_contents)
            print(f'Image downloaded and saved to {s_save_path}')
        except urllib.error.HTTPError as e:
            print(f'HTTP Error: {e.code} - {e.reason}')
        except urllib.error.URLError as e:
            print(f'URL Error: {e.reason}')


    def download(self, s_imgur_url, s_payload_path):

        # Setup temp dir
        o_temp_dir = tempfile.TemporaryDirectory()

        # Download images
        s_latter_img_url = s_imgur_url
        i_downloaded_img_ctr = 0
        llo_payload_bytes_subsets = []
        o_tqdm = tqdm()
        o_tqdm.set_description('Downloading')
        while True:

            # Download image
            s_img_w_payload_subset_path = os.path.join(o_temp_dir.name, f'{i_downloaded_img_ctr}_downloaded.png')
            i_downloaded_img_ctr += 1
            self._download(s_latter_img_url, s_img_w_payload_subset_path)

            # Read in image
            na_img = cv2.imread(s_img_w_payload_subset_path)

            # Remove padding
            na_payload_bytes_subset_w_pad = np.ravel(na_img)
            i_imgs_required = int(na_payload_bytes_subset_w_pad[-1])
            i_subset_img_idx = int(na_payload_bytes_subset_w_pad[-2])
            na_rand_pad_size_pixel = na_payload_bytes_subset_w_pad[-5:-2]
            i_rand_pad_size_binary = ''.join([format(i, f'08b') for i in na_rand_pad_size_pixel])
            i_rand_pad_size_baseten = int(i_rand_pad_size_binary, base=2)
            i_prior_img_url_pad_size_baseten = int(na_payload_bytes_subset_w_pad[-6])
            lo_payload_bytes_subset_ENCRYPT = na_payload_bytes_subset_w_pad[:-i_rand_pad_size_baseten - 6].tobytes()

            # Decrypt bytes
            lo_payload_bytes_subset_COMPRESS = self.fn_decrypt(lo_payload_bytes_subset_ENCRYPT, **self.d_decrypt_args)

            # Compress bytes
            lo_payload_bytes_subset_WURL = self.fn_decompress(lo_payload_bytes_subset_COMPRESS, **self.d_decompress_args)

            # Extract and update prior image url
            s_prior_img_url = lo_payload_bytes_subset_WURL[-i_prior_img_url_pad_size_baseten:].decode() if i_prior_img_url_pad_size_baseten > 0 else ''
            s_latter_img_url = s_prior_img_url
            
            # Get payload bytes subset
            lo_payload_bytes_subset_ORIG = lo_payload_bytes_subset_WURL[:-i_prior_img_url_pad_size_baseten] if i_prior_img_url_pad_size_baseten > 0 else lo_payload_bytes_subset_WURL

            # Store payload bytes subset
            llo_payload_bytes_subsets.append(lo_payload_bytes_subset_ORIG)

            # Update progress bar
            o_tqdm.total = i_imgs_required
            o_tqdm.update(i_imgs_required - i_subset_img_idx)

            # If there are no additional images, break
            if s_latter_img_url == '':
                break

        # Construct bytes of original payload
        lo_payload_bytes = b''.join(llo_payload_bytes_subsets[::-1])

        # Save payload to file
        bt.bytes_to_file(lo_payload_bytes, s_payload_path)

        # Tear down temp dir
        o_temp_dir.cleanup()


def main():

    # Read in command line arguments
    o_parser = argparse.ArgumentParser()
    o_parser.add_argument('mode', help='Whether to upload or download', type=str, choices=['upload', 'download'])
    o_parser.add_argument('source', help='Path of file to upload / Url of file to download', type=str, default=None)
    o_parser.add_argument('password', help='Password for encryption', type=str, default=None)
    o_parser.add_argument('-n', '--note', help='Note for upload log', type=str, default='')
    o_parser.add_argument('-t', '--tofile', help='Name of downloaded file', type=str, default=None)
    o_args = args = o_parser.parse_args()

    # Initialize imgur cloud object
    o_ic = ImgurCloud(t_img_shape=(1287, 1295, 3),
                      i_img_metadata_pad_default=1000,
                      fn_encompress=cpt.compress_zlib,
                      fn_decompress=cpt.decompress_zlib,
                      d_encompress_args={'i_compression_level': 9},
                      d_decompress_args={},
                      fn_encrypt=cgt.encrypt_aes,
                      fn_decrypt=cgt.decrypt_aes,
                      d_encrypt_args={'s_password': o_args.password, 'i_bit_standard': 256},
                      d_decrypt_args={'s_password': o_args.password, 'i_bit_standard': 256},
                      s_upload_log='upload_log.csv',
                      s_timestamp_log='timestamp_log.csv',)

    # Upload specified file
    if o_args.mode == 'upload':

        # Check that file exists
        assert os.path.isfile(o_args.source), \
            f'\nError:\tFile {o_args.source} does not exist'

        # Upload file
        o_ic.upload(s_payload_path=o_args.source, 
                    s_note=o_args.note,
                    s_img_w_payload_file='file_as_image.png',
                    b_headless=True)

    # Download specified file
    elif o_args.mode == 'download':

        # Check that file is specified
        assert o_args.tofile is not None, \
            '\nError:\tName for downloaded file not specified'

        # Download file
        o_ic.download(s_imgur_url=o_args.source,
                      s_payload_path=o_args.tofile)


if __name__ == '__main__':
    main()


