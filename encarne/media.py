"""Mediainfo related code."""
import os
import math
import hashlib
import subprocess

from lxml import etree
from datetime import datetime, timedelta

from encarne.logger import Logger


def check_duration(origin, temp, seconds=1):
    """Check if the duration is bigger than a specific amount."""
    # If the destination movie is shorter than a maximum of 1 seconds as the
    # original or has no duration property in mediainfo, the task will be dropped.
    origin_duration = get_media_duration(origin)
    duration = get_media_duration(temp)

    # If we can't get the duration the user needs to check manually.
    if origin_duration is None:
        Logger.info(f'Unknown time format for {origin}, compare them by hand.')
        return False, False,
    if duration is None:
        Logger.info(f'Unknown time format for {temp}, compare them by hand.')
        return False, False

    diff = origin_duration - duration
    THRESHOLD = 1
    if math.fabs(diff.total_seconds()) > THRESHOLD:
        Logger.info(f'Length differs more than {THRESHOLD} seconds.')
        return False, True
    return True, False


def check_file_size(origin, temp):
    """Compare the file size of original and re encoded file."""
    origin_filesize = os.path.getsize(origin)
    filesize = os.path.getsize(temp)
    if origin_filesize < filesize:
        Logger.info('Encoded movie is bigger than the original movie')
        return False, True
    else:
        difference = origin_filesize - filesize
        mebibyte = int(difference/1024/1024)
        Logger.info(f'The new movie is {mebibyte} MIB smaller than the old one')
        return True, False


def get_media_encoding(path):
    """Execute external mediainfo command and find the video encoding library."""
    # Get mediainfo output
    process = subprocess.run(
        ['mediainfo', '--Output=XML', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    root = etree.XML(process.stdout)

    # Try writing library
    try:
        writing_library = root.findall('.//{https://mediaarea.net/mediainfo}track[@type="Video"]/{https://mediaarea.net/mediainfo}Writing_library')[0].text
    except BaseException:
        writing_library = 'unknown'

    # Try encoded library name
    if writing_library == 'unknown':
        try:
            writing_library = root.findall('.//{https://mediaarea.net/mediainfo}track[@type="Video"]/{https://mediaarea.net/mediainfo}Encoded_Library_Name')[0].text
        except BaseException:
            writing_library = 'unknown'

    return writing_library


def get_media_duration(path):
    """Execute external mediainfo command and find the video encoding library."""
    process = subprocess.run(
        ['mediainfo', '--Output=PBCore2', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    root = etree.XML(process.stdout)
    try:
        duration = root.find(
            ".//ns:instantiationDuration",
            namespaces={'ns': 'http://www.pbcore.org/PBCore/PBCoreNamespace.html'},
        ).text
    except IndexError:
        Logger.info(f'Could not find duration for {path}')
        return None

    try:
        duration = duration.split('.')[0].split(';')[0]
        date = datetime.strptime(duration, '%H:%M:%S')
    except BaseException:
        try:
            duration = duration.rsplit(':', 1)[0]
            date = datetime.strptime(duration, '%H:%M:%S')
        except BaseException:
            Logger.info(f'Unknown duration: {duration}')
            return None

    delta = timedelta(
        hours=date.hour,
        minutes=date.minute,
        seconds=date.second,
    )

    return delta


def get_sha1(path):
    """Return the sha1 of a file."""
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 16 * 65536  # lets read stuff in 64kb chunks!

    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()
