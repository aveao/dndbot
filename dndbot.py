import discord
import subprocess
import re

# logging imports
import logging

# configparser for userid and token
import configparser

# logging config
log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
)

# configparser config
config_file_name = "dndbot.ini"
config = configparser.ConfigParser()
config.read(config_file_name)

client = discord.Client()
user_to_watch = config['base']['userid']
sink_regex = r"([0-9]{1,3}%)"
user_volume = 0

def pagetvolume(): # https://unix.stackexchange.com/questions/132230/
    """ Gets pulseaudio volume level """
    sink_data = subprocess.check_output("pactl list sinks | grep '^[[:space:]]Volume:'"
        "| head -n $(( $SINK + 1 ))  | tail -n 1", shell=True, stderr=subprocess.STDOUT)
    sink_string = sink_data.decode("utf-8")
    matches = re.search(sink_regex, sink_string)
    if matches:
        volume = int(matches[0][:-1])
        log.info(f"Got volume: {volume}%")
        return volume
    return 0

def pasavevolume():
    global user_volume
    user_volume = pagetvolume()

def pasetvolume(volume: int):
    """ Sets pulseaudio volume level to the specified amount """
    log.info(f"Setting volume to {volume}%")
    subprocess.check_output(f"pactl set-sink-volume 0 {volume}%", shell=True, stderr=subprocess.STDOUT)

@client.event
async def on_member_update(before, after):
    if (after.id != user_to_watch):
        return
    elif (str(before.status) == "dnd" and str(after.status) == "online"):
        pasetvolume(user_volume)
    elif (str(before.status) == "online" and str(after.status) == "dnd"):
        pasavevolume()
        pasetvolume(0)

@client.event
async def on_ready():
    log.info('Logged in as')
    log.info(client.user.name)
    log.info(client.user.id)
    log.info('------')
    pasavevolume()

if __name__ == '__main__':
    client.run(config['base']['token'])