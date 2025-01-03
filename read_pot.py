import struct
import zipfile

def decode_tag_code(tag_code_bytes):
    """从两个字节的标签码解码为字符."""
     # 移除可能存在的空字节
    tag_code_bytes = bytes(b for b in tag_code_bytes if b != 0x00)
    
    if len(tag_code_bytes) == 0:
        print("Warning: Tag code contains only null bytes. Skipping this entry.")
        return None

    try:
        # 尝试使用gb2312解码
        decoded_char = tag_code_bytes.decode('gb2312')
    except UnicodeDecodeError:
        try:
            # 如果gb2312失败，则尝试使用gbk解码
            decoded_char = tag_code_bytes.decode('gbk')
        except UnicodeDecodeError as e:
            print(f"Failed to decode the tag code: {e}")
            return None

    return decoded_char


def read_pot_file(pot_filepath):
    samples = []
    char_list = {}
    with open(pot_filepath, 'rb') as fp:
        while True:
            # 读取样本大小（Sample size）
            sample_size_data = fp.read(2)
            if len(sample_size_data) != 2:
                break  # 文件结束或读取失败
            sample_size = struct.unpack('<H', sample_size_data)[0]

            # 检查是否到达文件末尾
            if sample_size == 0:
                break

            # 读取标签码（Tag code GB）
            tag_code_data = fp.read(4)
            if len(tag_code_data) != 4:
                raise ValueError("Unexpected end of file while reading tag code")
            
            # 提取前两个字节并交换顺序
            tag_code_bytes = bytes([tag_code_data[1], tag_code_data[0]])  # 交换前两个字节

             # 解码标签码
            tag_code = decode_tag_code(tag_code_bytes)
            if tag_code is None:
                print(f"Warning: Unable to decode tag code {tag_code_data.hex()}. Skipping this entry.")
                continue

            # 读取笔画数（Stroke number）
            stroke_number_data = fp.read(2)
            if len(stroke_number_data) != 2:
                raise ValueError("Unexpected end of file while reading stroke number")
            stroke_number = struct.unpack('<H', stroke_number_data)[0]

            strokes = []
            for _ in range(stroke_number):
                points = []
                while True:
                    coordinate_data = fp.read(4)
                    if len(coordinate_data) != 4:
                        raise ValueError("Unexpected end of file while reading coordinates")
                    x, y = struct.unpack('<hh', coordinate_data)

                    # 笔画结束标志
                    if (x, y) == (-1, 0):
                        break
                    points.append((x, y))
                strokes.append(points)

            # 计算已经读取的字节数量
            bytes_read = 2 + 4 + 2 + (len(strokes) * 4) + sum(len(s) * 4 for s in strokes)

            # 读取字符结束标志（Character end tag）
            end_tag_data = fp.read(4)
            if len(end_tag_data) != 4:
                raise ValueError("Unexpected end of file while reading end tag")
            end_tag_x, end_tag_y = struct.unpack('<hh', end_tag_data)
            
            # 验证结束标签
            if (end_tag_x, end_tag_y) != (-1, -1):
                print(f"Warning: Invalid end tag encountered: ({end_tag_x}, {end_tag_y})")
                # 尝试继续读取下一个样本，而不是立即抛出异常

            # 将当前样本添加到列表中
            sample = {
                'sample_size': sample_size,
                'tag_code': tag_code,
                'stroke_number': stroke_number,
                'strokes': strokes
            }
            samples.append(sample)

            char_list.update({tag_code: strokes})  # 更新字典

            # 跳过剩余的字节以到达下一个样本
            remaining_bytes = sample_size - bytes_read - 4
            if remaining_bytes > 0:
                fp.seek(remaining_bytes, 1)
            elif remaining_bytes < 0:
                print(f"Warning: Sample size mismatch detected. Expected more data.")

    return samples, char_list

def read_pot_zip_file(zip_path, pot_name):
    samples = []
    char_list = {}
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        with zip_ref.open(pot_name) as fp:
            while True:
                # 读取样本大小（Sample size）
                sample_size_data = fp.read(2)
                if len(sample_size_data) != 2:
                    break  # 文件结束或读取失败
                sample_size = struct.unpack('<H', sample_size_data)[0]

                # 检查是否到达文件末尾
                if sample_size == 0:
                    break

                # 读取标签码（Tag code GB）
                tag_code_data = fp.read(4)
                if len(tag_code_data) != 4:
                    raise ValueError("Unexpected end of file while reading tag code")
                
                # 提取前两个字节并交换顺序
                tag_code_bytes = bytes([tag_code_data[1], tag_code_data[0]])  # 交换前两个字节

                # 解码标签码
                tag_code = decode_tag_code(tag_code_bytes)
                if tag_code is None:
                    print(f"Warning: Unable to decode tag code {tag_code_data.hex()}. Skipping this entry.")
                    continue

                # 读取笔画数（Stroke number）
                stroke_number_data = fp.read(2)
                if len(stroke_number_data) != 2:
                    raise ValueError("Unexpected end of file while reading stroke number")
                stroke_number = struct.unpack('<H', stroke_number_data)[0]

                strokes = []
                for _ in range(stroke_number):
                    points = []
                    while True:
                        coordinate_data = fp.read(4)
                        if len(coordinate_data) != 4:
                            raise ValueError("Unexpected end of file while reading coordinates")
                        x, y = struct.unpack('<hh', coordinate_data)

                        # 笔画结束标志
                        if (x, y) == (-1, 0):
                            break
                        points.append((x, y))
                    strokes.append(points)

                # 计算已经读取的字节数量
                bytes_read = 2 + 4 + 2 + (len(strokes) * 4) + sum(len(s) * 4 for s in strokes)

                # 读取字符结束标志（Character end tag）
                end_tag_data = fp.read(4)
                if len(end_tag_data) != 4:
                    raise ValueError("Unexpected end of file while reading end tag")
                end_tag_x, end_tag_y = struct.unpack('<hh', end_tag_data)
                
                # 验证结束标签
                if (end_tag_x, end_tag_y) != (-1, -1):
                    print(f"Warning: Invalid end tag encountered: ({end_tag_x}, {end_tag_y})")
                    # 尝试继续读取下一个样本，而不是立即抛出异常

                # 将当前样本添加到列表中
                sample = {
                    'sample_size': sample_size,
                    'tag_code': tag_code,
                    'stroke_number': stroke_number,
                    'strokes': strokes
                }
                samples.append(sample)

                char_list.update({tag_code: strokes})  # 更新字典

                # 跳过剩余的字节以到达下一个样本
                remaining_bytes = sample_size - bytes_read - 4
                if remaining_bytes > 0:
                    fp.seek(remaining_bytes, 1)
                elif remaining_bytes < 0:
                    print(f"Warning: Sample size mismatch detected. Expected more data.")

    return samples, char_list


# 示例用法
if __name__ == "__main__":
    pot_filepath = "./CASIA/OLHWDB1.0-1.2/001.pot"
    samples, char_list = read_pot_file(pot_filepath)
    print(char_list['迂'])

    # for i, sample in enumerate(samples):
    #     print(f"Sample {i + 1}:")
    #     print(f"  Sample Size: {sample['sample_size']}")
    #     print(f"  Tag Code: {sample['tag_code']}")
    #     print(f"  Stroke Number: {sample['stroke_number']}")
    #     for j, stroke in enumerate(sample['strokes']):
    #         print(f"  Stroke {j + 1}:")
    #         for point in stroke:
    #             print(f"    Point: {point}")
