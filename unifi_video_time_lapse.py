'''
Unifi Video TimeLapse Software

devel release 
	add logging support for stdout and stderr
	add start and stop methods for launchd
	automate ffmpeg frame-to-video creation and concatenation

if you are seeing an openssl error reference this article:
	https://github.com/kelaberetiv/TagUI/issues/635

	error ref:
	dyld: Library not loaded: /usr/local/opt/openssl/lib/libssl.1.0.0.dylib
		Referenced from: /usr/local/bin/ffmpeg


'''
import os
import sys
import time
import logging
import shutil
import subprocess
import daemon

import datetime
from astral import Astral


BASE_DIR 	= '/Users/rpl/projects/time_lapse/'
STORAGE_DIR = '/mnt/syntonique_inc/_OPUS38/studio_build/video/'


def camera_setup():
	'''
	setup camera names and associated rtsp streams
	'''
	cameras = dict()
	# 1st Floor Entry Camera
	cameras['1F_REAR'] = 'rtsp://192.168.1.40:7447/5c5f8a9fe4b00470df314462_0'
	# 1st Floor Main Camera
	cameras['1F_SERVER_ROOM'] = 'rtsp://192.168.1.40:7447/5c5f8a9fe4b00470df314461_0'
	# 1st Floor Main Camera
	cameras['1F_1139_Entry'] = 'rtsp://192.168.1.40:7447/5e5ad155e4b02e3879b5a97c_0'

	# 2nd Floor Front Camera
	cameras['2F_FRONT'] = 'rtsp://192.168.1.40:7447/5c5f8a9fe4b00470df31445d_0'
	# 2nd Floor Rear Camera
	cameras['2F_REAR'] = 'rtsp://192.168.1.40:7447/5c5f8a9fe4b00470df314460_0'
	# 2nd Floor Storage Camera
	cameras['2F_STORAGE'] = 'rtsp://192.168.1.40:7447/5c5f8a9fe4b00470df31445f_0'

	return (cameras)


def create_storage_folder():
	'''
	file system management
	'''
	#### create todays folder name e.g "20190322"
	todays_date = time.strftime("%Y%m%d")

	#### check if todays folder exists "/mnt/syntonique_inc/_OPUS38/studio_build/video/20190322"
	todays_dir_exists = os.path.isdir(STORAGE_DIR + todays_date)
	print ("todays directory exists: ", todays_dir_exists)

	#### if folder does not exist then create it
	#### this should only happen once daily just after midnight
	if not todays_dir_exists:
		print ("creating todays directory")
		# define the access rights
		access_rights = 0o755
		path = STORAGE_DIR + todays_date

		try:  
		    os.mkdir(path, access_rights)
		except OSError:  
		    print ("Creation of the directory %s failed" % path)
		else:  
		    print ("Successfully created the directory %s" % path)

	return (todays_date)


def move_snapshots_to_storage_folder(ffmpeg_snapshots, todays_date):

	#### move the ffmpeg snapshots to the storage directory
	for snapshot in ffmpeg_snapshots:
		current_path = BASE_DIR + snapshot
		rename_path = STORAGE_DIR + todays_date + "/" + snapshot

		## if file exists
		if os.path.isfile(current_path):
			print ("MOVING\n", "\t", current_path, "\n\t", rename_path)
			shutil.move(current_path, rename_path)

def camera_take_snapshots(cameras):

	#### create local time stamp for file prefix "20190322170409"
	localtime = time.strftime("%Y%m%d%H%M%S")
	print (localtime)

	#### loop through cameras, create filenames, and take ffmpeg snapshots
	ffmpeg_snapshots = list()	## store filenames for eventual file system move 

	for camera in cameras:
		print (camera, cameras[camera])
		#### time stamp prefix
		#file_name = localtime + "_" + camera + ".jpeg"
		#file_path_file_name = BASE_DIR + localtime + "_" + camera + ".jpeg"

		#### time stamp suffix
		file_name =  camera + "_" + localtime + ".jpeg"
		file_path_file_name = BASE_DIR + camera + "_" + localtime + ".jpeg"
		
		#### adding -rtsp_transport tcp in lieu of consistently dropped packets on a couple cameras on std UDP
		#### ffmpeg -ss 2 -rtsp_transport tcp -i cameras[camera] -y -f image2 -frames 1 -nostats -loglevel warning file_path_file_name
		#### ffmpeg -ss 2 -rtsp_transport tcp -i rtsp://192.168.1.40:7447/5c5f8a9fe4b00470df31445d_0 -y -f image2 -frames 1 -nostats -loglevel warning test.jpeg

		p = subprocess.run(['ffmpeg', '-ss', '2','-rtsp_transport','tcp', '-i', cameras[camera] ,'-y','-f','image2','-frames','1','-nostats','-loglevel','warning', file_path_file_name])
		#p = subprocess.Popen(['ffmpeg', '-ss', '2','-rtsp_transport','tcp', '-i', cameras[camera] ,'-y','-f','image2','-frames','1','-nostats','-loglevel','warning', file_path_file_name])
		#p = subprocess.Popen(['touch', file_path_file_name])
		
		#p = subprocess.run(['ffmpeg', '-ss', '2','-rtsp_transport','tcp', '-i', cameras[camera] ,'-y','-f','image2','-qscale','0','-frames','1','-nostats', file_path_file_name])
		ffmpeg_snapshots.append(file_name)


	#### wait until files are created before continuing
	for snapshot in ffmpeg_snapshots:
		while not os.path.exists(snapshot):
			time.sleep(1)

	return (ffmpeg_snapshots)


def dusk_til_dawn():

	a = Astral()
	a.solar_depression = 'civil'

	city_name = 'San Francisco'
	city = a[city_name]

	print('Information for %s/%s\n' % (city_name, city.region))

	timezone = city.timezone
	print('Timezone: %s' % timezone)

	print('Latitude: %.02f; Longitude: %.02f\n' % \
		(city.latitude, city.longitude))

	#### create todays folder name e.g "20190322"
	now = datetime.datetime.now()

	sun = city.sun(date=datetime.date(now.year, now.month, now.day), local=True)
	print('Dawn:    %s' % str(sun['dawn']))
	print('Sunrise: %s' % str(sun['sunrise']))
	print('Noon:    %s' % str(sun['noon']))
	print('Sunset:  %s' % str(sun['sunset']))
	print('Dusk:    %s' % str(sun['dusk']))

	#### extact only 24-hour time component of dawn and dusk
	#### Dawn:    2019-03-23 06:42:55-07:00
	#### Sunrise: 2019-03-23 07:09:07-07:00
	#### Noon:    2019-03-23 13:16:26-07:00
	#### Sunset:  2019-03-23 19:23:46-07:00
	#### Dusk:    2019-03-23 19:49:58-07:00

	today_dawn = str(sun['dawn'])
	today_dusk = str(sun['dusk'])

	#### refactor dawn and dusk to 24-hour numerical for logical operations
	#### dawn = 064255 
	#### dusk = 194958
	dawn = today_dawn[11:13] + today_dawn[14:16] + today_dawn[17:19] 
	dusk = today_dusk[11:13] + today_dusk[14:16] + today_dusk[17:19] 

	return (dawn, dusk)


def current_time_between_dawn_and_dusk(dawn, dusk):
	
	#### create local time stamp for file prefix "170409"
	now = time.strftime("%H%M%S")

	#### if current time is between dawn and dusk
	if int(now) > int(dawn) and int(now) < int(dusk):
		return True
	else:
		return False 



if __name__=='__main__':

	with daemon.DaemonContext( working_directory=BASE_DIR, stdout=sys.stdout, stderr=sys.stderr ):

		while True:
			#### retrieve todays dawn and dusk times
			(dawn, dusk) = dusk_til_dawn()
			#print (dawn, dusk)

			#### only create snapshots in between dawn and dusk 
			if current_time_between_dawn_and_dusk(dawn, dusk):
				print ("True")

				cameras = camera_setup()
				ffmpeg_snapshots = camera_take_snapshots(cameras)

				todays_date = create_storage_folder()
				move_snapshots_to_storage_folder(ffmpeg_snapshots, todays_date)

				time.sleep(600)
				#time.sleep(1200)

			else:
				print ("False")
				time.sleep(600)
























