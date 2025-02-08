import os
import shutil
import subprocess


def capture_frame(video_path):
    """
    Capture a frame from the video at the specified time and save it as a JPG.

    :param video_path: Path to the input video file
    :param time: Time to capture the frame (format: HH:MM:SS or seconds)
    """
    # output_path: Path to save the output JPG file (eg: 'S01E01-thumb.jpg')
    output_path = video_path.replace('.mp4', '-thumb.jpg').replace('.mkv', '-thumb.jpg')
    time = '00:01:41'
    command = [
        'ffmpeg',
        '-ss', str(time),
        '-i', video_path,
        '-frames:v', '1',
        '-an',  # Disable audio
        '-y',  # Overwrite output files without asking
        output_path
    ]
    subprocess.run(command, check=True)
    print(f"Frame captured at {time} and saved to {output_path}")


def process_directory(directory):
    """
    Recursively process all MP4 files in the specified directory.

    :param directory: Path to the directory to process
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp4') or file.lower().endswith('.mkv'):
                video_path = os.path.join(root, file)
                capture_frame(video_path)


def find_season_cover(series_root_directory):
    """
    Recursively find the first JPG image in each season directory and use it as the season cover image.

    :param series_root_directory: Path to the series root directory containing season directories
    """
    for root, dirs, _ in os.walk(series_root_directory):
        for dir_name in dirs:
            season_directory = str(os.path.join(root, dir_name))
            for _, _, files in os.walk(season_directory):
                files = sorted(files)  # Sort files by name
                for file in files:
                    if file.lower().endswith('.jpg'):
                        image_path = os.path.join(season_directory, file)
                        output_path = os.path.join(series_root_directory,
                                                   f"season{dir_name.replace('S', '')}-poster.jpg")
                        shutil.copyfile(image_path, output_path)
                        print(f"Season cover copied from {image_path} to {output_path}")
                        break
                break


if __name__ == '__main__':
    process_directory(r'\\qunhui\usbshare1\剧集\熊出没')  # Replace with the path to your video directory
    # find_season_cover(r'\\qunhui\usbshare1\剧集\猫和老鼠')  # Replace with the path to your video directory
