from multi_sensor_correlation_engine import main
from space_weather_engine import App
import sys
import os

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

running = True
while running:
    clear_console()
    print("|| ===== SCIENTIFIC SIGNAL ANALYSIS TOOLKIT ===== ||")

    print("Welcome to the Scientific Signal Analysis Toolkit.\n"
          "Please select a module to initiate: \n")
    print("1. Multi-Sensor Correlation Engine")
    print("2. Multi-Sensor Space Weather Engine")
    print("3. Exit")

    data = input("> ")

    if not data.isdigit():
        print("[!] Error! Invalid input")
        continue

    choice = int(data)

    if choice == 1:
        try:
            clear_console()
            main()
        except KeyboardInterrupt:
            print("\n[INFO] Terminating engine...")
            print("\n[INFO] Returning to main menu...")
            continue
    elif choice == 2:
        try:
            clear_console()
            App()
        except KeyboardInterrupt:
            print("\n[INFO] Terminating engine...")
            print("\n[INFO] Returning to main menu...")
            continue
    elif choice == 3:
        sys.exit()
    else:
        print("[!] Error! Invalid input")
