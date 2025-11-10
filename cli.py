from parking_system.core import ParkingLot
from parking_system.persistence import save_parking, load_parking
import sys

DATA_FILE = 'sample_data.json'

def print_menu():
    print('\nSmart Parking Management - CLI')
    print('1) Park Vehicle')
    print('2) Remove Vehicle')
    print('3) Display Status')
    print('4) List Parked Vehicles')
    print('5) Save & Exit')
    print('6) Exit without saving')

def main():
    pl = load_parking(DATA_FILE) or ParkingLot()
    print('Smart Parking System started.')
    while True:
        print_menu()
        choice = input('Choose an option: ').strip()
        if choice == '1':
            num = input('Vehicle number: ')
            vtype = input('Vehicle type (2W/4W/TR): ')
            ok, msg = pl.park_vehicle(num, vtype)
            print(msg)
        elif choice == '2':
            ident = input("Enter vehicle number or slot (e.g., '4W:3'): ")
            ok, msg, fee = pl.remove_vehicle(ident)
            print(msg)
        elif choice == '3':
            for t, v in pl.status_summary().items():
                print(f"{t}: total={v['total']}, occupied={v['occupied']}, available={v['available']}")
        elif choice == '4':
            for p in pl.list_parked():
                print(p)
        elif choice == '5':
            save_parking(DATA_FILE, pl)
            print('Saved successfully.')
            sys.exit(0)
        elif choice == '6':
            print('Exiting without saving.')
            sys.exit(0)
        else:
            print('Invalid choice.')

if __name__ == '__main__':
    main()
