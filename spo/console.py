from communication import *

def menu():
    print("Select one of the following commands:")
    print("1) Help screen")
    print("2) List files")
    print("3) Get data from a file")
    print("4) Exit")

if __name__ == "__main__":
    ports = serial.tools.list_ports.comports()
    stm_port = ''

    if len(ports) == 1:
        stm_port = ports[0].device

    try:
        device = STM32(stm_port)

        while True:
            menu()

            choice = int(input())

            if choice == 1  or choice == 2:
                device.send_command("HELP" if choice == 1 else "LIST")

                print(device.receive_data(1024).decode('utf-8'))
            elif choice == 3:
                fileName = input("Enter file name: ")
                
                print(device.receive_file(fileName))
            elif choice == 4:
                break

    except serial.SerialException as e:
        print(f"Something wrong: {e}")

    finally:
        if 'device.ser' in locals() and device.ser.is_open:
            device.ser.close()
            print("Port closed")