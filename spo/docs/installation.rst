Installation
============

Prerequisites
-------------

- Python 3.8.10 or higher
- pip package manager

Installation Steps
------------------

1. Install the required dependency:

.. code-block:: bash

   pip install pyserial

2. Copy the ``communication.py`` module to your project directory.

3. Import the module in your Python code:

.. code-block:: python

   from communication import STM32

Verifying Installation
----------------------

Run the following test to verify everything works:

.. code-block:: python

   from communication import STM32
   
   # Test CRC calculation (should output 0x4B37)
   crc = STM32.crc16_compute(b'123456789')
   print(f"CRC: 0x{crc:04X}")