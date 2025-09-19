#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片水印添加工具
从图片EXIF信息中提取拍摄时间作为水印
"""

import os
import argparse
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_exif_date(image_path):
    """从图片EXIF信息中提取拍摄日期"""
    try:
        exif_dict = piexif.load(image_path)
        
        # 尝试从EXIF中获取拍摄时间
        if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            # 格式: YYYY:MM:DD HH:MM:SS
            date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            return date_obj.strftime('%Y年%m月%d日')
        
        # 如果没有原始时间，尝试获取数字化的时间
        elif '0th' in exif_dict and piexif.ImageIFD.DateTime in exif_dict['0th']:
            date_str = exif_dict['0th'][piexif.ImageIFD.DateTime].decode('utf-8')
            date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            return date_obj.strftime('%Y年%m月%d日')
            
    except Exception as e:
        logger.warning(f"无法从 {image_path} 读取EXIF信息: {e}")
    
    return None

def add_watermark(image_path, output_path, text, font_size=36, color=(255, 255, 255), position='右下角'):
    """给图片添加水印"""
    try:
        # 打开图片
        image = Image.open(image_path).convert('RGBA')
        width, height = image.size
        
        # 创建透明层用于水印
        txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # 尝试使用系统字体，如果失败使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("Arial", font_size)
            except:
                font = ImageFont.load_default()
        
        # 计算文本尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算水印位置
        if position == '左上角':
            x = 20
            y = 20
        elif position == '居中':
            x = (width - text_width) // 2
            y = (height - text_height) // 2
        elif position == '右上角':
            x = width - text_width - 20
            y = 20
        elif position == '左下角':
            x = 20
            y = height - text_height - 20
        else:  # 右下角
            x = width - text_width - 20
            y = height - text_height - 20
        
        # 添加文字阴影效果
        shadow_color = (0, 0, 0, 128)
        draw.text((x+2, y+2), text, font=font, fill=shadow_color)
        
        # 添加主要文字
        draw.text((x, y), text, font=font, fill=color)
        
        # 合并图片和水印
        watermarked = Image.alpha_composite(image, txt_layer)
        
        # 保存图片（根据原格式）
        if image_path.lower().endswith(('.png', '.gif', '.bmp')):
            watermarked.save(output_path)
        else:
            watermarked.convert('RGB').save(output_path)
            
        logger.info(f"成功添加水印: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"处理图片 {image_path} 时出错: {e}")
        return False

def process_directory(input_dir, font_size=36, color=(255, 255, 255), position='右下角'):
    """处理目录中的所有图片"""
    # 创建输出目录
    output_dir = os.path.join(input_dir, f"{os.path.basename(input_dir)}_watermark")
    os.makedirs(output_dir, exist_ok=True)
    
    # 支持的图片格式
    supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif')
    
    processed_count = 0
    error_count = 0
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_formats):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            # 获取EXIF日期
            watermark_text = get_exif_date(input_path)
            
            # 如果没有EXIF日期，使用当前日期
            if not watermark_text:
                watermark_text = datetime.now().strftime('%Y年%m月%d日')
                logger.info(f"{filename} 无EXIF信息，使用当前日期")
            
            # 添加水印
            if add_watermark(input_path, output_path, watermark_text, font_size, color, position):
                processed_count += 1
            else:
                error_count += 1
    
    logger.info(f"处理完成: {processed_count} 成功, {error_count} 失败")
    return processed_count, error_count

def parse_color(color_str):
    """解析颜色字符串"""
    if color_str.startswith('#'):
        # HEX格式: #RRGGBB
        color_str = color_str[1:]
        if len(color_str) == 6:
            return tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
    elif ',' in color_str:
        # RGB格式: 255,255,255
        return tuple(int(x.strip()) for x in color_str.split(','))
    
    raise ValueError("颜色格式无效，请使用 #RRGGBB 或 R,G,B 格式")

def main():
    parser = argparse.ArgumentParser(description='图片水印添加工具')
    parser.add_argument('input_dir', help='输入图片目录路径')
    parser.add_argument('--font-size', type=int, default=36, help='字体大小 (默认: 36)')
    parser.add_argument('--color', default='255,255,255', help='水印颜色 (格式: #RRGGBB 或 R,G,B, 默认: 255,255,255)')
    parser.add_argument('--position', choices=['左上角', '右上角', '左下角', '右下角', '居中'], 
                       default='右下角', help='水印位置 (默认: 右下角)')
    
    args = parser.parse_args()
    
    # 验证输入目录
    if not os.path.isdir(args.input_dir):
        logger.error(f"目录不存在: {args.input_dir}")
        return
    
    # 解析颜色
    try:
        color = parse_color(args.color)
    except ValueError as e:
        logger.error(f"颜色解析错误: {e}")
        return
    
    # 处理目录
    process_directory(args.input_dir, args.font_size, color, args.position)

if __name__ == '__main__':
    main()
