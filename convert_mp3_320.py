import os, shutil
os.environ['PATH'] += ':/usr/local/bin'
import ffmpeg
import shutil
import subprocess
import time
from fcntl import flock, LOCK_EX, LOCK_NB


def acquire_lock(file_path):
    lockfile_path = file_path + '.lock'
    lockfile = open(lockfile_path, 'w')
    try:
        flock(lockfile, LOCK_EX | LOCK_NB)
        return lockfile
    except:
        return None

def release_lock(lockfile):
    if lockfile is not None:
        flock(lockfile, LOCK_EX)
        lockfile.close()

def apply_and_remove_lock(src):
    lockfile = acquire_lock(src)
    while lockfile is None:
        print(f'File {src} is locked, waiting to acquire lock...')
        time.sleep(5)
        lockfile = acquire_lock(src)
    release_lock(lockfile)

srcDir = 'Soulseek Downloads/complete/'
destDir = 'STLB2/'

ext_excl = set(['', '.asd', '.m3u', '.reapeaks', '.nfo', \
    '.sfv', '.jpg', '.png', '.jpeg', '.txt', '.url', '.log', '.cue', '.db', '.DS_Store', '._', '.lock'])

os.system("find ./STLB2/ -name '.DS_Store' -type f -delete")

# loop through source directory
for root, dirs, files in os.walk(srcDir, topdown=True):
    for file in files:
        src = os.path.join(root, file)
        target = os.path.join(destDir, '/'.join(src.split('/')[2:]))

        # check for duplicate first?
        # print(os.path.splitext(target)[0], os.path.splitext(target)[1], '\n\n')

        # If the mp3 copy does not exist
        if not os.path.exists(os.path.splitext(target)[0] + '.mp3') \
            and os.path.splitext(target)[1].lower() not in ext_excl:

            # Check if the source file is flac
            is_flac = False
            if os.path.splitext(src)[1].lower() == '.flac':
                is_flac = True

            if is_flac:
                try:
                    os.makedirs(os.path.dirname(target))
                except:
                    pass
                apply_and_remove_lock(src)
                out, _ = (ffmpeg
                    .input(src)
                    .output(os.path.splitext(target)[0] + '.mp3', format="mp3", audio_bitrate=320000)
                    .run(capture_stdout=True)
                )

            else:
                # Check if the source file is already an mp3 with 320kbps bitrate
                probe = subprocess.run(['ffprobe', '-show_streams', src], capture_output=True)
                probe_output = probe.stdout.decode()
                audio_bitrate = None
                for line in probe_output.splitlines():
                    if line.strip().startswith('bit_rate='):
                        audio_bitrate = int(line.strip().split('=')[1])
                        break
                if audio_bitrate and audio_bitrate >= 320000:
                    # print('TARGET:', target)
                    try:
                        os.makedirs(os.path.dirname(target))
                    except:
                        pass
                    apply_and_remove_lock(src)
                    shutil.copy(src, os.path.splitext(target)[0] + '.mp3')
                else:
                    try:
                        os.makedirs(os.path.dirname(target))
                    except:
                        pass
                    apply_and_remove_lock(src)
                    out, _ = (ffmpeg
                        .input(src)
                        .output(os.path.splitext(target)[0] + '.mp3', format="mp3", audio_bitrate=320000)
                        # .overwrite_output()
                        .run(capture_stdout=True)
                    )
        else:
            print('File already exists or excluded from conversion')

        # Delete source file
        os.remove(src)

# remove empty directories
for root, dirs, files in os.walk(srcDir, topdown=False):
    for dir in dirs:
        try:
            os.rmdir(os.path.join(root, dir))
        except OSError:
            pass
