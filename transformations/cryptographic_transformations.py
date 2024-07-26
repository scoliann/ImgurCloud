'''
    This file contains function pairs that encrypt and decrypt data.
'''


# Do imports
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES


def encrypt_aes(lo_payload_bytes, s_password, i_bit_standard):

    # Check if bit standard is valid
    assert i_bit_standard in [128, 192, 256], \
        '\nError:\ti_bit_standard must be in [128, 192, 256]'

    # Define key variables
    i_num_key_bytes = int(i_bit_standard / 8)
    i_count = 100000 * i_num_key_bytes

    # Get salt and nonce values
    lo_salt_bytes = get_random_bytes(i_num_key_bytes)
    lo_nonce_bytes = get_random_bytes(i_num_key_bytes)

    # Generate key
    lo_key_bytes = PBKDF2(s_password, lo_salt_bytes, i_num_key_bytes, i_count, hmac_hash_module=SHA512)
    
    # Encrypt
    o_cipher = AES.new(lo_key_bytes, AES.MODE_EAX, nonce=lo_nonce_bytes)
    lo_encrypted_bytes = o_cipher.encrypt(lo_payload_bytes)

    # Compose output
    lo_encrypted_bytes = lo_salt_bytes + lo_nonce_bytes + lo_encrypted_bytes

    # Return
    return lo_encrypted_bytes


def decrypt_aes(lo_payload_bytes, s_password, i_bit_standard):

    # Check if bit standard is valid
    assert i_bit_standard in [128, 192, 256], \
        '\nError:\ti_bit_standard must be in [128, 192, 256]'

    # Define key variables
    i_num_key_bytes = int(i_bit_standard / 8)
    i_count = 100000 * i_num_key_bytes

    # Decompose input
    lo_salt_bytes = lo_payload_bytes[:i_num_key_bytes]
    lo_nonce_bytes = lo_payload_bytes[i_num_key_bytes: 2 * i_num_key_bytes]
    lo_payload_bytes = lo_payload_bytes[2 * i_num_key_bytes:]

    # Generate key
    lo_key_bytes = PBKDF2(s_password, lo_salt_bytes, i_num_key_bytes, i_count, hmac_hash_module=SHA512)

    # Decrypt
    o_cipher = AES.new(lo_key_bytes, AES.MODE_EAX, nonce=lo_nonce_bytes)
    lo_decrypted_bytes = o_cipher.decrypt(lo_payload_bytes)

    # Return
    return lo_decrypted_bytes


