# 字体资源说明

## 推荐免费商用中文字体

以下字体均可免费商用，推荐下载使用：

### 1. 思源黑体 (Source Han Sans / Noto Sans CJK)
- **特点**：现代、清晰、易读
- **下载**：https://github.com/adobe-fonts/source-han-sans
- **适用**：正文、标题

### 2. 思源宋体 (Source Han Serif / Noto Serif CJK)
- **特点**：优雅、传统、文化感
- **下载**：https://github.com/adobe-fonts/source-han-serif
- **适用**：标题、诗词

### 3. 阿里巴巴普惠体
- **特点**：温暖、现代、开放
- **下载**：https://www.alibabafonts.com/
- **适用**：商务、电商

### 4. 站酷系列
- **站酷庆科黄油体**：可爱、圆润
- **站酷快乐体**：活泼、趣味
- **站酷高端黑**：现代、时尚
- **下载**：https://www.zcool.com.cn/fonts
- **适用**：创意、年轻

### 5. 霭毫冰川字体
- **特点**：清秀、现代
- **下载**：https://github.com/TakWolf/fira-miso
- **适用**：文艺、清新

### 6. 楷体、宋体、黑体
- **特点**：传统、正式
- **系统自带**：通常系统已安装
- **适用**：正式场合

## 安装方法

### macOS
1. 下载字体文件（.ttf 或 .otf）
2. 双击字体文件
3. 点击"安装字体"按钮
4. 重启应用程序

### Linux
```bash
# 复制字体到系统字体目录
sudo cp *.ttf /usr/share/fonts/truetype/

# 或复制到用户字体目录
mkdir -p ~/.local/share/fonts
cp *.ttf ~/.local/share/fonts/

# 刷新字体缓存
fc-cache -fv
```

### Windows
1. 下载字体文件
2. 右键字体文件 → "为所有用户安装"
3. 重启应用程序

## 当前配置使用

### 已配置字体方案
- **default**：思源宋体标题 + 思源黑体正文
- **modern**：思源黑体标题 + 思源黑体正文
- **elegant**：思源宋体标题 + 思源宋体正文

### 系统回退字体
如果思源字体未安装，系统会自动使用：
- `PingFang SC`（苹方）- macOS 默认中文字体
- `STHeiti`（华文黑体）- macOS 中文字体
- `NotoSansSC` - Google Noto Sans

## CSS 字体栈

```css
/* 优雅衬线字体栈 */
font-family: "Source Han Serif SC", "Noto Serif CJK SC", "STSong", "SimSun", serif;

/* 现代无衬线字体栈 */
font-family: "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif;

/* 圆润可爱字体栈 */
font-family: "ZCOOL KuaiLe", "YouYuan", "Rounded Mplus 1c", sans-serif;

### 传统书法字体栈 */
font-family: "KaiTi", "STKaiti", "AR PL UKai CN", "楷体", serif;
```

## 添加新字体

1. 下载并安装字体到系统
2. 更新 `config/platforms/xiaohongshu.yaml` 中的字体方案
3. 添加新的 `font_schemes` 配置
4. 重启后端服务

示例配置：
```yaml
font_schemes:
  - name: "playful"
    title_font: "ZCOOL KuaiLe, cursive"
    body_font: "ZCOOL KuaiLe, cursive"
```
