import os
from collections import defaultdict


def find_duplicates_by_size(directory, size_threshold=10 * 1024 * 1024):
    """
    找到指定目录中重复的文件，依据是文件大小相同且超过指定大小。

    :param directory: 要扫描的目录路径
    :param size_threshold: 文件大小阈值（默认 10MB）
    :return: 一个字典，键为文件大小，值为具有相同大小的文件列表
    """
    size_to_files = defaultdict(list)

    # 遍历目录及子目录中的所有文件
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                if file_size > size_threshold:
                    size_to_files[file_size].append(file_path)
            except Exception as e:
                print(f"无法处理文件 {file_path}: {e}")

    # 过滤出重复的文件（即具有相同大小的文件）
    duplicates = {size: paths for size, paths in size_to_files.items() if len(paths) > 1}
    return duplicates


def delete_duplicates(duplicates, preferred_dir):
    """
    删除重复文件，优先删除指定目录中的文件。

    :param duplicates: 重复文件的字典，键为文件大小，值为具有相同大小的文件列表
    :param preferred_dir: 优先删除的目录路径
    """
    for size, files in duplicates.items():
        # 按优先目录排序，优先删除 preferred_dir 中的文件
        files_sorted = sorted(files, key=lambda x: x.startswith(preferred_dir), reverse=True)
        # 保留第一个文件，删除其他文件
        for file_to_delete in files_sorted[1:]:
            try:
                os.remove(file_to_delete)
                print(f"已删除文件: {file_to_delete}")
            except Exception as e:
                print(f"无法删除文件 {file_to_delete}: {e}")
        print(f"保留文件: {files_sorted[0]}")


def main():
    directory =r"\\qunhui\home\Photos"
    preferred_dir = r"\\qunhui\home\Photos\未分类"

    if not os.path.isdir(directory):
        print("无效的扫描目录路径！")
        return
    if not os.path.isdir(preferred_dir):
        print("无效的优先删除目录路径！")
        return

    duplicates = find_duplicates_by_size(directory)

    if not duplicates:
        print("没有找到超过 10MB 且大小相同的重复文件。")
    else:
        print("发现重复文件，开始删除...")
        delete_duplicates(duplicates, preferred_dir)
        print("删除完成！")


if __name__ == "__main__":
    main()
