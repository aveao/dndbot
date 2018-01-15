import discord
import subprocess
import re

# logging shit
import sys
import logging
import logging.handlers

# configparser for userid and token
import configparser

# logging config
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [stdout_handler]
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

# configparser config
config_file_name = "dndbot.ini"
config = configparser.ConfigParser()
config.read(config_file_name)

client = discord.Client()
user_to_watch = config['base']['userid']
sink_regex = r"([0-9]{1,3}%)"
user_volume = 0

def pagetvolume(): # https://unix.stackexchange.com/questions/132230/read-out-pulseaudio-volume-from-commandline-i-want-pactl-get-sink-volume
    """ Gets pulseaudio volume level """
    sink_data = subprocess.check_output("pactl list sinks | grep '^[[:space:]]Volume:' | head -n $(( $SINK + 1 ))  | tail -n 1", shell=True, stderr=subprocess.STDOUT)
    sink_string = sink_data.decode("utf-8")
    matches = re.search(sink_regex, sink_string)
    if matches:
        volume = int(matches[0][:-1])
        logging.info("Got volume: {}.".format(volume))
        return volume
    else:
        return 0

def pasetvolume(volume: int):
    """ Sets pulseaudio volume level to the specified amount """
    logging.info("Setting volume to {}.".format(volume))
    paoutput = subprocess.check_output("pactl set-sink-volume 0 {}%".format(volume), shell=True, stderr=subprocess.STDOUT)

@client.event
async def on_member_update(before,after):
    global user_volume
    if (after.id == user_to_watch and str(before.status) == "dnd" and str(after.status) == "online"):
        pasetvolume(user_volume)
    elif (after.id == user_to_watch and str(before.status) == "online" and str(after.status) == "dnd"):
        user_volume = pagetvolume()
        pasetvolume(0)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    global user_volume
    user_volume = pagetvolume()

client.run(config['base']['token'])