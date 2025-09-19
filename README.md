# 图片水印添加工具

一个基于Python的命令行工具，用于从图片EXIF信息中提取拍摄时间并添加为水印。

## 功能特性

- 📸 自动读取图片EXIF信息中的拍摄时间
- 🎨 支持自定义字体大小、颜色和水印位置
- 📁 批量处理目录中的所有图片
- 💾 自动创建输出目录保存处理后的图片
- 🐛 完善的错误处理和日志记录

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法
```bash
python watermark.py /path/to/images
```

### 高级选项
```bash
# 自定义字体大小
python watermark.py /path/to/images --font-size 48

# 自定义水印颜色（RGB格式）
python watermark.py /path/to/images --color "255,0,0"

# 自定义水印颜色（HEX格式）
python watermark.py /path/to/images --color "#FF0000"

# 自定义水印位置
python watermark.py /path/to/images --position 左上角
```

### 位置选项
- `左上角` - 左上角
- `右上角` - 右上角  
- `左下角` - 左下角
- `右下角` - 右下角（默认）
- `居中` - 图片中心

## 输出说明

程序会在原目录下创建名为 `原目录名_watermark` 的子目录，所有处理后的图片将保存在该目录中。

## 支持格式

- JPEG/JPG
- PNG
- TIFF
- BMP
- GIF

## 注意事项

- 如果图片没有EXIF信息，将使用当前日期作为水印
- 建议使用有EXIF信息的图片以获得准确的拍摄时间
- 确保有足够的磁盘空间存放处理后的图片

## 许可证

MIT License
