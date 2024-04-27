#!/usr/bin/env python3
import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def decrypt_data(key, iv, data):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(data) + decryptor.finalize()
    return decrypted_data


def handle_connection(connection):
    try:
        while True:
            header = connection.recv(52)  # Attempt to read the header
            if len(header) < 52:
                break  # End of data or incomplete header

            magic, data_size_bytes, unknown, serial_number, iv, timestamp = \
                header[:6], header[6:10], header[10:14], header[14:30], header[30:46], header[46:52]

            if magic.decode() != "POSTGW":
                print("Error: File does not start with the expected magic value.")
                continue

            data_size = int.from_bytes(data_size_bytes, 'big')
            data = connection.recv(data_size - 41)  # Read the data part
            crc = connection.recv(2)  # Read the CRC

            year, month, day, hour, minute, second = timestamp

            print(f"magic   : {magic.decode()}")
            print(f"data_sz : {data_size}")
            print(f"unknown : {unknown.hex()}")
            print(f"s/n     : {serial_number.decode()}")
            print(f"iv      : {iv.hex()}")
            print(f"time    : {2000 + year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}")

            key = b'\xFF' * 16
            decrypted_data = decrypt_data(key, iv, data)

            print("data    :", decrypted_data.hex())
            print("crc     :", crc.hex())
            print()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()


def listen_on_port(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen(5)
    print(f"Listening on {ip}:{port}")

    try:
        while True:
            connection, addr = sock.accept()
            print(f"Connected by {addr}")
            handle_connection(connection)
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        sock.close()


if __name__ == "__main__":
    listen_on_port('0.0.0.0', 20001)
