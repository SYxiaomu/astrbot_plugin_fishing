# ★ 星级图片渲染方案使用说明

## 问题背景
- DouyinSansBold 字体不包含 ★ (U+2605) 字形
- 需要一种可靠的方式来渲染星级图标

## 解决方案
使用图片渲染 ★，保证 100% 显示成功率。

## 文件清单
1. `draw/resource/star.png` - 金色星星图片（32x32 RGBA）
2. `draw/star_renderer.py` - 星级渲染器模块
3. `test_integration.py` - 集成测试示例

## 使用方法

### 1. 导入模块
```python
from draw.star_renderer import draw_text_with_stars
```

### 2. 替换原有的 draw.text() 调用

**原来的代码：**
```python
draw.text((x, y), '稀有度：★★★★★', font=font, fill=(255, 165, 0))
```

**修改后的代码：**
```python
draw_text_with_stars(img, draw, (x, y), '稀有度：★★★★★', 
                     font, fill=(255, 165, 0), star_size=32)
```

### 3. 参数说明
- `img`: Image 对象（必需，用于 paste 操作）
- `draw`: ImageDraw 对象（必需）
- `xy`: 起始坐标 (x, y)
- `text`: 文本内容（包含 ★ 字符）
- `font`: 字体对象
- `fill`: 文字颜色（RGB 元组）
- `star_size`: 星星图片大小（默认 32）

## 特性
- ✅ ★  guaranteed 显示（不依赖字体）
- ✅ 自动处理文本和星星的混合渲染
- ✅ 支持垂直居中对齐
- ✅ 支持 RGBA 透明通道
- ✅ 与现有 emoji 渲染机制兼容
- ✅ 星星图片缓存，性能优化

## 测试验证
运行 `python test_integration.py` 查看效果
输出文件：`m:/integration_test.png`

## 注意事项
1. 必须同时传递 `img` 和 `draw` 参数
2. 星星大小建议与字体大小匹配（32号字体用32px星星）
3. 如果 star.png 不存在，会回退到普通文本渲染