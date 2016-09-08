import os, logging, platform


log = logging.getLogger(__name__)


sms_message = """Hi {0}, You have successfully registered with online 
music app.\nPlease login to {1}/music/login/\n\nThank you,\nSongs India Team"""

register_email_body = """Hello {0},<br><br>Thank you for register with our 
online music application.<br><br>Your login credentials:<br>
Username: {1}<br>Password: {2}<br><br>If you like this web site please
share it with you friends.<br><br><br>Thank you,<br>Songs India Team<br>"""

forget_pass_email_body = """Hello {0},<br><br>Your Songs India credentials:
<br><br>&nbsp;&nbsp;&nbsp;&nbsp;Username: {1}<br>&nbsp;&nbsp;&nbsp;&nbsp;
Temporary Password: {2}<br><br>Please <a href="{3}/music/change-password/">
click here</a> to reset your password.<br><br><br>Thank you,<br>
Songs India Team"""

change_pass_email_body = """Hello {0},<br><br>Your password has been changed 
successfully. Your new Songs India credentials:<br><br>&nbsp;&nbsp;&nbsp;
&nbsp;Username: {1}<br>&nbsp;&nbsp;&nbsp;&nbsp;New Password: {2}<br><br>
Please <a href="{3}/music/login/">click here</a> to login your account.
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
    log.info('Operating system: {0}'.format(platform.system()))
    try:
        if platform.system() == 'Windows':
            deleting_file = file_location.split('/')[-1]
            os.remove('songsindia.com\media\{0}'.format(deleting_file))
        else:
            os.remove('songsindia.com{0}'.format(file_location))

        log.debug('File: {0} is removed successfully.'.format(
            file_location))

    except OSError as err:
        log.info(err)
        log.debug('File: {0} does not exists in the system!!!.'.format(
            file_location))
