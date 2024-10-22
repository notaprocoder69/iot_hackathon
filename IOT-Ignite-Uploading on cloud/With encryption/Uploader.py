import time
import random
import csv
import shadow_pb2
import data_pb2
import numpy as np

#shadow = shadow_pb2.Shadow()

Ultrasonic = data_pb2.Ultrasonic_Datapoint_3()
#aqi.pm10 = 18.9
#aqi.temperature = 27.9
#aqi.humidity = 80.1

device = GolainClient(None)
device.connect()
device.client.loop_start()

def shadowCallback(data):
  print(f'received shadow data: {data}')
  #newShadow = shadow_pb2.Shadow()
  #newShadow.ParseFromString(data)
  #print(newShadow)

device.setShadowCallback(shadowCallback)
# device._publish(f'/{device.root_topic}/{device.device_name}/device-shadow/u', shadow.SerializeToString())


while True:
    with open('sha-256.csv', mode='r') as file:
        # Create a CSV reader
        csv_reader = csv.reader(file)

        # Skip the header row
        next(csv_reader)

        # Iterate over each row in the CSV
        for row in csv_reader:
            # Extract data
            Ultrasonic.hash = row[1]
            timestamp_ms = int(row[2])
            Ultrasonic.time_stamp = timestamp_ms // 1000  # Convert ms to seconds

            # Create a data dictionary

                # "ultra": distance,
                # "mac_address": mac_address,
                # "timestamp": timestamp
            #print(Ultrasonic)

            #print(str(Ultrasonic))

            # Publish the data
            device.publishData('Ultrasonic_Datapoint_3', Ultrasonic.SerializeToString())

            # Sleep for 1 second
            time.sleep(1)