# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import zmq
import socket
import json
import struct
import threading
import argparse

def zmq_to_tcp(zmq_host, zmq_port, tcp_host, tcp_port):
    context = zmq.Context()
    zmq_socket = context.socket(zmq.SUB)
    zmq_socket.connect(f"tcp://{zmq_host}:{zmq_port}")
    zmq_socket.setsockopt_string(zmq.SUBSCRIBE, "")

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((tcp_host, tcp_port))
    tcp_socket.listen(5)

    print(f"TCP server listening on {tcp_host}:{tcp_port}")

    def handle_client(client_socket):
        try:
            while True:
                message = zmq_socket.recv_json()
                print(f"Received JSON: {message}")

                # Convert the message to the ANTSDR format
                antsdr_data = convert_to_antsdr_format(message)
                if antsdr_data:
                    # Send the converted data to the client
                    client_socket.sendall(antsdr_data)
        except zmq.error.ContextTerminated:
            print("ZMQ context terminated")
        except Exception as e:
            print(f"Error in handle_client: {e}")
        finally:
            client_socket.close()
            print("Closed client connection")

    while True:
        client_socket, addr = tcp_socket.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

def parse_float(value):
    try:
        # Remove any units or extraneous characters
        return float(value.split()[0])
    except (ValueError, AttributeError):
        return 0.0

def convert_to_antsdr_format(data):
    try:
        antsdr_frame = bytearray()

        # Header
        header = 0x0001
        antsdr_frame.extend(struct.pack('<H', header))

        # Packet type
        packet_type = 0x01
        antsdr_frame.append(packet_type)

        # Placeholder for length
        antsdr_frame.extend((0).to_bytes(2, 'little'))

        # Data (ANTSDR struct format)
        serial = b'\x00' * 64
        device_type = b'\x00' * 64
        device_type_8 = 0
        app_lat = app_lon = drone_lat = drone_lon = height = altitude = home_lat = home_lon = freq = speed_e = speed_n = speed_u = 0.0
        rssi = 0

        for item in data:
            if "Basic ID" in item:
                basic_id = item["Basic ID"]
                if basic_id.get("id_type") == "Serial Number (ANSI/CTA-2063-A)":
                    serial = basic_id.get("id", "").ljust(64, '\x00')[:64].encode('utf-8')
                device_type = basic_id.get("ua_type", "").ljust(64, '\x00')[:64].encode('utf-8')
                device_type_8 = 1

            if "Location/Vector Message" in item:
                loc_msg = item["Location/Vector Message"]
                drone_lat = parse_float(loc_msg.get("latitude", 0.0))
                drone_lon = parse_float(loc_msg.get("longitude", 0.0))
                height = parse_float(loc_msg.get("height_agl", 0.0))
                altitude = parse_float(loc_msg.get("geodetic_altitude", 0.0))
                speed_e = parse_float(loc_msg.get("speed", 0.0))
                speed_u = parse_float(loc_msg.get("vert_speed", 0.0))

            if "System Message" in item:
                sys_msg = item["System Message"]
                app_lat = parse_float(sys_msg.get("latitude", 0.0))
                app_lon = parse_float(sys_msg.get("longitude", 0.0))
                home_lat = parse_float(sys_msg.get("latitude", 0.0))
                home_lon = parse_float(sys_msg.get("longitude", 0.0))
                altitude = parse_float(sys_msg.get("geodetic_altitude", 0.0))

        antsdr_frame.extend(serial)
        antsdr_frame.extend(device_type)
        antsdr_frame.append(device_type_8)

        antsdr_frame.extend(struct.pack('<d', app_lat))
        antsdr_frame.extend(struct.pack('<d', app_lon))
        antsdr_frame.extend(struct.pack('<d', drone_lat))
        antsdr_frame.extend(struct.pack('<d', drone_lon))
        antsdr_frame.extend(struct.pack('<d', height))
        antsdr_frame.extend(struct.pack('<d', altitude))
        antsdr_frame.extend(struct.pack('<d', home_lat))
        antsdr_frame.extend(struct.pack('<d', home_lon))
        antsdr_frame.extend(struct.pack('<d', freq))
        antsdr_frame.extend(struct.pack('<d', speed_e))
        antsdr_frame.extend(struct.pack('<d', speed_n))
        antsdr_frame.extend(struct.pack('<d', speed_u))
        antsdr_frame.extend(struct.pack('<I', rssi))

        # Update length
        length = len(antsdr_frame) - 5
        antsdr_frame[3:5] = struct.pack('<H', length)

        return bytes(antsdr_frame)
    except Exception as e:
        print(f"Error converting to ANTSDR format: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ZMQ to TCP proxy for converting drone data to ANTSDR format.")
    parser.add_argument("--zmq-host", default="127.0.0.1", help="ZMQ server host")
    parser.add_argument("--zmq-port", type=int, default=12345, help="ZMQ server port")
    parser.add_argument("--tcp-host", default="0.0.0.0", help="TCP proxy host")
    parser.add_argument("--tcp-port", type=int, default=9876, help="TCP proxy port")
    args = parser.parse_args()

    zmq_to_tcp(args.zmq_host, args.zmq_port, args.tcp_host, args.tcp_port)
