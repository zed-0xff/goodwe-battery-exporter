import socket
from config import LISTEN_IP, LISTEN_PORT, HEADER_LENGTH, AES_KEY, FORWARD_ENABLED
from conversion_utils import hex_to_celsius, hex_to_soc, hex_to_battery_volt, hex_to_grid_volt_l1, hex_to_grid_volt_l2, hex_to_grid_volt_l3, hex_to_backup_volt_l1, hex_to_backup_volt_l2, hex_to_backup_volt_l3, hex_to_MPP1, hex_to_MPP2
from networking import forward_data
from encryption import decrypt_data
from log_config import setup_logging
import logging

setup_logging()  # This sets up the logging based on the configuration specified in log_config.py


def handle_connection(connection):
    try:
        with open('decrypted_data.log', 'a') as file:
            while True:
                header = connection.recv(HEADER_LENGTH)
                if len(header) < HEADER_LENGTH:
                    break

                magic, data_size_bytes, unknown, serial_number, iv, timestamp = \
                    header[:6], header[6:10], header[10:14], header[14:30], header[30:46], header[46:52]

                if magic.decode() != "POSTGW":
                    logging.error("Invalid magic value.")
                    continue

                data_size = int.from_bytes(data_size_bytes, 'big')
                data = connection.recv(data_size - 41)
                crc = connection.recv(2)
                year, month, day, hour, minute, second = [int(x) for x in timestamp]

                if FORWARD_ENABLED:
                    response = forward_data(header + data + crc)
                    logging.info(f"Forwarded data, received response: {response.hex()}")
                else:
                    logging.info("Skipped Forwarding to GoodWe")

                decrypted_data = decrypt_data(AES_KEY, iv, data)

                file.write(decrypted_data.hex() + '\n')

                logging.info("---------------------------------------------------------")
                logging.info(f"Date-Time: {day:02}-{month:02}-{2000 + year:04} {hour:02}:{minute:02}:{second:02}")
                logging.info(f"Temperature: {hex_to_celsius(decrypted_data.hex())}°C")
                logging.info(f"State of Charge: {hex_to_soc(decrypted_data.hex())}%")
                logging.info(f"Voltage of Battery: {hex_to_battery_volt(decrypted_data.hex())}V")
                logging.info(f"Grid Voltage L1: {hex_to_grid_volt_l1(decrypted_data.hex())}V")
                logging.info(f"Grid Voltage L2: {hex_to_grid_volt_l2(decrypted_data.hex())}V")
                logging.info(f"Grid Voltage L3: {hex_to_grid_volt_l3(decrypted_data.hex())}V")
                logging.info(f"Backup Voltage L1: {hex_to_backup_volt_l1(decrypted_data.hex())}V")
                logging.info(f"Backup Voltage L2: {hex_to_backup_volt_l2(decrypted_data.hex())}V")
                logging.info(f"Backup Voltage L3: {hex_to_backup_volt_l3(decrypted_data.hex())}V")
                logging.info(f"MPPT1 Voltage: {hex_to_MPP1(decrypted_data.hex())}V")
                logging.info(f"MPPT2 Voltage: {hex_to_MPP2(decrypted_data.hex())}V")

                logging.info("---------------------------------------------------------")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        connection.close()

def listen_on_port():
    """Listen on a specified port and handle connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((LISTEN_IP, LISTEN_PORT))
        sock.listen(5)
        logging.info(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
        try:
            while True:
                connection, addr = sock.accept()
                logging.info(f"Connected by {addr}")
                handle_connection(connection)
        except KeyboardInterrupt:
            logging.info("Server shutting down.")

if __name__ == "__main__":
    listen_on_port()