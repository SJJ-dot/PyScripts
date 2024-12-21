import os
import re
import traceback
from datetime import datetime

import piexif
from PIL import Image, PngImagePlugin, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

import ffmpeg


def set_creation_time(input_file, creation_time):
    # 检查视频文件原来是否有创建时间
    probe = ffmpeg.probe(input_file)
    for stream in probe['streams']:
        if stream['codec_type'] == 'video':
            if 'tags' in stream:
                if 'creation_time' in stream['tags']:
                    # print("Creation time already exists:", stream['tags']['creation_time'])
                    return False
    tmp_file = os.path.join(os.path.dirname(input_file), 'tmp.mp4')
    try:
        creation_time = datetime.strptime(creation_time, "%Y%m%d_%H%M%S").strftime("%Y%m%dT%H:%M:%S")
        ffmpeg.input(input_file).output(tmp_file, metadata=f'creation_time={creation_time}', vcodec='h264_nvenc').run()
        os.remove(input_file)
        os.rename(tmp_file, input_file)
        print(f"Added creation time: {creation_time}", input_file)
        return True
    except Exception as e:
        # 打印堆栈信息
        print("Error setting creation time:", e)
        traceback.print_exc()
        os.remove(tmp_file)
        return False


def validate_and_fix_exif(exif_dict):
    """验证并修复EXIF数据，确保符合piexif.dump的要求"""
    for ifd in list(exif_dict.keys()):  # 遍历字典的键，确保不会修改字典大小
        if not isinstance(exif_dict[ifd], dict):
            print(f"Skipping non-dict IFD: {ifd}, type: {type(exif_dict[ifd])}")
            del exif_dict[ifd]  # 删除非字典类型的IFD
            continue

        # 使用 list() 来避免在迭代时修改字典
        for tag, value in list(exif_dict[ifd].items()):
            # 忽略空值或类型完全错误的字段
            if value is None:
                del exif_dict[ifd][tag]
                continue

            # 修复常见错误类型
            if isinstance(value, int):
                # 如果字段需要字符串或字节，转换为字符串字节
                exif_dict[ifd][tag] = str(value).encode('utf-8')
            elif not isinstance(value, (bytes, str, int, tuple)):
                # 如果类型完全不符合，移除字段
                del exif_dict[ifd][tag]

    return exif_dict


def add_shooting_time(file_path, shooting_time=None):
    # 打开图像文件
    img = Image.open(file_path)
    # 检查图像文件是否包含EXIF信息
    if 'exif' in img.info:
        # 获取EXIF信息
        exif_dict = piexif.load(img.info['exif'])
    else:
        # 创建一个新的EXIF字典
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

    # 检查是否有拍摄时间
    if piexif.ExifIFD.DateTimeOriginal not in exif_dict['Exif'] or not validate_date(
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8'), "%Y:%m:%d %H:%M:%S"):
        # 如果没有拍摄时间，则添加拍摄时间
        if shooting_time is None:
            shooting_time = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        else:
            shooting_time = datetime.strptime(shooting_time, "%Y%m%d_%H%M%S").strftime("%Y:%m:%d %H:%M:%S")
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = shooting_time.encode('utf-8')

        # 转换EXIF信息为字节
        exif_bytes = piexif.dump(validate_and_fix_exif(exif_dict))
        # 如果图像是RGBA模式，转换为RGB模式
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        # 保存图像文件，带有新的EXIF信息
        tmp_file = os.path.join(os.path.dirname(file_path), 'tmp.jpg')
        img.save(tmp_file, "jpeg", exif=exif_bytes)
        os.remove(file_path)
        os.rename(tmp_file, file_path)
        print(f"Added shooting time: {shooting_time}", file_path)
    else:
        # print("Shooting time already exists.", exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal], file_path)
        pass


def png_to_jpg(file_path):
    if not file_path.lower().endswith('.png'):
        return file_path
    # 打开PNG图像文件
    img = Image.open(file_path)
    # Convert image to RGB mode if it is in RGBA mode
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    # 创建一个新的JPG文件
    jpg_file_path = file_path.lower().replace('.png', '.jpg')
    # 保存图像文件为JPG格式
    img.save(jpg_file_path, "jpeg")
    print(f"Converted PNG to JPG: {jpg_file_path}")
    # 删除PNG文件
    os.remove(file_path)
    return jpg_file_path


def validate_date(date_str, format="%Y%m%d_%H%M%S"):
    try:
        datetime.strptime(date_str, format)
        # 时间不能超过当前时间
        if datetime.strptime(date_str, format) > datetime.now():
            return False
        return True
    except ValueError:
        return False


def remove_uuid(filename):
    # 匹配有连字符的 UUID
    uuid_with_hyphens = r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
    # 匹配无连字符的 UUID（至少 32 位）
    uuid_without_hyphens = r'[a-fA-F0-9]{32,}'

    # 1. 检查并移除有连字符的 UUID
    if re.search(uuid_with_hyphens, filename):
        # 替换有连字符的 UUID
        cleaned_filename = re.sub(uuid_with_hyphens, '', filename)
        # 去除多余符号
        return cleaned_filename

    # 2. 检查并移除无连字符的 UUID
    matches = re.finditer(uuid_without_hyphens, filename)
    for match in matches:
        uuid = match.group()
        if len(uuid) == 32:
            cleaned_filename = filename.replace(uuid, '')
            # 去除多余符号
            return cleaned_filename
        if len(uuid) >= 42:
            # 检查是否是时间戳，前后是否紧邻数字
            if re.search(r'^\d{10,}', uuid):
                # 开头包含时间戳，去除UUID最后的32个字符
                cleaned_filename = filename.replace(uuid[-32:], '')
                return cleaned_filename
            if re.search(r'\d{10,}$', uuid):
                # 结尾包含UUID，去除最前的32个字符
                cleaned_filename = filename.replace(uuid[:32], '')
                return cleaned_filename
    # 未匹配到 UUID，返回原文件名
    return filename


def parse_date(file_path):
    # 尝试获取拍摄时间，返回格式为 yyyyMMdd_HHmmss
    if file_path.lower().endswith('.png'):
        #     尝试解析元数据
        img = Image.open(file_path)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
            if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                return exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
        metadata = {}
        # 提取 tEXt、zTXt 和 iTXt 块
        for key, value in img.info.items():
            if isinstance(value, PngImagePlugin.PngInfo):
                for k, v in value.items():
                    metadata[k] = v
            else:
                metadata[key] = value
        # 尝试从元数据中获取拍摄时间
        if 'Creation Time' in metadata:
            return metadata['Creation Time']
    # 获取文件名和扩展名
    file_name = os.path.basename(file_path)
    file_name = remove_uuid(file_name)
    #     MYXJ_20180317141344_fast.jpg
    match = re.search(r'(?<=_)\d{14}(?=_)', file_name)
    if match:
        # 将时间转换为日期 yyyyMMdd_HHmmss
        if validate_date(match.group(), "%Y%m%d%H%M%S"):
            return datetime.strptime(match.group(), "%Y%m%d%H%M%S").strftime("%Y%m%d_%H%M%S")
    match = re.search(r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{3}', file_name)
    if match:  # 提取匹配的时间部分
        datetime_str = match.group()
        # 转换为 datetime 格式（忽略毫秒部分）
        dt = datetime.strptime(datetime_str[: 19], "%Y-%m-%d-%H-%M-%S")
        # 格式化为目标日期格式
        return dt.strftime("%Y%m%d_%H%M%S")
    match = re.search(r'\d{8}_\d{6}', file_name)
    if match:
        if validate_date(match.group()):
            return match.group()
    # 正则表达式匹配日期和时间 2021-05-12-214815930.mp4
    pattern = r"(\d{4}-\d{2}-\d{2})-(\d{6})(\d{3})"
    match = re.search(pattern, file_name)
    if match:
        date_part = match.group(1)  # 日期部分
        time_part = match.group(2)  # 时间部分 (小时、分钟、秒)
        millis_part = match.group(3)  # 毫秒部分
        # 将时间格式化为标准格式
        return datetime.strptime(f"{date_part}-{time_part}", "%Y-%m-%d-%H%M%S").strftime("%Y%m%d_%H%M%S")

    match = re.search(r'(\d{2})(\d{2})(\d{2})(\d{6})(\d{4})', file_name)
    if match:
        year = int(match.group(1)) + 2000  # 假设年份为 2000 年之后2303221954461692
        month = match.group(2)
        day = match.group(3)
        time = match.group(4)[:6]  # 提取小时分钟秒
        # 格式化为 yyyyMMdd_HHmmss
        if validate_date(f"{year}{month}{day}_{time}"):
            return f"{year}{month}{day}_{time}"
    #     照片20121128 172927.jpg
    # 正则表达式匹配日期和时间
    pattern = r'(\d{8})\s(\d{6})'
    match = re.search(pattern, file_name)

    if match:
        date_part = match.group(1)  # 日期部分 (yyyyMMdd)
        time_part = match.group(2)  # 时间部分 (HHmmss)
        if validate_date(f"{date_part}_{time_part}"):
            return f"{date_part}_{time_part}"
    pattern = r'(\d{8})_(\d{6})'
    match = re.search(pattern, file_name)
    if match:
        date_part = match.group(1)  # 日期部分 (yyyyMMdd)
        time_part = match.group(2)  # 时间部分 (HHmmss)
        if validate_date(f"{date_part}_{time_part}"):
            return f"{date_part}_{time_part}"

    match = re.search(r'20\d{12}(?=\.jpg)', file_name)
    if match:
        date_part = match.group()[:8]  # 日期部分 (yyyyMMdd)
        time_part = match.group()[8:14]
        if validate_date(f"{date_part}_{time_part}"):
            return f"{date_part}_{time_part}"

    # 2021-05-12-214709.mp4
    match = re.search(r'(\d{4}-\d{2}-\d{2})-(\d{6})', file_name)
    if match:
        date_part = match.group(1)
        time_part = match.group(2)
        shooting_time = f"{date_part}_{time_part}".replace('-', '')
        if validate_date(shooting_time):
            return shooting_time

    # Screenshot_2015-04-27-09-24-58.jpeg
    match = re.search(r'(\d{4}-\d{2}-\d{2})-(\d{2}-\d{2}-\d{2})', file_name)
    if match:
        date_part = match.group(1)
        time_part = match.group(2)
        shooting_time = f"{date_part}_{time_part}".replace('-', '')
        if validate_date(shooting_time):
            return shooting_time

        # 正则表达式匹配 17 位时间戳，例如 1726136788549698.jpg
    # 匹配时间戳
    # 匹配最长连续数字share_fd00214c34d7f7ffe1c138a6dbd194301733885973551
    match = max(re.findall(r'\d+', file_name), key=len)
    # match = re.search(r'1\d{15}', file_name)
    if match:
        if len(match) == 16:
            timestamp = int(match)
            shooting_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y%m%d_%H%M%S")
            if validate_date(shooting_time):
                return shooting_time
        # 例如：1380164325634.jpg 包含时间戳日期
        if len(match) == 13:
            timestamp = int(match)
            # 将时间戳转换为日期 yyyyMMdd_HHmmss
            shooting_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y%m%d_%H%M%S")
            if validate_date(shooting_time):
                return shooting_time
    return None


def set_photo_date(file_path):
    # print("Processing:", file_path)
    try:
        shooting_time = parse_date(file_path)
        if shooting_time:
            try:
                # print("Shooting time:", shooting_time)
                file_path = png_to_jpg(file_path)
                if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                    add_shooting_time(file_path, shooting_time)
                elif file_path.lower().endswith('.mp4'):
                    set_creation_time(file_path, shooting_time)
                else:
                    print(f"Unsupported file format: {file_path}")
            except Exception as e:
                print("Error processing file:", file_path, e)
                traceback.print_exc()
    except:
        pass


def set_photo_date_all(dir):
    idx = 0
    for root, dirs, files in os.walk(dir):
        dirs[:] = [d for d in dirs if d != '@eaDir']
        for file in files:
            file_path = os.path.join(root, file)
            set_photo_date(file_path)
            idx += 1
            if idx % 100 == 0:
                print(f"Processed {idx} files.")


if __name__ == '__main__':
    # set_photo_date(r"87664848.png")
    set_photo_date_all(r'\temp')
