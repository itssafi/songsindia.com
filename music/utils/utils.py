import os
import logging
import platform
from server.settings import MEDIA_ROOT

log = logging.getLogger(__name__)


sms_message = """Hi {0}, You have successfully registered with online 
music web app.\nPlease login to {1}/users/login/\n\nThank you,\nSongs India Team"""

register_email_body = """Hello {0},<br><br>Thank you for register with our 
online music application.<br><br>Your login credentials:<br>
Username: {1}<br>Password: {2}<br><br>If you like this web site please
share it with your friends and family.<br><br><br>Thank you,<br>Songs India Team<br>"""

forget_pass_email_body = """Hello {0},<br><br>Your Songs India credentials:
<br><br>&nbsp;&nbsp;&nbsp;&nbsp;Username: {1}<br>&nbsp;&nbsp;&nbsp;&nbsp;
Temporary Password: {2}<br><br>Please <a href="{3}/users/change-password/">
click here</a> to reset your password.<br><br><br>Thank you,<br>
Songs India Team"""

change_pass_email_body = """Hello {0},<br><br>Your password has been changed 
successfully. Your new Songs India credentials:<br><br>&nbsp;&nbsp;&nbsp;
&nbsp;Username: {1}<br>&nbsp;&nbsp;&nbsp;&nbsp;New Password: {2}<br><br>
Please <a href="{3}/users/login/">click here</a> to login your account.
<br><br><br>Thank You,<br>Songs India Team"""


def select_next_pre_song(songs, context):
    pre_song, next_song, is_found = None, None, False
    for index, song in enumerate(songs):
        if is_found:
            context['next_song'] = song
            break
        elif song.song_title == context['song_title']:
            is_found = True
            context['previous_song'] = pre_song
            if songs.count() == index + 1:
                context['next_song'] = next_song
                break
        else:
            pre_song = song

    return context


def remove_file_logging(file_location):
    if platform.system() == 'Windows':
        absolute_file_path = r'/'.join(MEDIA_ROOT.split(os.sep)).replace('/media', '') + file_location
    else:
        absolute_file_path = MEDIA_ROOT.replace('/media', '') + file_location
    if os.path.isfile(absolute_file_path):
        try:
            os.remove(absolute_file_path)
            log.debug('File: {0} is removed successfully.'.format(file_location))

        except OSError as err:
            log.info(err)
            log.debug("File: '{0}' not found!!!.".format(file_location))
