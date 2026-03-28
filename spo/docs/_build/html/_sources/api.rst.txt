API Reference
=============

STM32 Class
-----------

.. autoclass:: communication
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
   :noindex:

Methods
-------
.. automethod:: communication.STM32.__init__
.. automethod:: communication.STM32.send_command
.. automethod:: communication.STM32.receive_line
.. automethod:: communication.STM32.receive_data
.. automethod:: communication.STM32.receive_file
.. automethod:: communication.STM32.unstuff
.. automethod:: communication.STM32.crc16_update
.. automethod:: communication.STM32.crc16_compute
.. automethod:: communication.STM32.parse_packet
.. automethod:: communication.STM32.parse_data

Constants
---------

.. data:: STM32.CRC16_POLY
   :type: int
   :value: 0xA001
   
   CRC-16/Modbus polynomial in reflected form.