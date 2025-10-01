#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
水印文件本地应用 - GUI版本
支持Windows和MacOS的跨平台桌面应用
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import piexif

# GUI框架选择
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
    from tkinter.font import Font
except ImportError:
    print("错误: 需要tkinter库，请确保Python安装正确")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("水印文件本地应用")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # 应用数据
        self.images = []  # 存储导入的图片路径
        self.current_image_index = -1
        self.watermark_settings = {
            'text': '水印文字',
            'font_family': 'Arial',
            'font_size': 36,
            'font_color': (255, 255, 255),
            'font_bold': False,
            'font_italic': False,
            'opacity': 80,
            'position': '右下角',
            'rotation': 0,
            'shadow_enabled': False,
            'stroke_enabled': False,
            'image_watermark_path': None,
            'image_watermark_scale': 100,
            'image_watermark_opacity': 80
        }
        
        self.templates = {}
        self.current_template = None
        
        # 输出设置
        self.output_settings = {
            'output_dir': '',
            'naming_rule': 'original',
            'prefix': 'wm_',
            'suffix': '_watermarked',
            'format': 'JPEG',
            'quality': 90,
            'resize_enabled': False,
            'resize_width': 0,
            'resize_height': 0,
            'resize_percent': 100
        }
        
        # 创建界面
        self.setup_ui()
        
        # 加载配置
        self.load_config()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 顶部工具栏
        self.create_toolbar(main_frame)
        
        # 主内容区域
        self.create_main_content(main_frame)
        
        # 底部状态栏
        self.create_statusbar(main_frame)
    
    def create_toolbar(self, parent):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 文件操作按钮
        ttk.Button(toolbar, text="导入图片", command=self.import_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导入文件夹", command=self.import_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空列表", command=self.clear_images).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # 模板操作按钮
        ttk.Button(toolbar, text="保存模板", command=self.save_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="加载模板", command=self.load_template).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # 导出按钮
        ttk.Button(toolbar, text="导出设置", command=self.show_export_settings).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="批量导出", command=self.batch_export).pack(side=tk.LEFT, padx=2)
    
    def create_main_content(self, parent):
        """创建主内容区域"""
        # 左侧图片列表
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.N, tk.S), padx=(0, 10))
        
        # 图片列表标签
        ttk.Label(left_frame, text="图片列表", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # 图片列表框架
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 图片列表
        self.image_listbox = tk.Listbox(list_frame, width=25, height=15)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.image_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_listbox.config(yscrollcommand=scrollbar.set)
        
        # 中间预览区域
        middle_frame = ttk.Frame(parent)
        middle_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10)
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        
        # 预览标签
        ttk.Label(middle_frame, text="预览", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # 预览画布
        self.preview_canvas = tk.Canvas(middle_frame, bg='white', width=400, height=300)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.preview_canvas.bind('<Button-1>', self.on_canvas_click)
        self.preview_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        
        # 右侧水印设置
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=1, column=2, sticky=(tk.E, tk.N, tk.S), padx=(10, 0))
        
        # 水印设置标签
        ttk.Label(right_frame, text="水印设置", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # 创建设置面板
        self.create_watermark_settings(right_frame)
    
    def create_watermark_settings(self, parent):
        """创建水印设置面板"""
        # 创建滚动框架
        canvas = tk.Canvas(parent, width=300, height=500)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 水印类型选择
        type_frame = ttk.LabelFrame(scrollable_frame, text="水印类型", padding="5")
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.watermark_type = tk.StringVar(value="text")
        ttk.Radiobutton(type_frame, text="文字水印", variable=self.watermark_type, 
                       value="text", command=self.on_watermark_type_change).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="图片水印", variable=self.watermark_type, 
                       value="image", command=self.on_watermark_type_change).pack(anchor=tk.W)
        
        # 文字水印设置
        self.text_settings_frame = ttk.LabelFrame(scrollable_frame, text="文字设置", padding="5")
        self.text_settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 水印文字
        ttk.Label(self.text_settings_frame, text="水印文字:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.text_entry = ttk.Entry(self.text_settings_frame, width=20)
        self.text_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.text_entry.insert(0, self.watermark_settings['text'])
        self.text_entry.bind('<KeyRelease>', self.on_text_change)
        
        # 字体设置
        ttk.Label(self.text_settings_frame, text="字体:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.font_family = ttk.Combobox(self.text_settings_frame, width=18, values=self.get_available_fonts())
        self.font_family.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.font_family.set(self.watermark_settings['font_family'])
        self.font_family.bind('<<ComboboxSelected>>', self.on_font_change)
        
        # 字体大小
        ttk.Label(self.text_settings_frame, text="字号:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.font_size = ttk.Spinbox(self.text_settings_frame, from_=8, to=200, width=18)
        self.font_size.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.font_size.set(self.watermark_settings['font_size'])
        self.font_size.bind('<KeyRelease>', self.on_font_change)
        
        # 字体样式
        style_frame = ttk.Frame(self.text_settings_frame)
        style_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        self.bold_var = tk.BooleanVar(value=self.watermark_settings['font_bold'])
        self.italic_var = tk.BooleanVar(value=self.watermark_settings['font_italic'])
        
        ttk.Checkbutton(style_frame, text="粗体", variable=self.bold_var, 
                       command=self.on_font_style_change).pack(side=tk.LEFT)
        ttk.Checkbutton(style_frame, text="斜体", variable=self.italic_var, 
                       command=self.on_font_style_change).pack(side=tk.LEFT)
        
        # 颜色选择
        ttk.Label(self.text_settings_frame, text="颜色:").grid(row=4, column=0, sticky=tk.W, pady=2)
        color_frame = ttk.Frame(self.text_settings_frame)
        color_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.color_button = ttk.Button(color_frame, text="选择颜色", command=self.choose_color)
        self.color_button.pack(side=tk.LEFT)
        
        self.color_preview = tk.Canvas(color_frame, width=30, height=20, bg=self.rgb_to_hex(self.watermark_settings['font_color']))
        self.color_preview.pack(side=tk.LEFT, padx=(5, 0))
        
        # 图片水印设置（初始隐藏）
        self.image_settings_frame = ttk.LabelFrame(scrollable_frame, text="图片设置", padding="5")
        
        # 图片水印文件选择
        ttk.Label(self.image_settings_frame, text="水印图片:").grid(row=0, column=0, sticky=tk.W, pady=2)
        image_frame = ttk.Frame(self.image_settings_frame)
        image_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.image_path_var = tk.StringVar(value="未选择")
        self.image_path_label = ttk.Label(image_frame, textvariable=self.image_path_var, width=15)
        self.image_path_label.pack(side=tk.LEFT)
        
        ttk.Button(image_frame, text="选择图片", command=self.choose_watermark_image).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(image_frame, text="清除", command=self.clear_watermark_image).pack(side=tk.LEFT, padx=(5, 0))
        
        # 图片缩放设置
        ttk.Label(self.image_settings_frame, text="缩放比例:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.image_scale_var = tk.IntVar(value=self.watermark_settings['image_watermark_scale'])
        image_scale_scale = ttk.Scale(self.image_settings_frame, from_=10, to=200, variable=self.image_scale_var, 
                                     orient=tk.HORIZONTAL, command=self.on_image_scale_change)
        image_scale_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        image_scale_label = ttk.Label(self.image_settings_frame, textvariable=self.image_scale_var)
        image_scale_label.grid(row=1, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        ttk.Label(self.image_settings_frame, text="%").grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # 图片透明度设置
        ttk.Label(self.image_settings_frame, text="透明度:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.image_opacity_var = tk.IntVar(value=self.watermark_settings['image_watermark_opacity'])
        image_opacity_scale = ttk.Scale(self.image_settings_frame, from_=0, to=100, variable=self.image_opacity_var, 
                                       orient=tk.HORIZONTAL, command=self.on_image_opacity_change)
        image_opacity_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        image_opacity_label = ttk.Label(self.image_settings_frame, textvariable=self.image_opacity_var)
        image_opacity_label.grid(row=2, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        ttk.Label(self.image_settings_frame, text="%").grid(row=2, column=3, sticky=tk.W, pady=2)
        
        # 位置设置
        self.create_position_settings(scrollable_frame)
        
        # 样式设置
        self.create_style_settings(scrollable_frame)
        
        # 初始显示文字设置
        self.on_watermark_type_change()
    
    def create_position_settings(self, parent):
        """创建位置设置面板"""
        pos_frame = ttk.LabelFrame(parent, text="位置设置", padding="5")
        pos_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 九宫格位置选择
        positions = ['左上角', '上中', '右上角', '左中', '居中', '右中', '左下角', '下中', '右下角']
        
        # 创建位置按钮网格
        grid_frame = ttk.Frame(pos_frame)
        grid_frame.pack(fill=tk.X)
        
        for i, pos in enumerate(positions):
            row = i // 3
            col = i % 3
            ttk.Button(grid_frame, text=pos, width=8, 
                      command=lambda p=pos: self.set_position(p)).grid(row=row, column=col, padx=2, pady=2)
        
        # 手动拖拽说明
        ttk.Label(pos_frame, text="提示: 点击预览图可手动放置水印", font=('Arial', 8)).pack(pady=(5, 0))
        
        # 旋转设置
        rot_frame = ttk.Frame(pos_frame)
        rot_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(rot_frame, text="旋转角度:").pack(side=tk.LEFT)
        self.rotation_var = tk.StringVar(value=str(self.watermark_settings['rotation']))
        rotation_entry = ttk.Entry(rot_frame, textvariable=self.rotation_var, width=8)
        rotation_entry.pack(side=tk.LEFT, padx=(5, 0))
        rotation_entry.bind('<KeyRelease>', self.on_rotation_change)
        
        ttk.Label(rot_frame, text="°").pack(side=tk.LEFT, padx=(2, 0))
    
    def create_style_settings(self, parent):
        """创建样式设置面板"""
        style_frame = ttk.LabelFrame(parent, text="样式设置", padding="5")
        style_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 透明度
        ttk.Label(style_frame, text="透明度:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.opacity_var = tk.IntVar(value=self.watermark_settings['opacity'])
        opacity_scale = ttk.Scale(style_frame, from_=0, to=100, variable=self.opacity_var, 
                                 orient=tk.HORIZONTAL, command=self.on_opacity_change)
        opacity_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        opacity_label = ttk.Label(style_frame, textvariable=self.opacity_var)
        opacity_label.grid(row=0, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        ttk.Label(style_frame, text="%").grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # 阴影效果
        self.shadow_var = tk.BooleanVar(value=self.watermark_settings['shadow_enabled'])
        ttk.Checkbutton(style_frame, text="阴影效果", variable=self.shadow_var, 
                       command=self.on_style_change).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 描边效果
        self.stroke_var = tk.BooleanVar(value=self.watermark_settings['stroke_enabled'])
        ttk.Checkbutton(style_frame, text="描边效果", variable=self.stroke_var, 
                       command=self.on_style_change).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def create_statusbar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # 图片计数
        self.count_var = tk.StringVar(value="图片: 0")
        count_label = ttk.Label(status_frame, textvariable=self.count_var)
        count_label.pack(side=tk.RIGHT)
    
    # 工具方法
    def get_available_fonts(self):
        """获取系统可用字体"""
        try:
            return sorted(list(set(ImageFont.getfonts())))
        except:
            return ['Arial', 'Times New Roman', 'Courier New', 'Verdana', 'Helvetica']
    
    def rgb_to_hex(self, rgb):
        """RGB元组转十六进制"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def hex_to_rgb(self, hex_color):
        """十六进制颜色转RGB元组"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def update_preview(self):
        """更新预览"""
        if self.current_image_index >= 0 and self.images:
            try:
                image_path = self.images[self.current_image_index]
                image = Image.open(image_path)
                
                # 调整预览大小
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                if canvas_width > 1 and canvas_height > 1:
                    # 计算缩放比例
                    img_width, img_height = image.size
                    scale = min(canvas_width / img_width, canvas_height / img_height) * 0.9
                    
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    # 缩放图片
                    preview_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 转换为PhotoImage
                    from PIL import ImageTk
                    self.preview_photo = ImageTk.PhotoImage(preview_image)
                    
                    # 清空画布并显示图片
                    self.preview_canvas.delete("all")
                    x = (canvas_width - new_width) // 2
                    y = (canvas_height - new_height) // 2
                    self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_photo)
                    
                    # 添加水印预览
                    self.draw_watermark_preview()
                    
            except Exception as e:
                logger.error(f"更新预览时出错: {e}")
    
    def draw_watermark_preview(self):
        """在预览图上绘制水印"""
        if not hasattr(self, 'preview_photo'):
            return
        
        # 获取当前图片尺寸
        image_path = self.images[self.current_image_index]
        original_image = Image.open(image_path)
        orig_width, orig_height = original_image.size
        
        # 获取预览图尺寸
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # 计算缩放比例
        scale = min(canvas_width / orig_width, canvas_height / orig_height) * 0.9
        
        # 计算水印在预览图上的位置
        if self.watermark_type.get() == "text":
            # 文字水印预览
            text = self.watermark_settings['text']
            if text:
                # 计算水印位置
                x, y = self.calculate_watermark_position(orig_width, orig_height, scale)
                
                # 绘制水印文本
                self.preview_canvas.create_text(
                    x, y, 
                    text=text,
                    fill=self.rgb_to_hex(self.watermark_settings['font_color']),
                    font=(self.watermark_settings['font_family'], 
                          int(self.watermark_settings['font_size'] * scale)),
                    anchor=tk.CENTER
                )
        
        else:
            # 图片水印预览
            if self.watermark_settings['image_watermark_path']:
                try:
                    # 加载水印图片
                    watermark_image = Image.open(self.watermark_settings['image_watermark_path'])
                    
                    # 计算水印缩放
                    watermark_scale = self.watermark_settings['image_watermark_scale'] / 100.0
                    wm_width = int(watermark_image.width * watermark_scale * scale)
                    wm_height = int(watermark_image.height * watermark_scale * scale)
                    
                    # 计算水印位置
                    x, y = self.calculate_watermark_position(orig_width, orig_height, scale)
                    
                    # 计算画布偏移
                    canvas_width = self.preview_canvas.winfo_width()
                    canvas_height = self.preview_canvas.winfo_height()
                    x_offset = (canvas_width - orig_width * scale) // 2
                    y_offset = (canvas_height - orig_height * scale) // 2
                    
                    # 调整位置为中心对齐
                    x += x_offset - wm_width // 2
                    y += y_offset - wm_height // 2
                    
                    # 创建临时预览图片
                    from PIL import ImageTk
                    preview_watermark = watermark_image.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
                    
                    # 应用透明度
                    opacity = self.watermark_settings['image_watermark_opacity']
                    if opacity < 100:
                        preview_watermark = preview_watermark.convert("RGBA")
                        alpha = preview_watermark.split()[3]
                        alpha = alpha.point(lambda p: p * opacity // 100)
                        preview_watermark.putalpha(alpha)
                    
                    preview_watermark_photo = ImageTk.PhotoImage(preview_watermark)
                    
                    # 保存引用防止垃圾回收
                    if not hasattr(self, 'preview_watermark_photos'):
                        self.preview_watermark_photos = []
                    self.preview_watermark_photos.append(preview_watermark_photo)
                    
                    # 绘制水印图片
                    self.preview_canvas.create_image(x, y, anchor=tk.NW, image=preview_watermark_photo)
                    
                except Exception as e:
                    logger.error(f"绘制图片水印预览时出错: {e}")
    
    def calculate_watermark_position(self, width, height, scale):
        """计算水印位置"""
        position = self.watermark_settings['position']
        margin = 20 * scale
        
        if position == '左上角':
            x = margin
            y = margin
        elif position == '上中':
            x = width * scale // 2
            y = margin
        elif position == '右上角':
            x = width * scale - margin
            y = margin
        elif position == '左中':
            x = margin
            y = height * scale // 2
        elif position == '居中':
            x = width * scale // 2
            y = height * scale // 2
        elif position == '右中':
            x = width * scale - margin
            y = height * scale // 2
        elif position == '左下角':
            x = margin
            y = height * scale - margin
        elif position == '下中':
            x = width * scale // 2
            y = height * scale - margin
        else:  # 右下角
            x = width * scale - margin
            y = height * scale - margin
        
        # 添加画布偏移
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        x_offset = (canvas_width - width * scale) // 2
        y_offset = (canvas_height - height * scale) // 2
        
        return x + x_offset, y + y_offset
    
    # 事件处理方法
    def on_watermark_type_change(self):
        """水印类型改变事件"""
        if self.watermark_type.get() == "text":
            self.text_settings_frame.pack(fill=tk.X, pady=(0, 10))
            if hasattr(self, 'image_settings_frame'):
                self.image_settings_frame.pack_forget()
        else:
            if hasattr(self, 'image_settings_frame'):
                self.image_settings_frame.pack(fill=tk.X, pady=(0, 10))
            self.text_settings_frame.pack_forget()
        
        self.update_preview()
    
    def on_text_change(self, event=None):
        """文字改变事件"""
        self.watermark_settings['text'] = self.text_entry.get()
        self.update_preview()
    
    def on_font_change(self, event=None):
        """字体改变事件"""
        try:
            self.watermark_settings['font_family'] = self.font_family.get()
            self.watermark_settings['font_size'] = int(self.font_size.get())
            self.update_preview()
        except ValueError:
            pass
    
    def on_font_style_change(self):
        """字体样式改变事件"""
        self.watermark_settings['font_bold'] = self.bold_var.get()
        self.watermark_settings['font_italic'] = self.italic_var.get()
        self.update_preview()
    
    def choose_color(self):
        """选择颜色"""
        color = colorchooser.askcolor(
            initialcolor=self.rgb_to_hex(self.watermark_settings['font_color'])
        )
        if color[0]:
            self.watermark_settings['font_color'] = tuple(int(c) for c in color[0])
            self.color_preview.config(bg=color[1])
            self.update_preview()
    
    def set_position(self, position):
        """设置水印位置"""
        self.watermark_settings['position'] = position
        self.update_preview()
    
    def on_rotation_change(self, event=None):
        """旋转角度改变事件"""
        try:
            rotation = int(self.rotation_var.get())
            self.watermark_settings['rotation'] = rotation % 360
            self.update_preview()
        except ValueError:
            pass
    
    def on_opacity_change(self, value):
        """透明度改变事件"""
        self.watermark_settings['opacity'] = int(float(value))
        self.update_preview()
    
    def on_style_change(self):
        """样式改变事件"""
        self.watermark_settings['shadow_enabled'] = self.shadow_var.get()
        self.watermark_settings['stroke_enabled'] = self.stroke_var.get()
        self.update_preview()
    
    def choose_watermark_image(self):
        """选择水印图片"""
        filetypes = [
            ('图片文件', '*.png *.jpg *.jpeg *.bmp *.tiff *.tif'),
            ('PNG文件', '*.png'),
            ('所有文件', '*.*')
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=filetypes
        )
        
        if file_path:
            try:
                # 验证图片文件
                with Image.open(file_path) as img:
                    self.watermark_settings['image_watermark_path'] = file_path
                    filename = Path(file_path).name
                    self.image_path_var.set(filename)
                    self.status_var.set(f"已选择水印图片: {filename}")
                    self.update_preview()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图片文件: {e}")
    
    def clear_watermark_image(self):
        """清除水印图片"""
        self.watermark_settings['image_watermark_path'] = None
        self.image_path_var.set("未选择")
        self.status_var.set("已清除水印图片")
        self.update_preview()
    
    def on_image_scale_change(self, value):
        """图片缩放改变事件"""
        self.watermark_settings['image_watermark_scale'] = int(float(value))
        self.update_preview()
    
    def on_image_opacity_change(self, value):
        """图片透明度改变事件"""
        self.watermark_settings['image_watermark_opacity'] = int(float(value))
        self.update_preview()
    
    def on_canvas_click(self, event):
        """画布点击事件 - 手动放置水印"""
        # 计算点击位置对应的原图位置
        if self.current_image_index >= 0:
            image_path = self.images[self.current_image_index]
            original_image = Image.open(image_path)
            orig_width, orig_height = original_image.size
            
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            scale = min(canvas_width / orig_width, canvas_height / orig_height) * 0.9
            x_offset = (canvas_width - orig_width * scale) // 2
            y_offset = (canvas_height - orig_height * scale) // 2
            
            # 计算原图坐标
            orig_x = int((event.x - x_offset) / scale)
            orig_y = int((event.y - y_offset) / scale)
            
            if 0 <= orig_x <= orig_width and 0 <= orig_y <= orig_height:
                # 设置手动位置
                self.watermark_settings['position'] = 'manual'
                self.watermark_settings['manual_x'] = orig_x
                self.watermark_settings['manual_y'] = orig_y
                self.update_preview()
    
    def on_canvas_drag(self, event):
        """画布拖拽事件"""
        self.on_canvas_click(event)
    
    def on_image_select(self, event):
        """图片选择事件"""
        selection = self.image_listbox.curselection()
        if selection:
            self.current_image_index = selection[0]
            self.update_preview()
    
    # 文件操作方法
    def import_images(self):
        """导入图片"""
        filetypes = [
            ('图片文件', '*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.gif'),
            ('JPEG文件', '*.jpg *.jpeg'),
            ('PNG文件', '*.png'),
            ('所有文件', '*.*')
        ]
        
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=filetypes
        )
        
        if files:
            self.add_images(files)
    
    def import_folder(self):
        """导入文件夹"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif')
            image_files = []
            
            for file in Path(folder).rglob('*'):
                if file.suffix.lower() in supported_formats:
                    image_files.append(str(file))
            
            if image_files:
                self.add_images(image_files)
            else:
                messagebox.showwarning("警告", "所选文件夹中没有找到支持的图片文件")
    
    def add_images(self, files):
        """添加图片到列表"""
        new_count = 0
        for file in files:
            if file not in self.images:
                self.images.append(file)
                filename = Path(file).name
                self.image_listbox.insert(tk.END, filename)
                new_count += 1
        
        if new_count > 0:
            self.count_var.set(f"图片: {len(self.images)}")
            self.status_var.set(f"成功导入 {new_count} 张图片")
            
            # 自动选择第一张图片
            if len(self.images) == new_count:
                self.image_listbox.selection_set(0)
                self.on_image_select(None)
        else:
            self.status_var.set("没有新图片可导入")
    
    def clear_images(self):
        """清空图片列表"""
        if self.images:
            if messagebox.askyesno("确认", "确定要清空所有图片吗？"):
                self.images.clear()
                self.image_listbox.delete(0, tk.END)
                self.current_image_index = -1
                self.preview_canvas.delete("all")
                self.count_var.set("图片: 0")
                self.status_var.set("已清空图片列表")
    
    # 模板管理方法
    def save_template(self):
        """保存模板"""
        name = simpledialog.askstring("保存模板", "请输入模板名称:")
        if name:
            self.templates[name] = self.watermark_settings.copy()
            self.save_config()
            self.status_var.set(f"模板 '{name}' 已保存")
    
    def load_template(self):
        """加载模板"""
        if not self.templates:
            messagebox.showinfo("信息", "没有可用的模板")
            return
        
        # 创建模板选择对话框
        template_window = tk.Toplevel(self.root)
        template_window.title("选择模板")
        template_window.geometry("300x200")
        template_window.transient(self.root)
        template_window.grab_set()
        
        ttk.Label(template_window, text="选择要加载的模板:").pack(pady=10)
        
        template_listbox = tk.Listbox(template_window)
        for name in self.templates.keys():
            template_listbox.insert(tk.END, name)
        template_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        def on_template_select():
            selection = template_listbox.curselection()
            if selection:
                name = list(self.templates.keys())[selection[0]]
                self.watermark_settings = self.templates[name].copy()
                self.update_ui_from_settings()
                template_window.destroy()
                self.status_var.set(f"已加载模板 '{name}'")
        
        ttk.Button(template_window, text="加载", command=on_template_select).pack(pady=10)
    
    def update_ui_from_settings(self):
        """根据设置更新UI"""
        # 更新文字设置
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, self.watermark_settings['text'])
        
        self.font_family.set(self.watermark_settings['font_family'])
        self.font_size.set(self.watermark_settings['font_size'])
        
        self.bold_var.set(self.watermark_settings['font_bold'])
        self.italic_var.set(self.watermark_settings['font_italic'])
        
        self.color_preview.config(bg=self.rgb_to_hex(self.watermark_settings['font_color']))
        
        # 更新其他设置
        self.opacity_var.set(self.watermark_settings['opacity'])
        self.shadow_var.set(self.watermark_settings['shadow_enabled'])
        self.stroke_var.set(self.watermark_settings['stroke_enabled'])
        self.rotation_var.set(str(self.watermark_settings['rotation']))
        
        self.update_preview()
    
    # 导出方法
    def show_export_settings(self):
        """显示导出设置对话框"""
        # 创建导出设置窗口
        export_window = tk.Toplevel(self.root)
        export_window.title("导出设置")
        export_window.geometry("400x500")
        export_window.transient(self.root)
        export_window.grab_set()
        
        # 输出目录
        ttk.Label(export_window, text="输出目录:").pack(anchor=tk.W, pady=(10, 2), padx=20)
        dir_frame = ttk.Frame(export_window)
        dir_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.output_dir_var = tk.StringVar(value=self.output_settings['output_dir'])
        ttk.Entry(dir_frame, textvariable=self.output_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="浏览", command=self.choose_output_dir).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 文件命名规则
        ttk.Label(export_window, text="文件命名规则:").pack(anchor=tk.W, pady=(10, 2), padx=20)
        naming_frame = ttk.Frame(export_window)
        naming_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.naming_rule_var = tk.StringVar(value=self.output_settings['naming_rule'])
        ttk.Radiobutton(naming_frame, text="保留原文件名", 
                       variable=self.naming_rule_var, value="original").pack(anchor=tk.W)
        ttk.Radiobutton(naming_frame, text="添加前缀", 
                       variable=self.naming_rule_var, value="prefix").pack(anchor=tk.W)
        ttk.Radiobutton(naming_frame, text="添加后缀", 
                       variable=self.naming_rule_var, value="suffix").pack(anchor=tk.W)
        
        prefix_frame = ttk.Frame(export_window)
        prefix_frame.pack(fill=tk.X, padx=40, pady=(0, 10))
        ttk.Label(prefix_frame, text="前缀:").pack(side=tk.LEFT)
        self.prefix_var = tk.StringVar(value=self.output_settings['prefix'])
        ttk.Entry(prefix_frame, textvariable=self.prefix_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        suffix_frame = ttk.Frame(export_window)
        suffix_frame.pack(fill=tk.X, padx=40, pady=(0, 10))
        ttk.Label(suffix_frame, text="后缀:").pack(side=tk.LEFT)
        self.suffix_var = tk.StringVar(value=self.output_settings['suffix'])
        ttk.Entry(suffix_frame, textvariable=self.suffix_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # 输出格式
        ttk.Label(export_window, text="输出格式:").pack(anchor=tk.W, pady=(10, 2), padx=20)
        format_frame = ttk.Frame(export_window)
        format_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.format_var = tk.StringVar(value=self.output_settings['format'])
        ttk.Radiobutton(format_frame, text="JPEG", 
                       variable=self.format_var, value="JPEG").pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="PNG", 
                       variable=self.format_var, value="PNG").pack(side=tk.LEFT)
        
        # JPEG质量设置
        ttk.Label(export_window, text="JPEG质量 (0-100):").pack(anchor=tk.W, pady=(10, 2), padx=20)
        quality_frame = ttk.Frame(export_window)
        quality_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.quality_var = tk.IntVar(value=self.output_settings['quality'])
        quality_scale = ttk.Scale(quality_frame, from_=0, to=100, variable=self.quality_var, 
                                 orient=tk.HORIZONTAL)
        quality_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        quality_label = ttk.Label(quality_frame, textvariable=self.quality_var)
        quality_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 保存按钮
        def save_export_settings():
            self.output_settings['output_dir'] = self.output_dir_var.get()
            self.output_settings['naming_rule'] = self.naming_rule_var.get()
            self.output_settings['prefix'] = self.prefix_var.get()
            self.output_settings['suffix'] = self.suffix_var.get()
            self.output_settings['format'] = self.format_var.get()
            self.output_settings['quality'] = self.quality_var.get()
            export_window.destroy()
            self.status_var.set("导出设置已保存")
        
        ttk.Button(export_window, text="保存设置", command=save_export_settings).pack(pady=20)
    
    def choose_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)
    
    def batch_export(self):
        """批量导出"""
        if not self.images:
            messagebox.showwarning("警告", "请先导入图片")
            return
        
        if not self.output_settings['output_dir']:
            messagebox.showwarning("警告", "请先设置输出目录")
            return
        
        # 创建进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("批量导出")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="正在导出图片...").pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=len(self.images))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = ttk.Label(progress_window, text="准备开始")
        status_label.pack()
        
        # 更新进度
        progress_window.update()
        
        success_count = 0
        error_count = 0
        
        for i, image_path in enumerate(self.images):
            try:
                filename = Path(image_path).name
                status_label.config(text=f"处理: {filename}")
                
                # 生成输出文件名
                output_filename = self.generate_output_filename(filename)
                output_path = Path(self.output_settings['output_dir']) / output_filename
                
                # 添加水印
                if self.add_watermark_to_image(image_path, str(output_path)):
                    success_count += 1
                else:
                    error_count += 1
                
                # 更新进度
                progress_var.set(i + 1)
                progress_window.update()
                
            except Exception as e:
                logger.error(f"导出图片 {image_path} 时出错: {e}")
                error_count += 1
        
        progress_window.destroy()
        
        if error_count == 0:
            messagebox.showinfo("完成", f"成功导出 {success_count} 张图片")
            self.status_var.set(f"批量导出完成: {success_count} 成功")
        else:
            messagebox.showwarning("完成", f"导出完成: {success_count} 成功, {error_count} 失败")
            self.status_var.set(f"批量导出完成: {success_count} 成功, {error_count} 失败")
    
    def generate_output_filename(self, original_filename):
        """生成输出文件名"""
        name, ext = os.path.splitext(original_filename)
        
        if self.output_settings['format'] == 'JPEG':
            ext = '.jpg'
        elif self.output_settings['format'] == 'PNG':
            ext = '.png'
        
        if self.output_settings['naming_rule'] == 'prefix':
            return f"{self.output_settings['prefix']}{name}{ext}"
        elif self.output_settings['naming_rule'] == 'suffix':
            return f"{name}{self.output_settings['suffix']}{ext}"
        else:  # original
            return f"{name}{ext}"
    
    def add_watermark_to_image(self, input_path, output_path):
        """给图片添加水印"""
        try:
            # 打开图片
            image = Image.open(input_path).convert('RGBA')
            width, height = image.size
            
            # 创建透明层用于水印
            watermark_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
            
            if self.watermark_type.get() == "text":
                # 文字水印
                self.add_text_watermark(watermark_layer, width, height)
            else:
                # 图片水印
                self.add_image_watermark(watermark_layer, width, height)
            
            # 合并图片和水印
            watermarked = Image.alpha_composite(image, watermark_layer)
            
            # 保存图片
            if self.output_settings['format'] == 'JPEG':
                watermarked = watermarked.convert('RGB')
                watermarked.save(output_path, 'JPEG', quality=self.output_settings['quality'])
            else:
                watermarked.save(output_path, 'PNG')
            
            return True
            
        except Exception as e:
            logger.error(f"添加水印时出错: {e}")
            return False
    
    def add_text_watermark(self, layer, width, height):
        """添加文字水印"""
        draw = ImageDraw.Draw(layer)
        
        # 创建字体
        try:
            font_size = self.watermark_settings['font_size']
            font_family = self.watermark_settings['font_family']
            
            # 尝试创建字体
            font_path = None
            if sys.platform == "win32":
                font_path = f"C:/Windows/Fonts/{font_family}.ttf"
            elif sys.platform == "darwin":  # macOS
                font_path = f"/Library/Fonts/{font_family}.ttf"
            else:  # Linux
                font_path = f"/usr/share/fonts/truetype/{font_family}.ttf"
            
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 使用默认字体
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 计算文本位置
        text = self.watermark_settings['text']
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算位置
        if self.watermark_settings['position'] == 'manual':
            x = self.watermark_settings.get('manual_x', width - text_width - 20)
            y = self.watermark_settings.get('manual_y', height - text_height - 20)
        else:
            x, y = self.calculate_actual_position(width, height, text_width, text_height)
        
        # 设置透明度
        opacity = int(255 * self.watermark_settings['opacity'] / 100)
        color = self.watermark_settings['font_color'] + (opacity,)
        
        # 添加阴影效果
        if self.watermark_settings['shadow_enabled']:
            shadow_color = (0, 0, 0, opacity // 2)
            draw.text((x+2, y+2), text, font=font, fill=shadow_color)
        
        # 添加描边效果
        if self.watermark_settings['stroke_enabled']:
            stroke_color = (0, 0, 0, opacity)
            for dx in [-2, 0, 2]:
                for dy in [-2, 0, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((x+dx, y+dy), text, font=font, fill=stroke_color)
        
        # 添加主要文字
        draw.text((x, y), text, font=font, fill=color)
    
    def add_image_watermark(self, layer, width, height):
        """添加图片水印"""
        if not self.watermark_settings['image_watermark_path']:
            return
        
        try:
            # 加载水印图片
            watermark_image = Image.open(self.watermark_settings['image_watermark_path'])
            
            # 确保图片是RGBA模式以支持透明度
            if watermark_image.mode != 'RGBA':
                watermark_image = watermark_image.convert('RGBA')
            
            # 计算缩放比例
            scale = self.watermark_settings['image_watermark_scale'] / 100.0
            new_width = int(watermark_image.width * scale)
            new_height = int(watermark_image.height * scale)
            
            # 缩放水印图片
            watermark_image = watermark_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 应用透明度
            opacity = self.watermark_settings['image_watermark_opacity']
            if opacity < 100:
                # 创建新的alpha通道
                alpha = watermark_image.split()[3]
                alpha = alpha.point(lambda p: p * opacity // 100)
                watermark_image.putalpha(alpha)
            
            # 计算水印位置
            if self.watermark_settings['position'] == 'manual':
                x = self.watermark_settings.get('manual_x', width - new_width - 20)
                y = self.watermark_settings.get('manual_y', height - new_height - 20)
            else:
                x, y = self.calculate_actual_position(width, height, new_width, new_height)
            
            # 确保位置在图片范围内
            x = max(0, min(x, width - new_width))
            y = max(0, min(y, height - new_height))
            
            # 将水印图片粘贴到水印层
            layer.paste(watermark_image, (x, y), watermark_image)
            
        except Exception as e:
            logger.error(f"添加图片水印时出错: {e}")
            raise
    
    def calculate_actual_position(self, width, height, text_width, text_height):
        """计算实际水印位置"""
        margin = 20
        position = self.watermark_settings['position']
        
        if position == '左上角':
            return margin, margin
        elif position == '上中':
            return (width - text_width) // 2, margin
        elif position == '右上角':
            return width - text_width - margin, margin
        elif position == '左中':
            return margin, (height - text_height) // 2
        elif position == '居中':
            return (width - text_width) // 2, (height - text_height) // 2
        elif position == '右中':
            return width - text_width - margin, (height - text_height) // 2
        elif position == '左下角':
            return margin, height - text_height - margin
        elif position == '下中':
            return (width - text_width) // 2, height - text_height - margin
        else:  # 右下角
            return width - text_width - margin, height - text_height - margin
    
    # 配置管理方法
    def load_config(self):
        """加载配置"""
        config_path = Path.home() / ".watermark_app_config.json"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.templates = config.get('templates', {})
                    self.output_settings.update(config.get('output_settings', {}))
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        config_path = Path.home() / ".watermark_app_config.json"
        try:
            config = {
                'templates': self.templates,
                'output_settings': self.output_settings
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

def main():
    """主函数"""
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
