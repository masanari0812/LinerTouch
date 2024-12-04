import serial
import time

ser = serial.Serial("COM9", 115200, timeout=0.1)


def diagnostic_read():
    start_time = time.time()
    total_bytes = 0

    try:
        while time.time() - start_time < 5:  # 5秒間テスト
            data = ser.read(1024)
            if data:
                total_bytes += len(data)
                print(f"Received {len(data)} bytes")
            else:
                print("No data received")
            time.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")

    print(f"Total bytes received in 5 seconds: {total_bytes}")


diagnostic_read()
ser.close()
