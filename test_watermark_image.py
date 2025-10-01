#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试图片水印功能
"""

from PIL import Image, ImageDraw

def create_test_watermark():
    """创建测试水印图片"""
    # 创建一个简单的PNG水印图片（带透明通道）
    width, height = 200, 100
    watermark = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark)
    
    # 绘制一个简单的Logo
    draw.rectangle([10, 10, 190, 90], fill=(255, 0, 0, 128))  # 半透明红色矩形
    draw.ellipse([50, 30, 150, 70], fill=(0, 255, 0, 128))   # 半透明绿色椭圆
    draw.text((70, 40), "LOGO", fill=(255, 255, 255, 255))   # 白色文字
    
    # 保存水印图片
    watermark.save('test_watermark.png', 'PNG')
    print("测试水印图片已创建: test_watermark.png")

if __name__ == "__main__":
    create_test_watermark()
