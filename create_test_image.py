#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试图片并添加EXIF信息
"""

from PIL import Image, ImageDraw
import piexif
from datetime import datetime

def create_test_image():
    # 创建一个简单的测试图片
    img = Image.new('RGB', (800, 600), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # 添加一些文本（使用英文避免编码问题）
    draw.text((400, 300), "Test Image", fill='black', anchor='mm')
    draw.text((400, 330), "For Watermark Testing", fill='darkblue', anchor='mm')
    
    # 添加EXIF信息
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: "Test Camera".encode('utf-8'),
            piexif.ImageIFD.Model: "Test Model".encode('utf-8'),
            piexif.ImageIFD.DateTime: datetime.now().strftime('%Y:%m:%d %H:%M:%S').encode('utf-8')
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: datetime(2023, 10, 15, 14, 30, 25).strftime('%Y:%m:%d %H:%M:%S').encode('utf-8'),
            piexif.ExifIFD.DateTimeDigitized: datetime(2023, 10, 15, 14, 30, 25).strftime('%Y:%m:%d %H:%M:%S').encode('utf-8')
        }
    }
    
    # 转换EXIF数据
    exif_bytes = piexif.dump(exif_dict)
    
    # 保存图片
    img.save('test_image.jpg', exif=exif_bytes)
    print("测试图片已创建: test_image.jpg")
    
    # 再创建一个没有EXIF的图片（使用英文）
    img2 = Image.new('RGB', (800, 600), color='lightgreen')
    draw2 = ImageDraw.Draw(img2)
    draw2.text((400, 300), "No EXIF Test Image", fill='black', anchor='mm')
    img2.save('test_no_exif.jpg')
    print("无EXIF测试图片已创建: test_no_exif.jpg")

if __name__ == '__main__':
    create_test_image()
