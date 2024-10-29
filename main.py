import time
from pimoroni import RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
from pimoroni_i2c import PimoroniI2C

# Initialize the display for Pico Display Pack 2.8" (320x240 resolution)
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)

# Disable the RGB LED on the Pico Display
rgb_led = RGBLED(26, 27, 28) #the RGB LED is hooked up to different pins on 2.8" 
rgb_led.set_rgb(0, 0, 0)  # Turn off the LED

# Set the font to bitmap8
display.set_font("bitmap8")

# Set display dimensions for Pico Display Pack 2.8"
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

# Define colors
dark_blue_pen = display.create_pen(0, 0, 100)  # Dark blue for menu background
white_pen = display.create_pen(255, 255, 255)  # White for text and outlines
green_pen = display.create_pen(0, 255, 0)      # Green for low values
yellow_pen = display.create_pen(255, 255, 0)   # Yellow for medium values
orange_pen = display.create_pen(255, 165, 0)   # Orange for high values
red_pen = display.create_pen(255, 0, 0)        # Red for max values
black_pen = display.create_pen(0, 0, 0)        # Black for clearing the display on the right side

# Initialize I2C and sensors
i2c = PimoroniI2C(sda=4, scl=5)
bme280 = BreakoutBME280(i2c)
ltr559 = BreakoutLTR559(i2c)
motion_sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)

# Define sensor titles
sensor_titles = [
    "Temperature", "Pressure", "Humidity", 
    "Light", "Proximity", "Orientation", "Motion"
]

temperature, pressure, humidity, light, proximity = 0, 0, 0, 0, 0
orientation = (0, 0, 0)  # Will now hold `Gx`, `Gy`, `Gz` values
motion = (0, 0, 0)       # Will now hold `Ax`, `Ay`, `Az` values

# Set max values for bar scaling
GYRO_MAX = 250.0  # Cap for Gx, Gy, Gz
ACCEL_MAX = 5.0   # Cap for Ax, Ay, Az

# Adjustments for layout
TITLE_WIDTH_REDUCTION = 30
x_offset = int(DISPLAY_WIDTH // 2 - TITLE_WIDTH_REDUCTION + 10)  # Shifted x starting point for sensor bars
max_bar_width = int(DISPLAY_WIDTH // 2 - TITLE_WIDTH_REDUCTION - 40)  # Adjusted max bar width

def set_bar_color(value, max_value):
    """Determine the color of the bar based on the value's percentage of max_value."""
    percentage = value / max_value
    if percentage < 0.25:
        return green_pen
    elif percentage < 0.5:
        return yellow_pen
    elif percentage < 0.75:
        return orange_pen
    else:
        return red_pen

def draw_sensor_titles():
    display.set_pen(dark_blue_pen)  # Set background color to dark blue
    display.clear()  # Clear the entire display

    item_spacing = DISPLAY_HEIGHT // len(sensor_titles)

    # Loop through titles and display them on the left
    for i, title in enumerate(sensor_titles):
        display.set_pen(white_pen)  # Set pen to white for text
        display.text(title, 10, int(i * item_spacing) + 10, scale=2)

    # Draw black background on the adjusted right side
    display.set_pen(black_pen)
    display.rectangle(int(DISPLAY_WIDTH // 2 - TITLE_WIDTH_REDUCTION), 0, int(DISPLAY_WIDTH // 2 + TITLE_WIDTH_REDUCTION), DISPLAY_HEIGHT)
    
    display.update()  # Ensure initial display of titles

def display_sensor_values():
    global temperature, pressure, humidity, light, proximity, orientation, motion

    # Clear the right side of the display to avoid overlapping from previous updates
    display.set_pen(black_pen)
    display.rectangle(int(DISPLAY_WIDTH // 2 - TITLE_WIDTH_REDUCTION), 0, int(DISPLAY_WIDTH // 2 + TITLE_WIDTH_REDUCTION), DISPLAY_HEIGHT)

    # Read BME280 sensor data
    bme_reading = bme280.read()
    temperature = bme_reading[0] - 5  # Apply a -5°C offset for temperature
    pressure = bme_reading[1] / 100  # Convert pressure to hPa
    humidity = bme_reading[2]  # Humidity

    # Read LTR-559 light and proximity sensor data
    ltr_reading = ltr559.get_reading()
    light = ltr_reading[BreakoutLTR559.LUX] if ltr_reading else 0
    proximity = ltr_reading[BreakoutLTR559.PROXIMITY] if ltr_reading else 0

    # Read acceleration and gyroscope data from LSM6DS3
    ax, ay, az, gx, gy, gz = motion_sensor.get_readings()
    orientation = (gx, gy, gz)  # Now uses gyroscope readings for rotation
    motion = (ax, ay, az)       # Now uses accelerometer readings for movement

    item_spacing = DISPLAY_HEIGHT // len(sensor_titles)
    bar_height = 3  # Thin bar height for Ax, Ay, Az lines
    y_offset = 3  # Additional 3-pixel downward shift for top 5 sensors

    # Temperature bar
    temp_y = int(10 + 0 * item_spacing + y_offset)
    temp_bar_width = int((temperature / 50) * max_bar_width)  # Scale temp (0-50°C)
    display.set_pen(set_bar_color(temperature, 50))
    display.rectangle(x_offset, temp_y, temp_bar_width, 10)
    display.set_pen(white_pen)
    display.text(f"{temperature:.1f}°C", x_offset + temp_bar_width + 5, temp_y - 2, scale=2)

    # Pressure bar
    press_y = int(10 + 1 * item_spacing + y_offset)
    press_bar_width = int(((pressure - 950) / 100) * max_bar_width)  # Scale pressure (950-1050 hPa)
    display.set_pen(set_bar_color(pressure, 1050))
    display.rectangle(x_offset, press_y, press_bar_width, 10)
    display.set_pen(white_pen)
    display.text(f"{pressure:.1f} hPa", x_offset + press_bar_width + 5, press_y - 2, scale=2)

    # Humidity bar
    hum_y = int(10 + 2 * item_spacing + y_offset)
    hum_bar_width = int((humidity / 100) * max_bar_width)  # Scale humidity (0-100%)
    display.set_pen(set_bar_color(humidity, 100))
    display.rectangle(x_offset, hum_y, hum_bar_width, 10)
    display.set_pen(white_pen)
    display.text(f"{humidity:.1f}%", x_offset + hum_bar_width + 5, hum_y - 2, scale=2)

    # Light bar
    light_y = int(10 + 3 * item_spacing + y_offset)
    light_bar_width = int((light / 2000) * max_bar_width)  # Scale light (0-2000 lux)
    display.set_pen(set_bar_color(light, 2000))
    display.rectangle(x_offset, light_y, light_bar_width, 10)
    display.set_pen(white_pen)
    display.text(f"{light:.0f} lx", x_offset + light_bar_width + 5, light_y - 2, scale=2)

    # Proximity bar (scaled to 0-50 range)
    prox_y = int(10 + 4 * item_spacing + y_offset)
    prox_bar_width = int((proximity / 50) * max_bar_width)  # Scale proximity (0-50)
    display.set_pen(set_bar_color(proximity, 50))
    display.rectangle(x_offset, prox_y, prox_bar_width, 10)
    display.set_pen(white_pen)
    display.text(f"{proximity}", x_offset + prox_bar_width + 5, prox_y - 2, scale=2)

    # Orientation bars (Gx, Gy, Gz) with custom label alignment
    orientation_y = int(10 + 5 * item_spacing)
    gap = 5  # Gap between each thin line for Gx, Gy, Gz

    gx, gy, gz = orientation
    gx_bar_width = min(int((abs(gx) / GYRO_MAX) * max_bar_width), max_bar_width)
    gy_bar_width = min(int((abs(gy) / GYRO_MAX) * max_bar_width), max_bar_width)
    gz_bar_width = min(int((abs(gz) / GYRO_MAX) * max_bar_width), max_bar_width)

    display.set_pen(set_bar_color(abs(gx), GYRO_MAX))
    display.rectangle(x_offset, orientation_y, gx_bar_width, bar_height)
    display.set_pen(white_pen)
    display.text(f"Gx:{gx:.1f}", x_offset + gx_bar_width + 5, int(orientation_y -5), scale=1)  # Align bottom

    display.set_pen(set_bar_color(abs(gy), GYRO_MAX))
    display.rectangle(x_offset, int(orientation_y + bar_height + gap), gy_bar_width, bar_height)
    display.set_pen(white_pen)
    display.text(f"Gy:{gy:.1f}", x_offset + gy_bar_width + 5, int(orientation_y + 6), scale=1)  # Centered

    display.set_pen(set_bar_color(abs(gz), GYRO_MAX))
    display.rectangle(x_offset, int(orientation_y + 2 * (bar_height + gap)), gz_bar_width, bar_height)
    display.set_pen(white_pen)
    display.text(f"Gz:{gz:.1f}", x_offset + gz_bar_width + 5, int(orientation_y + 2 * (bar_height + gap)), scale=1)

    # Motion bars (Ax, Ay, Az) with color scaling and value labels
    motion_y = int(10 + 6 * item_spacing)
    ax, ay, az = motion
    ax_bar_width = min(int((abs(ax) / ACCEL_MAX) * max_bar_width), max_bar_width)
    ay_bar_width = min(int((abs(ay) / ACCEL_MAX) * max_bar_width), max_bar_width)
    az_bar_width = min(int((abs(az) / ACCEL_MAX) * max_bar_width), max_bar_width)

    display.set_pen(set_bar_color(abs(ax), ACCEL_MAX))
    display.rectangle(x_offset, motion_y, ax_bar_width, bar_height)
    display.set_pen(white_pen)
    display.text(f"Ax:{ax:.1f}", x_offset + ax_bar_width + 5, motion_y -4 , scale=1)

    display.set_pen(set_bar_color(abs(ay), ACCEL_MAX))
    display.rectangle(x_offset, int(motion_y + bar_height + gap), ay_bar_width, bar_height)
    display.set_pen(white_pen)
    display.text(f"Ay:{ay:.1f}", x_offset + ay_bar_width + 5, int(motion_y + 6), scale=1)

    display.set_pen(set_bar_color(abs(az), ACCEL_MAX))
    display.rectangle(x_offset, int(motion_y + 2 * (bar_height + gap)), az_bar_width, bar_height)
    display.set_pen(white_pen)
    display.text(f"Az:{az:.1f}", x_offset + az_bar_width + 5, int(motion_y + 2 * (bar_height + gap)), scale=1)

    display.update()  # Update the display with sensor data

def main_loop():
    draw_sensor_titles()  # Display static sensor titles initially
    while True:
        display_sensor_values()  # Dynamic sensor values and bars on the right
        time.sleep(0.01)  # Shorter delay for real-time updates

# Run the main loop
main_loop()

