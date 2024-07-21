
# SniffleToKismet

SniffleToKismet is a proxy tool that bridges the gap between the Sniffle Bluetooth 5 long range extended sniffing and Kismet's ANTSDR capture mechanism. This tool allows users to utilize a Sniffle compatible dongle to detect Bluetooth 5 long range extended packets and relay them to Kismet through a ZMQ to TCP proxy.

## Features
- Leverages the Sniffle fork from [Sniffle GitHub](https://github.com/bkerler/Sniffle).
- Supports ZeroMQ (ZMQ) for data transmission.
- Converts ZMQ messages to a format compatible with Kismet's ANTSDR capture tool.
- Provides seamless integration with Kismet for enhanced drone detection and monitoring.

## Requirements
- Sniffle compatible dongle
- Kismet
- Python 3

## Setup and Usage

1. Clone the Sniffle fork:
   ```sh
   git clone https://github.com/bkerler/Sniffle
   ```

2. Run the Sniffle receiver:
   ```sh
   python3 Sniffle/python_cli/sniff_receiver.py -l -e -z --zmqhost 0.0.0.0 --zmqport 12345
   ```
   This command configures the Sniffle dongle to look for Bluetooth 5 long range extended packets.

3. Start the SniffleToKismet proxy with the correct ZMQ details:
   ```sh
   python3 zmq_to_tcp_proxy.py --zmq-host 0.0.0.0 --zmq-port 12345 --tcp-host 0.0.0.0 --tcp-port 9876
   ```

4. Start the Kismet capture tool:
   ```sh
   kismet_cap_antsdr_droneid --source antsdr-droneid:host=0.0.0.0,port=9876 --connect localhost:3501 --tcp
   ```

## How It Works
- The Sniffle compatible dongle captures Bluetooth 5 long range extended packets.
- The captured packets are sent to the Sniffle receiver script which forwards them via ZeroMQ (ZMQ).
- The SniffleToKismet proxy receives the ZMQ messages and translates them into a format compatible with Kismet's ANTSDR capture tool.
- Kismet processes the data and provides enhanced drone detection and monitoring.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
