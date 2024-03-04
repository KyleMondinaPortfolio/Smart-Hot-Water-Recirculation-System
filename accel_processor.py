import smbus2				#import SMBus module of I2C
from time import sleep          #import
import ctypes
import csv
from multiprocessing import Process, Queue, Lock
import numpy as np
from datetime import datetime

#some MPU6050 Registers and their Address, MPU 6050 uses big endian
PWR_MGMT_1   = 0x6B
SELF_TEST_X  = 0x0D
SELF_TEST_Y  = 0x0E
SELF_TEST_Z  = 0x0F
SELF_TEST_A  = 0x10
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
ACCEL_CONFIG = 0x1C
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_XOUT_L = 0x3C
ACCEL_YOUT_H = 0x3D
ACCEL_YOUT_L = 0x3E
ACCEL_ZOUT_H = 0x3F
ACCEL_ZOUT_L = 0x40
GYRO_XOUT_H  = 0x43
GYRO_XOUT_L  = 0x44
GYRO_YOUT_H  = 0x45
GYRO_YOUT_L  = 0x46
GYRO_ZOUT_H  = 0x47
GYRO_ZOUT_L  = 0x48
TEMP_OUT_H   = 0x41
TEMP_OUT_L   = 0x42


AFS_SEL_VALS = [16384.0, 8192.0, 4096.0, 2048.0] #2g, 4g, 8g, 16g
FS_SEL_VALS = [131.0, 65.5, 32.8, 16.4] #250, 500, 1000, 2000 deg/s


#CONFIG VALUES
AFS_SEL_IDX = 3
FS_SEL_IDX = 3

bus = smbus2.SMBus(1) 	# or bus = smbus.SMBus(0) for older version boards
Device_Address = 0x68   # MPU6050 device address

def self_test_gyro():
	gyro_config_restore = bus.read_byte_data(Device_Address, GYRO_CONFIG)

	#gyro test
	print("Running self-test for gyroscope...")

	#enable self test
	bus.write_byte_data(Device_Address, GYRO_CONFIG, 0b11100000)
	sleep(0.25)
	enabled_x = read_s16_raw(GYRO_XOUT_H, GYRO_XOUT_L)
	enabled_y = read_s16_raw(GYRO_YOUT_H, GYRO_YOUT_L)
	enabled_z = read_s16_raw(GYRO_ZOUT_H, GYRO_ZOUT_L)

	#disable self test
	bus.write_byte_data(Device_Address, GYRO_CONFIG, 0b00000000)
	sleep(0.25)
	disabled_x = read_s16_raw(GYRO_XOUT_H, GYRO_XOUT_L)
	disabled_y = read_s16_raw(GYRO_YOUT_H, GYRO_YOUT_L)
	disabled_z = read_s16_raw(GYRO_ZOUT_H, GYRO_ZOUT_L)

	response_x = enabled_x - disabled_x
	response_y = enabled_y - disabled_y
	response_z = enabled_z - disabled_z

	factory_x = bus.read_byte_data(Device_Address, SELF_TEST_X) & 0b00011111
	factory_y = bus.read_byte_data(Device_Address, SELF_TEST_Y) & 0b00011111
	factory_z = bus.read_byte_data(Device_Address, SELF_TEST_Z) & 0b00011111
	if factory_x == 0 or factory_y == 0 or factory_z == 0:
		print("\tWARNING: 0 value for factory trim")

	factory_trim_x = 25 * 131 * 1.046**(factory_x - 1)
	factory_trim_y = (-25) * 131 * 1.046**(factory_y - 1)
	factory_trim_z = 25 * 131 * 1.046**(factory_z - 1)

	x_change_p = (response_x - factory_trim_x) / factory_trim_x 
	y_change_p = (response_y - factory_trim_y) / factory_trim_y 
	z_change_p = (response_z - factory_trim_z) / factory_trim_z 

	print("\tMax Allowed Error: 0.14")
	print(f"\tError Gx: {x_change_p}")
	print(f"\tError Gy: {y_change_p}")
	print(f"\tError Gz: {z_change_p}")

	if abs(x_change_p) > 0.14 or abs(y_change_p) > 0.14 or abs(z_change_p) > 0.14:
		print("\tGyroscope self-test failed! Exiting...")
		exit(1)
	else:
		print("Gyroscope self-test succeeded!")

	bus.write_byte_data(Device_Address, GYRO_CONFIG, gyro_config_restore)

def self_test_accel():
	accel_config_restore = bus.read_byte_data(Device_Address, ACCEL_CONFIG)

	#gyro test
	print("Running self-test for accelerometer...")

	#enable self test
	bus.write_byte_data(Device_Address, ACCEL_CONFIG, 0b11110000)
	sleep(0.25)
	enabled_x = read_s16_raw(ACCEL_XOUT_H, ACCEL_XOUT_L)
	enabled_y = read_s16_raw(ACCEL_YOUT_H, ACCEL_YOUT_L)
	enabled_z = read_s16_raw(ACCEL_ZOUT_H, ACCEL_ZOUT_L)

	#disable self test
	bus.write_byte_data(Device_Address, ACCEL_CONFIG, 0b00010000)
	sleep(0.25)
	disabled_x = read_s16_raw(ACCEL_XOUT_H, ACCEL_XOUT_L)
	disabled_y = read_s16_raw(ACCEL_YOUT_H, ACCEL_YOUT_L)
	disabled_z = read_s16_raw(ACCEL_ZOUT_H, ACCEL_ZOUT_L)

	response_x = enabled_x - disabled_x
	response_y = enabled_y - disabled_y
	response_z = enabled_z - disabled_z

	a_val = bus.read_byte_data(Device_Address, SELF_TEST_A)
	factory_x = ((bus.read_byte_data(Device_Address, SELF_TEST_X) & 0b11100000) >> 3) | ((a_val & 0b00110000) >> 4)
	factory_y = ((bus.read_byte_data(Device_Address, SELF_TEST_Y) & 0b11100000) >> 3) | ((a_val & 0b00001100) >> 2)
	factory_z = ((bus.read_byte_data(Device_Address, SELF_TEST_Z) & 0b11100000) >> 3) | (a_val & 0b00000011)
	if factory_x == 0 or factory_y == 0 or factory_z == 0:
		print("\tWARNING: 0 value for factory trim")

	factory_trim_x = 4096 * 0.34 * (0.92/0.34)**((factory_x - 1)/(2**5 - 2))
	factory_trim_y = 4096 * 0.34 * (0.92/0.34)**((factory_y - 1)/(2**5 - 2))
	factory_trim_z = 4096 * 0.34 * (0.92/0.34)**((factory_z - 1)/(2**5 - 2))

	x_change_p = (response_x - factory_trim_x) / factory_trim_x 
	y_change_p = (response_y - factory_trim_y) / factory_trim_y 
	z_change_p = (response_z - factory_trim_z) / factory_trim_z 

	print("\tMax Error: 0.14")
	print(f"\tError Ax: {x_change_p}")
	print(f"\tError Ay: {y_change_p}")
	print(f"\tError Az: {z_change_p}")

	if abs(x_change_p) > 0.14 or abs(y_change_p) > 0.14 or abs(z_change_p) > 0.14:
		print("Accelerometer self-test failed! Exiting...")
		exit(1)
	else:
		print("Accelerometer self-test succeeded!")

	bus.write_byte_data(Device_Address, ACCEL_CONFIG, accel_config_restore)


def MPU_Init():
	#write to sample rate register [1khz]
	bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
	
	#Write to power management register
	bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)
	
	#Write to Configuration register
	#Gyro output rate: 8khz, accel output rate: 1khz
	bus.write_byte_data(Device_Address, CONFIG, 0)
	
	#Write to Gyro configuration register
	bus.write_byte_data(Device_Address, GYRO_CONFIG, ctypes.c_uint8(FS_SEL_IDX << 3))

	bus.write_byte_data(Device_Address, ACCEL_CONFIG, ctypes.c_uint8(AFS_SEL_IDX << 3))
	
	#Write to interrupt enable register
	bus.write_byte_data(Device_Address, INT_ENABLE, 1)

	self_test_gyro()
	self_test_accel()



def read_s16_raw(addr_h, addr_l):
	high = bus.read_byte_data(Device_Address, addr_h)
	low = bus.read_byte_data(Device_Address, addr_l)

	#concatenate higher and lower value
	value = ((high << 8) | low)

	signed_value = ctypes.c_int16(value).value
	return signed_value

def read_temp():
	value = read_s16_raw(TEMP_OUT_H, TEMP_OUT_L)
	return value/340 + 36.53

def read_accel():
	valx = read_s16_raw(ACCEL_XOUT_H, ACCEL_XOUT_L)
	valy = read_s16_raw(ACCEL_YOUT_H, ACCEL_YOUT_L)
	valz = read_s16_raw(ACCEL_ZOUT_H, ACCEL_ZOUT_L)

	divisor = AFS_SEL_VALS[AFS_SEL_IDX]

	return [valx/divisor, valy/divisor, valz/divisor] #value depends on accel scale, returns in g

def read_gyro():
	valx = read_s16_raw(GYRO_XOUT_H, GYRO_XOUT_L)
	valy = read_s16_raw(GYRO_YOUT_H, GYRO_YOUT_L)
	valz = read_s16_raw(GYRO_ZOUT_H, GYRO_ZOUT_L)

	divisor = FS_SEL_VALS[FS_SEL_IDX]

	return [valx/divisor, valy/divisor, valz/divisor] #value depends on gyro scale, returns in deg/s


SAMPLE_COUNT = 500

def producer(dqueue: Queue, plock):
	print("Im a producer")
	MPU_Init()

	while True:		
		sample_segment = []
		for i in range(SAMPLE_COUNT):

			#Read Accelerometer value
			accel = read_accel()
			Ax = accel[0]
			Ay = accel[1]
			Az = accel[2]
			
			#Read Gyroscope value
			gyro = read_gyro()
			Gx = gyro[0]
			Gy = gyro[1]
			Gz = gyro[2]

			#Read temp value
			Temp = read_temp()
			
			#print ("Gx=%.6f" %Gx, u'\u00b0'+ "/s", "\tGy=%.6f" %Gy, u'\u00b0'+ "/s", "\tGz=%.6f" %Gz, u'\u00b0'+ "/s", "\tAx=%.6f g" %Ax, "\tAy=%.6f g" %Ay, "\tAz=%.6f g" %Az, "\tTemp=%.2f c" %Temp, end='\x1b[2k\r') 	
			sample_segment.append(accel)

			#sleep(0.001)
		dqueue.put(sample_segment)

def consumer(dqueue, plock):
	print("Im a consumer")

	seq = 0
	is_on = False
	while True:
		s = dqueue.get()
		
		#this processing isnt final, it's calibrated to Roshan's house (sorta) to gather basic data
		sample = np.ndarray(shape=(SAMPLE_COUNT, 3), buffer=np.array(s)).transpose() #(3, SAMPLE_COUNT)
		sample = np.linalg.norm(sample, axis=0)

		if np.var(sample) > 0.001:
			if is_on:
				seq = 3
			else:
				seq += 1
		else:
			if is_on:
				seq -= 1
			else:
				seq = 0

		old_on = is_on
		if seq == 3:
			is_on = True
		elif seq == 0:
			is_on = False
		
		#found change in state
		if old_on != is_on:
			if is_on:
				with plock:
					print("Hot water ON")
				with open('running-data.txt', 'a') as f:
					f.write(f"1 {datetime.now()}\n")
			else:
				with plock:
					print("Hot water OFF")
				with open('running-data.txt', 'a') as f:
					f.write(f"0 {datetime.now()}\n")
		





if __name__ == "__main__":
	data_queue = Queue()
	print_lock = Lock()

	p = Process(target=consumer, args=(data_queue, print_lock))
	p.daemon = True
	p.start()

	producer(data_queue, print_lock)
	p.join()