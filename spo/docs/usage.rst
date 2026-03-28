Usage Guide
===========

Basic Usage
-----------

.. code-block:: python

   from communication import STM32
   
   # Initialize connection
   device = STM32(port='COM3')  # Windows
   # device = STM32(port='/dev/ttyUSB0')  # Linux
   
   # Send command
   device.send_command("GET data.bin")
   
   # Receive file data
   data = device.receive_data(1024)
   
   # Parse packets
   packets = STM32.parse_data(data)
   
   # Process packets
   for packet in packets:
       if packet:
           print(f"Timestamp: {packet['timestamp']}")
           for chunk_id, samples in packet['chunks'].items():
               print(f"  Chunk {chunk_id}: {len(samples)} samples")

Working with Chunks
-------------------

Chunks contain sensor data in different formats:

.. code-block:: python

   # Access specific chunk types
   accel_samples = packet['chunks'].get(1, [])  # Accelerometer
   gyro_samples = packet['chunks'].get(2, [])   # Gyroscope
   temp_samples = packet['chunks'].get(3, [])   # Temperature
   
   # Iterate through samples
   for x, y, z in accel_samples:
       print(f"X: {x}, Y: {y}, Z: {z}")

Error Handling
--------------

The parser automatically handles errors:

.. code-block:: python

   packets = STM32.parse_data(raw_data)
   
   for i, packet in enumerate(packets):
       if packet is None:
           print(f"Packet {i} is invalid (CRC mismatch)")
           continue
       
       # Process valid packet
       print(f"Valid packet {i}: {packet['timestamp']}")

Multiple Packets
----------------

When receiving multiple packets in one buffer:

.. code-block:: python

   # Receive multiple packets
   data = device.receive_data(4096)
   
   # Parse all packets
   packets = STM32.parse_data(data)
   
   # Filter valid packets
   valid_packets = [p for p in packets if p is not None]
   print(f"Found {len(valid_packets)} valid packets")