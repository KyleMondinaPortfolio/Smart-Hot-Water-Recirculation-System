#This file contains the sampling and analysis program for the MPU 6050 used for hot water detection
#It includes:
#1. I2C functions that implement required functionality including self testing for the MPU 6050
#2. A program that divides into two processes for sampling from the MPU 6050 and outputting an analysis of water flow state to a file
#Program should be run using the .venv in the repository

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

#Values for selecting accelerometer and gyroscope measurement ranges
AFS_SEL_VALS = [16384.0, 8192.0, 4096.0, 2048.0] #2g, 4g, 8g, 16g
FS_SEL_VALS = [131.0, 65.5, 32.8, 16.4] #250, 500, 1000, 2000 deg/s


#CONFIG VALUES for measurement ranges
AFS_SEL_IDX = 0
FS_SEL_IDX = 0

bus = smbus2.SMBus(1)   #use SMBUS v2
Device_Address = 0x68   # MPU6050 device address

#Runs a self test for the gyroscope
#Sets self test flags in the config register and compares them to the values with self test disabled
#If the percent error of the difference compared to the factory trim stored in the SELF_TEST registers is too high, test fails
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

	#Max allowed error according to manufacturer spec
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

#Runs a self test for the accelerometer
#Sets self test flags in the config register and compares them to the values with self test disabled
#If the percent error of the difference compared to the factory trim stored in the SELF_TEST registers is too high, test fails
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

	#Max allowed error according to manufacturer spec
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

#Wakes and Initializes MPU to a 1khz sample rate (8khz for the gyro) and sets the configuration for accel and gyro range
#Runs a self test after
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


#Read raw 16 bit value from MPU register
def read_s16_raw(addr_h, addr_l):
	high = bus.read_byte_data(Device_Address, addr_h)
	low = bus.read_byte_data(Device_Address, addr_l)

	#concatenate higher and lower value
	value = ((high << 8) | low)

	signed_value = ctypes.c_int16(value).value
	return signed_value

#Read temperature value (in Celsius) from MPU
def read_temp():
	value = read_s16_raw(TEMP_OUT_H, TEMP_OUT_L)
	return value/340 + 36.53

#Read acceleration values (in g) from MPU, returns [3]
def read_accel():
	valx = read_s16_raw(ACCEL_XOUT_H, ACCEL_XOUT_L)
	valy = read_s16_raw(ACCEL_YOUT_H, ACCEL_YOUT_L)
	valz = read_s16_raw(ACCEL_ZOUT_H, ACCEL_ZOUT_L)

	divisor = AFS_SEL_VALS[AFS_SEL_IDX]

	return [valx/divisor, valy/divisor, valz/divisor] #value depends on accel scale, returns in g

#Reads gyroscope rotation values (in deg/s), returns [3]
def read_gyro():
	valx = read_s16_raw(GYRO_XOUT_H, GYRO_XOUT_L)
	valy = read_s16_raw(GYRO_YOUT_H, GYRO_YOUT_L)
	valz = read_s16_raw(GYRO_ZOUT_H, GYRO_ZOUT_L)

	divisor = FS_SEL_VALS[FS_SEL_IDX]

	return [valx/divisor, valy/divisor, valz/divisor] #value depends on gyro scale, returns in deg/s

#Samples per analysis block
SAMPLE_COUNT = 512

#Starts a sampler that reads and creates analysis blocks for processing and sends to analysis process
def producer(dqueue: Queue, plock):
	print("Im a producer")
	MPU_Init()

	temp_count = 0
	while True:		
		sample_segment = []
		for i in range(SAMPLE_COUNT):

			#Read Accelerometer value
			accel = read_accel()
			Ax = accel[0]
			Ay = accel[1]
			Az = accel[2]

			#Read temp value
			Temp = read_temp()
			if Temp > 85:
				temp_count += 1
				print("WARNING: MPU TEMPERATURE EXCEEDED OPERATING RANGE")
			else:
				temp_count = 0
			if temp_count >= 100:
				print("ERROR: MPU TEMPERATURE TOO HIGH, EXTING PROGRAM")
				exit(1)
				
			sample_segment.append(accel)

		dqueue.put(sample_segment)

#number of consecutive "on" tests required to change to "on" state
DELAY_SAMPLES = 4

#Analysis process, receives sample block and determines if hot water is on or off
#If a state change occurs, writes to the output csv for use by the prediction system
def consumer(dqueue, plock):
	print("Im a consumer")

	tsample_count = 0
	seq = 0
	is_on = False
	while True:
		s = dqueue.get()
		
		sample = np.ndarray(shape=(SAMPLE_COUNT, 3), buffer=np.array(s), dtype=np.double).transpose() #(3, SAMPLE_COUNT)

		threshold = False
		fft = np.fft.fft(sample[0])[SAMPLE_COUNT//2:]
		fft_norm = np.abs(fft)
		fft_mb = np.argmax(fft_norm)
		if (fft_mb == 238 or fft_mb == 224 or 110 <= fft_mb <= 114) and fft_norm[fft_mb] > 2:
			threshold = True

		if threshold:
			if is_on:
				seq = DELAY_SAMPLES
			else:
				seq += 1
		else:
			if is_on:
				seq -= 1
			else:
				seq = 0

		old_on = is_on
		if seq == DELAY_SAMPLES:
			is_on = True
		elif seq == 0:
			is_on = False
		
		#found change in state
		if old_on != is_on:
			if is_on:
				with plock:
					print("Hot water ON")
				with open('running-data.csv', 'a') as f:
					writer = csv.writer(f, delimiter=',')
					writer.writerow([1, {datetime.now()}])			
			else:
				with plock:
					print("Hot water OFF")
				with open('running-data.csv', 'a') as f:
					writer = csv.writer(f, delimiter=',')
					writer.writerow([0, {datetime.now()}])

			tsample_count += 1
		
#Start producer and consumer processes with an IPC queue
#While threads would be preferable, python cannot do true thread parallelism in many cases except I/O due to GIL
#This could bottleneck the program and limit the sampling speed, so processes are used instead
if __name__ == "__main__":
	data_queue = Queue()
	print_lock = Lock()

	p = Process(target=consumer, args=(data_queue, print_lock))
	p.daemon = True
	p.start()

	producer(data_queue, print_lock)
	p.join()