import os
import re
import shutil


def delete_dir(dir_path, dir_name):
    for root, dirs, files in os.walk(dir_path):
        for dir_child in dirs:
            if dir_child == dir_name:
                shutil.rmtree(os.path.join(root, dir_child))
                print("删除目录：", os.path.join(root, dir_child))
            else:
                print("未找到目录：", os.path.join(root, dir_child))
        # break

episode_number_def = 0

def parse_file_name(file_name, season):
    # Rename the MP4 file according to Jellyfin rules
    # 安全警长啦咘啦哆.An.Quan.Jing.Zhang.La.Bu.La.Duo.S01E01.2022.2160p.HQ.WEB-DL.AAC.H265-HDSWEB.mp4
    match = re.search(rf"({season}E\d+)", file_name)
    if match:
        return match.group(1)
    # Gourd.Brothers.1986.E01.Webrip.1080p.x265.10bit.AAC.MNHD-FRDS
    match = re.search(r"\.(E\d+)\.", file_name)
    if match:
        return f"{season}{match.group(1)}"
    # 超级飞侠 第09集 迷路的小羚羊-超高清 4K.mp4
    match = re.search(r"第(\d+)集", file_name)
    if match:
        episode_number = f"{season}E{match.group(1)}"
        title_match = re.search(r"第\d+集 (.+?)-", file_name)
        if title_match:
            episode_title = title_match.group(1)
            return f"{episode_number} {episode_title}"
        title_match = re.search(r"第\d+集 (.+?)_", file_name)
        if title_match:
            episode_title = title_match.group(1)
            return f"{episode_number} {episode_title}"
        title_match = re.search(r"第\d+集 (.+?)\.", file_name)
        if title_match:
            episode_title = title_match.group(1)
            return f"{episode_number} {episode_title}"
        return episode_number
    # 3 蒙古国恐龙之旅（上）4K.mp4
    # 1 巴西的消防演习 4K.mp4
    match = re.search(r"^(\d+) (.+?)$", file_name)
    if match:
        episode_number = f"{season}E{match.group(1)}"
        episode_title = match.group(2).replace("_4K","").replace("4K","").strip()
        return f"{episode_number} {episode_title}"
    # # 01 摩纳哥快车 4K.mp4
    # match = re.search(r"(\d{2}) (.+?) ", file_name)
    # if match:
    #     episode_number = f"{season}E{match.group(1)}"
    #     episode_title = match.group(2)
    #     return f"{episode_number} {episode_title}"
    # # 阿尔卑斯火车救援_4K.mp4
    # match = re.search(r"(.+?)_", file_name)
    # if match:
    #     episode_title = match.group(1)
    #     global episode_number_def
    #     episode_number_def=episode_number_def+1
    #     return f"{season}E{episode_number_def} {episode_title}"
    return None


def rename_mp4_files(dir_path):
    subtitle_extensions = ['.srt', '.ass']
    # last directory is the season directory
    season = os.path.basename(dir_path)
    for root, dirs, files in os.walk(dir_path):
        files = sorted(files)  # Sort files by name
        for file in files:
            file_path = os.path.join(root, file)
            if file.lower().endswith('.nfo'):
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                else:
                    print(f"File not found: {file_path}")
                continue
            if file.lower().endswith(f'.mp4') or file.lower().endswith(f'.mkv'):
                base_name = os.path.splitext(file)[0]
                file_format = os.path.splitext(file)[1]
                mp4_path = os.path.join(root, file)

                # Rename the MP4 file according to Jellyfin rules
                # 安全警长啦咘啦哆.An.Quan.Jing.Zhang.La.Bu.La.Duo.S01E01.2022.2160p.HQ.WEB-DL.AAC.H265-HDSWEB.mp4
                match = parse_file_name(base_name, season)
                if match:
                    # Delete files with the same base name but different extensions
                    for other_file in files:
                        other_ext = os.path.splitext(other_file)[1].lower()
                        if other_file != file and os.path.splitext(other_file)[0].startswith(
                                base_name) and other_ext not in subtitle_extensions:
                            os.remove(os.path.join(root, other_file))
                            print(f"Deleted: {os.path.join(root, other_file)}")

                    new_name = f"{match}{file_format}"
                    new_path = os.path.join(root, new_name)
                    os.rename(mp4_path, new_path)
                    print(f"Renamed: {mp4_path} to {new_path}")
                else:
                    print(f"Skipped: {mp4_path}")
        break


if __name__ == '__main__':
    rename_mp4_files(r"\\qunhui\usbshare1\剧集\熊出没\S04")
