from communication import *

def menu():
    print("Select one of the following commands:")
    print("1) Get data from a file")
    print("2) Stream data")
    print("3) Parse the data you got")
    print("4) Exit")

if __name__ == "__main__":
    ports = serial.tools.list_ports.comports()
    stm_port = ''

    if len(ports) == 1:
        stm_port = ports[0].device
    else:
        stm_port = input("Please enter the port where your STM32 is connected")

    data = b''

    try:
        device = STM32(stm_port)

        while True:
            menu()

            choice = int(input())

            if choice == 1:
                device.send_command("LIST")

                print(device.receive_data(1024).decode('utf-8'))

                fileName = input("Enter file name (n to cancel): ")

                if fileName == 'n'or fileName == 'N':
                    continue
                
                data = device.receive_file(fileName)
            elif choice == 2:
                device.send_command("STREAM")

                i = 0
                while i < 5:
                    print(device.receive_line())
                    i += 1

                device.send_command("OFF")
            elif choice == 3:
                if len(data) == 0:
                    print("Load data first then parse :)")
                    continue

                print(STM32.parse_data(data))
            elif choice == 4:
                break

    except serial.SerialException as e:
        print(f"Something wrong: {e}")

    finally:
        if 'device.ser' in locals() and device.ser.is_open:
            device.ser.close()
            print("Port closed")