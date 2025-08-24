import os
import sys
import signal
import logging
import traceback
import re
import hid
import time

class Arctis7PlusChatMix:
	def __init__(self):

		# set to receive signal from systemd for termination
		signal.signal(signal.SIGTERM, self.__handle_sigterm)

		self.log = self._init_log()
		self.log.info("Initializing ac7pcm...")

		# identify the arctis 7+ device
		try:
			self.dev = hid.device()
			self.dev.open(0x1038, 0x2202)
		except Exception as e:
			self.log.error("""Failed to identify the Arctis 7+ device.
			Please ensure it is connected.\n
			Please note: This program only supports the '7+' model.""")
			self.die_gracefully(trigger)

		self.VAC = self._init_VAC()


	def _init_log(self):
		log = logging.getLogger(__name__)
		log.setLevel(logging.DEBUG)
		stdout_handler = logging.StreamHandler()
		stdout_handler.setLevel(logging.DEBUG)
		stdout_handler.setFormatter(logging.Formatter('%(levelname)8s | %(message)s'))
		log.addHandler(stdout_handler)
		return (log)

	def _init_VAC(self):
		"""Get name of default sink, establish virtual sink
		and pipe its output to the default sink
		"""

		# get the default sink id from pactl
		self.system_default_sink = os.popen("pactl get-default-sink").read().strip()
		self.log.info(f"default sink identified as {self.system_default_sink}")

		# attempt to identify an Arctis sink via pactl
		try:
			pactl_short_sinks = os.popen("pactl list short sinks").readlines()
			# grab any elements from list of pactl sinks that are Arctis 7
			arctis = re.compile('.*[aA]rctis.*7')
			arctis_sink = list(filter(arctis.match, pactl_short_sinks))[0]

			# split the arctis line on tabs (which form table given by 'pactl short sinks')
			tabs_pattern = re.compile(r'\t')
			tabs_re = re.split(tabs_pattern, arctis_sink)

			# skip first element of tabs_re (sink's ID which is not persistent)
			arctis_device = tabs_re[1]
			self.log.info(f"Arctis sink identified as {arctis_device}")
			default_sink = arctis_device

		except Exception as e:
			self.log.error("""Something wrong with Arctis definition
			in pactl list short sinks regex matching.
			Likely no match found for device, check traceback.
			""", exc_info=True)
			self.die_gracefully(trigger="No Arctis device match")

		# Destroy virtual sinks if they already existed incase of previous failure:
		try:
			destroy_a7p_game = os.system("pw-cli destroy Arctis_Game 2>/dev/null")
			destroy_a7p_chat = os.system("pw-cli destroy Arctis_Chat 2>/dev/null")
			if destroy_a7p_game == 0 or destroy_a7p_chat == 0:
				raise Exception
		except Exception as e:
			self.log.info("""Attempted to destroy old VAC sinks at init but none existed""")

		# Instantiate our virtual sinks - Arctis_Chat and Arctis_Game
		try:
			self.log.info("Creating VACS...")
			os.system("""pw-cli create-node adapter '{
				factory.name=support.null-audio-sink
				node.name=Arctis_Game
				node.description="Arctis 7+ Game"
				media.class=Audio/Sink
				monitor.channel-volumes=true
				object.linger=true
				audio.position=[FL FR]
				}' 1>/dev/null
			""")

			os.system("""pw-cli create-node adapter '{
				factory.name=support.null-audio-sink
				node.name=Arctis_Chat
				node.description="Arctis 7+ Chat"
				media.class=Audio/Sink
				monitor.channel-volumes=true
				object.linger=true
				audio.position=[FL FR]
				}' 1>/dev/null
			""")
		except Exception as E:
			self.log.error("""Failure to create node adapter -
			Arctis_Chat virtual device could not be created""", exc_info=True)
			self.die_gracefully(sink_creation_fail=True, trigger="VAC node adapter")

		#route the virtual sink's L&R channels to the default system output's LR
		try:
			self.log.info("Assigning VAC sink monitors output to default device...")

			os.system(f'pw-link "Arctis_Game:monitor_FL" '
			f'"{default_sink}:playback_FL" 1>/dev/null')

			os.system(f'pw-link "Arctis_Game:monitor_FR" '
			f'"{default_sink}:playback_FR" 1>/dev/null')

			os.system(f'pw-link "Arctis_Chat:monitor_FL" '
			f'"{default_sink}:playback_FL" 1>/dev/null')

			os.system(f'pw-link "Arctis_Chat:monitor_FR" '
			f'"{default_sink}:playback_FR" 1>/dev/null')

		except Exception as e:
			self.log.error("""Couldn't create the links to
			pipe LR from VAC to default device""", exc_info=True)
			self.die_gracefully(sink_fail=True, trigger="LR links")

		# set the default sink to Arctis Game
		os.system('pactl set-default-sink Arctis_Game')

	def start_modulator_signal(self):
		"""Listen to the USB device for modulator knob's signal
		and adjust volume accordingly
		"""

		self.log.info("Reading modulator USB input started")
		self.log.info("-"*45)
		self.log.info("Arctis 7+ ChatMix Enabled!")
		self.log.info("-"*45)
		last = None
		while True:
			try:
				self.dev.write([0x00, 0xb0])
				resp = self.dev.read(8)
				if resp != last:
					last = resp
					os.system(f'pactl set-sink-volume Arctis_Game {resp[4]}%')
					os.system(f'pactl set-sink-volume Arctis_Chat {resp[5]}%')
				else:
					time.sleep(0.1)
			except Exception as e:
				pass

	def __handle_sigterm(self, sig, frame):
		self.die_gracefully()

	def die_gracefully(self, sink_creation_fail=False, trigger=None):
		"""Kill the process and remove the VACs
		on fatal exceptions or SIGTERM / SIGINT
		"""

		self.log.info('Cleanup on shutdown')
		os.system(f"pactl set-default-sink {self.system_default_sink}")

		# cleanup virtual sinks if they exist
		if  sink_creation_fail == False:
			self.log.info("Destroying virtual sinks...")
			os.system("pw-cli destroy Arctis_Game 1>/dev/null")
			os.system("pw-cli destroy Arctis_Chat 1>/dev/null")

		if trigger is not None:
			self.log.info("-"*45)
			self.log.fatal("Failure reason: " + trigger)
			self.log.info("-"*45)
			sys.exit(1)
		else:
			self.log.info("-"*45)
			self.log.info("Artcis 7+ ChatMix shut down gracefully... Bye Bye!")
			self.log.info("-"*45)
			sys.exit(0)

# init
if __name__ == '__main__':
	a7pcm_service = Arctis7PlusChatMix()
	a7pcm_service.start_modulator_signal()
