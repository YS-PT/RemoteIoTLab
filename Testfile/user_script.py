from machine import Pin
import time

led1 = Pin(3, Pin.OUT)  # GPIO3 as output

start_time = time.time()

while time.time() - start_time < 10:  # Run for 10 seconds
    led1.value(1)
    time.sleep(0.5)
    led1.value(0)
    time.sleep(0.5)

print("✅ Done blinking for 10 seconds.")