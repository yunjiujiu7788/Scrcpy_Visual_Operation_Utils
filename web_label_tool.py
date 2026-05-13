from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import cv2
import shutil
from pathlib import Path
import json

app = Flask(__name__)

# 配置
RAW_DIR = Path('raw_screenshots')
OUTPUT_IMG_DIR = Path('datasets/xiaohongshu/images/train')
OUTPUT_LABEL_DIR = Path('datasets/xiaohongshu/labels/train')
CURRENT_SESSIONS = {}  # 存储当前标注会话

# 创建目录
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_LABEL_DIR.mkdir(parents=True, exist_ok=True)

def get_image_list():
    """获取待标注图片列表"""
    exts = ['.jpg', '.jpeg', '.png', '.bmp']
    return [f.name for f in RAW_DIR.iterdir() if f.suffix.lower() in exts]

def convert_to_yolo(img_path, boxes):
    """将像素坐标转换为YOLO格式"""
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    img_height, img_width = img.shape[:2]
    
    yolo_lines = []
    for box in boxes:
        x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
        center_x = (x1 + x2) / 2 / img_width
        center_y = (y1 + y2) / 2 / img_height
        width = abs(x2 - x1) / img_width
        height = abs(y2 - y1) / img_height
        
        # 确保在有效范围内
        center_x = max(0.001, min(0.999, center_x))
        center_y = max(0.001, min(0.999, center_y))
        width = max(0.001, min(0.999, width))
        height = max(0.001, min(0.999, height))
        
        yolo_lines.append(f'0 {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}')
    return yolo_lines

@app.route('/')
def index():
    images = get_image_list()
    return render_template('label.html', images=images)

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(str(RAW_DIR), filename)

@app.route('/api/get_images')
def api_get_images():
    images = get_image_list()
    return jsonify({'images': images})

@app.route('/api/save_annotation', methods=['POST'])
def api_save_annotation():
    data = request.json
    filename = data['filename']
    boxes = data['boxes']
    
    # 复制图片到训练集
    src_path = RAW_DIR / filename
    if not src_path.exists():
        return jsonify({'success': False, 'message': '图片不存在'})
    
    # 生成新文件名
    ext = filename.split('.')[-1]
    count = len(list(OUTPUT_IMG_DIR.glob('*.jpg'))) + 1
    new_name = f'{count:04d}.{ext}'
    dst_img_path = OUTPUT_IMG_DIR / new_name
    shutil.copy(str(src_path), str(dst_img_path))
    
    # 保存标签文件
    yolo_lines = convert_to_yolo(src_path, boxes)
    if yolo_lines is None:
        return jsonify({'success': False, 'message': '图片读取失败'})
    
    label_path = OUTPUT_LABEL_DIR / f'{new_name.replace(f".{ext}", ".txt")}'
    with open(label_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(yolo_lines))
    
    return jsonify({
        'success': True,
        'message': f'已保存 {len(boxes)} 个标注框',
        'saved_name': new_name
    })

@app.route('/api/skip_image', methods=['POST'])
def api_skip_image():
    data = request.json
    filename = data['filename']
    return jsonify({'success': True, 'message': f'已跳过 {filename}'})

if __name__ == '__main__':
    # 创建模板目录和HTML文件
    template_dir = Path('templates')
    template_dir.mkdir(exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书笔记卡片标注工具</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: white; overflow: hidden; }
        .header { background: #16213e; padding: 12px 20px; text-align: center; height: 50px; display: flex; align-items: center; justify-content: center; }
        .header h1 { font-size: 18px; margin: 0; }
        .main { display: flex; height: calc(100vh - 50px); }
        .sidebar { width: 260px; background: #16213e; padding: 15px; display: flex; flex-direction: column; border-right: 1px solid #2a3f5f; }
        .sidebar h3 { margin-bottom: 12px; color: #00d9ff; font-size: 14px; }
        .image-list { list-style: none; flex: 1; overflow-y: auto; }
        .image-item { padding: 8px; margin-bottom: 6px; background: #0f3460; border-radius: 6px; cursor: pointer; transition: all 0.2s; font-size: 13px; }
        .image-item:hover { background: #1a5276; }
        .image-item.active { background: #00d9ff; color: #1a1a2e; }
        .sidebar-actions { margin-top: 15px; padding-top: 15px; border-top: 1px solid #2a3f5f; }
        .sidebar-btn { width: 100%; padding: 10px; margin-bottom: 8px; border: none; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-save { background: #00d9ff; color: #1a1a2e; }
        .btn-save:hover { background: #00b8e6; }
        .btn-skip { background: #e74c3c; color: white; }
        .btn-skip:hover { background: #c0392b; }
        .btn-undo { background: #9b59b6; color: white; }
        .btn-undo:hover { background: #8e44ad; }
        .btn-clear { background: #f39c12; color: white; }
        .btn-clear:hover { background: #e67e22; }
        .btn-reset-point { background: #3498db; color: white; }
        .btn-reset-point:hover { background: #2980b9; }
        .workspace { flex: 1; position: relative; background: #0a0a0f; overflow: hidden; }
        .viewport { position: absolute; width: 100%; height: 100%; overflow: hidden; cursor: crosshair; }
        .image-container { position: absolute; transform-origin: 0 0; }
        #imageCanvas { display: block; pointer-events: none; }
        .annotation-box { position: absolute; border: 2px solid #00ff88; background: rgba(0, 255, 136, 0.1); pointer-events: auto; }
        .annotation-box:hover { border-color: #ff6b6b; }
        .annotation-box .delete-btn { position: absolute; top: -12px; right: -12px; width: 24px; height: 24px; background: #ff6b6b; border: none; border-radius: 50%; color: white; cursor: pointer; font-weight: bold; font-size: 14px; z-index: 10; }
        .temp-point { position: absolute; width: 10px; height: 10px; background: #ff6b6b; border-radius: 50%; border: 2px solid white; transform: translate(-50%, -50%); z-index: 5; pointer-events: none; }
        .controls { position: fixed; top: 60px; left: 280px; background: rgba(22, 33, 62, 0.95); padding: 12px; border-radius: 10px; z-index: 100; display: flex; flex-direction: column; align-items: center; }
        .zoom-controls { display: flex; flex-direction: column; align-items: center; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #2a3f5f; }
        .zoom-btn { width: 36px; height: 36px; border: none; border-radius: 6px; background: #2a3f5f; color: white; font-size: 18px; cursor: pointer; margin: 2px; transition: all 0.2s; }
        .zoom-btn:hover { background: #3a5f7f; }
        .zoom-value { display: block; text-align: center; font-size: 12px; color: #aaa; margin-top: 5px; }
        .pan-controls { display: flex; flex-direction: column; align-items: center; }
        .pan-area { width: 60px; height: 60px; background: #2a3f5f; border-radius: 50%; position: relative; cursor: grab; border: 2px solid #3a5f7f; }
        .pan-area.dragging { cursor: grabbing; }
        .pan-ball { width: 24px; height: 24px; background: #00d9ff; border-radius: 50%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); cursor: move; box-shadow: 0 2px 8px rgba(0, 217, 255, 0.4); }
        .pan-ball:hover { background: #00b8e6; }
        .pan-ball.dragging { background: #00ff88; transform: translate(-50%, -50%) scale(1.2); }
        .pan-hint { font-size: 10px; color: #666; margin-top: 5px; text-align: center; }
        .status-bar { position: fixed; top: 60px; right: 20px; background: rgba(22, 33, 62, 0.95); padding: 10px 15px; border-radius: 8px; font-size: 13px; z-index: 100; }
        .status-bar span { color: #00ff88; }
        .drawing-hint { position: fixed; top: 60px; right: 120px; background: rgba(22, 33, 62, 0.95); padding: 10px 15px; border-radius: 8px; font-size: 14px; color: #00d9ff; z-index: 100; }
        .shortcuts { position: fixed; bottom: 15px; right: 20px; background: rgba(22, 33, 62, 0.9); padding: 10px 15px; border-radius: 8px; font-size: 12px; color: #ccc; z-index: 100; }
        .shortcuts h4 { color: #00d9ff; margin-bottom: 5px; font-size: 13px; }
        .shortcuts div { margin: 3px 0; }
        .shortcuts kbd { background: #2a3f5f; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 11px; }
        .image-info { position: fixed; bottom: 15px; left: 280px; background: rgba(22, 33, 62, 0.9); padding: 10px 15px; border-radius: 8px; font-size: 12px; color: #aaa; z-index: 100; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 小红书笔记卡片标注工具</h1>
    </div>
    
    <div class="main">
        <div class="sidebar">
            <h3>📁 待标注图片</h3>
            <ul class="image-list" id="imageList"></ul>
            
            <div class="sidebar-actions">
                <button class="sidebar-btn btn-undo" onclick="undoLast()">↩ 撤销</button>
                <button class="sidebar-btn btn-reset-point" onclick="resetFirstPoint()">◀ 重置点</button>
                <button class="sidebar-btn btn-clear" onclick="clearBoxes()">🗑 清空</button>
                <button class="sidebar-btn btn-skip" onclick="skipImage()">➡ 跳过</button>
                <button class="sidebar-btn btn-save" onclick="saveAnnotation()">💾 保存</button>
            </div>
        </div>
        
        <div class="workspace">
            <div class="viewport" id="viewport">
                <div class="image-container" id="imageContainer">
                    <img id="imageCanvas" src="" alt="点击左侧图片开始标注" draggable="false" />
                </div>
            </div>
        </div>
    </div>
    
    <div class="controls">
        <div class="zoom-controls">
            <button class="zoom-btn" onclick="zoomIn()">+</button>
            <button class="zoom-btn" onclick="zoomOut()">−</button>
            <button class="zoom-btn" onclick="zoomReset()">⟲</button>
            <div class="zoom-value" id="zoomValue">100%</div>
        </div>
        <div class="pan-controls">
            <div class="pan-area" id="panArea">
                <div class="pan-ball" id="panBall"></div>
            </div>
            <div class="pan-hint">拖动圆球移动图片</div>
        </div>
    </div>
    
    <div class="status-bar">
        当前框数: <span id="boxCount">0</span>
    </div>
    
    <div class="drawing-hint" id="drawingHint" style="display: none;">📌 请点击第二点完成矩形框</div>
    
    <div class="shortcuts">
        <h4>快捷键:</h4>
        <div><kbd>+</kbd> / <kbd>滚轮上</kbd> 放大</div>
        <div><kbd>-</kbd> / <kbd>滚轮下</kbd> 缩小</div>
        <div><kbd>0</kbd> 重置缩放</div>
        <div><kbd>Z</kbd> 撤销</div>
        <div><kbd>R</kbd> 重置点</div>
        <div><kbd>C</kbd> 清空</div>
    </div>
    
    <div class="image-info" id="imageInfo" style="display: none;">
        图片尺寸: <span id="imageSize">-</span>
    </div>

    <script>
        let currentImage = null;
        let boxes = [];
        let firstPoint = null;
        let zoom = 1;
        let panX = 0;
        let panY = 0;
        
        let viewport = document.getElementById('viewport');
        let imageContainer = document.getElementById('imageContainer');
        let imageCanvas = document.getElementById('imageCanvas');
        let boxCount = document.getElementById('boxCount');
        let zoomValue = document.getElementById('zoomValue');
        let drawingHint = document.getElementById('drawingHint');
        let imageInfo = document.getElementById('imageInfo');
        let imageSize = document.getElementById('imageSize');
        
        // 拖动圆球相关
        let panArea = document.getElementById('panArea');
        let panBall = document.getElementById('panBall');
        let isPanning = false;
        let panStartX = 0;
        let panStartY = 0;
        let ballStartX = 0;
        let ballStartY = 0;
        
        // 加载图片列表
        async function loadImages() {
            const response = await fetch('/api/get_images');
            const data = await response.json();
            const list = document.getElementById('imageList');
            list.innerHTML = '';
            
            data.images.forEach(img => {
                const li = document.createElement('li');
                li.className = 'image-item';
                li.textContent = img;
                li.onclick = () => selectImage(img);
                list.appendChild(li);
            });
        }
        
        // 选择图片
        function selectImage(filename) {
            currentImage = filename;
            imageCanvas.src = `/images/${filename}`;
            imageCanvas.onload = () => {
                boxes = [];
                firstPoint = null;
                zoom = 1;
                panX = 0;
                panY = 0;
                resetPanBall();
                updateZoomDisplay();
                updateTransform();
                removeTempPoint();
                
                imageInfo.style.display = 'block';
                imageSize.textContent = `${imageCanvas.naturalWidth} x ${imageCanvas.naturalHeight}`;
                
                document.querySelectorAll('.image-item').forEach(item => {
                    item.classList.remove('active');
                });
                event.target.classList.add('active');
                
                updateBoxCount();
                clearCanvasBoxes();
                hideDrawingHint();
            };
        }
        
        // 获取点击位置的原始坐标
        function getOriginalPosition(clientX, clientY) {
            const rect = viewport.getBoundingClientRect();
            const x = (clientX - rect.left - panX) / zoom;
            const y = (clientY - rect.top - panY) / zoom;
            return { x, y };
        }
        
        // 点击画布处理（只处理标注）
        viewport.addEventListener('click', (e) => {
            if (!currentImage) return;
            if (e.target.classList.contains('delete-btn')) return;
            if (e.target.classList.contains('annotation-box')) return;
            
            const pos = getOriginalPosition(e.clientX, e.clientY);
            
            if (!firstPoint) {
                firstPoint = pos;
                showTempPoint(pos);
                showDrawingHint();
            } else {
                const secondPoint = pos;
                const box = {
                    id: Date.now(),
                    x1: Math.min(firstPoint.x, secondPoint.x),
                    y1: Math.min(firstPoint.y, secondPoint.y),
                    x2: Math.max(firstPoint.x, secondPoint.x),
                    y2: Math.max(firstPoint.y, secondPoint.y)
                };
                
                // 限制在图片范围内
                box.x1 = Math.max(0, box.x1);
                box.y1 = Math.max(0, box.y1);
                box.x2 = Math.min(imageCanvas.naturalWidth, box.x2);
                box.y2 = Math.min(imageCanvas.naturalHeight, box.y2);
                
                const minSize = 5;
                if (Math.abs(box.x2 - box.x1) > minSize && Math.abs(box.y2 - box.y1) > minSize) {
                    boxes.push(box);
                    drawBox(box);
                    updateBoxCount();
                }
                
                firstPoint = null;
                removeTempPoint();
                hideDrawingHint();
            }
        });
        
        // 显示临时点
        function showTempPoint(pos) {
            const pointEl = document.createElement('div');
            pointEl.className = 'temp-point';
            pointEl.id = 'tempPoint';
            pointEl.style.left = `${pos.x}px`;
            pointEl.style.top = `${pos.y}px`;
            imageContainer.appendChild(pointEl);
        }
        
        // 移除临时点
        function removeTempPoint() {
            const pointEl = document.getElementById('tempPoint');
            if (pointEl) pointEl.remove();
        }
        
        // 显示提示
        function showDrawingHint() {
            drawingHint.style.display = 'block';
        }
        
        // 隐藏提示
        function hideDrawingHint() {
            drawingHint.style.display = 'none';
        }
        
        // 重置第一个点
        function resetFirstPoint() {
            firstPoint = null;
            removeTempPoint();
            hideDrawingHint();
        }
        
        // 绘制标注框
        function drawBox(box) {
            const boxEl = document.createElement('div');
            boxEl.className = 'annotation-box';
            boxEl.dataset.id = box.id;
            boxEl.style.left = `${box.x1}px`;
            boxEl.style.top = `${box.y1}px`;
            boxEl.style.width = `${box.x2 - box.x1}px`;
            boxEl.style.height = `${box.y2 - box.y1}px`;
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.innerHTML = '×';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                deleteBox(box.id);
            };
            boxEl.appendChild(deleteBtn);
            
            imageContainer.appendChild(boxEl);
        }
        
        // 删除单个框
        function deleteBox(id) {
            boxes = boxes.filter(b => b.id !== id);
            document.querySelector(`.annotation-box[data-id="${id}"]`)?.remove();
            updateBoxCount();
        }
        
        // 清空所有框
        function clearBoxes() {
            boxes = [];
            clearCanvasBoxes();
            resetFirstPoint();
            updateBoxCount();
        }
        
        // 清除画布上的框
        function clearCanvasBoxes() {
            document.querySelectorAll('.annotation-box').forEach(el => el.remove());
        }
        
        // 撤销最后一个框
        function undoLast() {
            if (boxes.length === 0) return;
            const lastBox = boxes.pop();
            document.querySelector(`.annotation-box[data-id="${lastBox.id}"]`)?.remove();
            updateBoxCount();
        }
        
        // 更新框数显示
        function updateBoxCount() {
            boxCount.textContent = boxes.length;
        }
        
        // 缩放控制
        function zoomIn() {
            zoom = Math.min(zoom * 1.2, 4);
            updateZoomDisplay();
            updateTransform();
        }
        
        function zoomOut() {
            zoom = Math.max(zoom / 1.2, 0.25);
            updateZoomDisplay();
            updateTransform();
        }
        
        function zoomReset() {
            zoom = 1;
            panX = 0;
            panY = 0;
            resetPanBall();
            updateZoomDisplay();
            updateTransform();
        }
        
        function updateZoomDisplay() {
            zoomValue.textContent = `${Math.round(zoom * 100)}%`;
        }
        
        function updateTransform() {
            imageContainer.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
        }
        
        // 鼠标滚轮缩放
        viewport.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (!currentImage) return;
            
            if (e.deltaY < 0) {
                zoomIn();
            } else {
                zoomOut();
            }
        });
        
        // 拖动圆球控制图片移动
        panBall.addEventListener('mousedown', (e) => {
            e.preventDefault();
            if (!currentImage) return;
            
            isPanning = true;
            panArea.classList.add('dragging');
            panBall.classList.add('dragging');
            
            const rect = panArea.getBoundingClientRect();
            panStartX = e.clientX;
            panStartY = e.clientY;
            ballStartX = panBall.offsetLeft;
            ballStartY = panBall.offsetTop;
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isPanning || !currentImage) return;
            
            const rect = panArea.getBoundingClientRect();
            const maxOffset = (rect.width - panBall.offsetWidth) / 2;
            
            // 计算圆球偏移
            let offsetX = e.clientX - panStartX + ballStartX - rect.width / 2 + panBall.offsetWidth / 2;
            let offsetY = e.clientY - panStartY + ballStartY - rect.height / 2 + panBall.offsetHeight / 2;
            
            // 限制圆球在圆形区域内
            const centerX = rect.width / 2 - panBall.offsetWidth / 2;
            const centerY = rect.height / 2 - panBall.offsetHeight / 2;
            const distance = Math.sqrt(Math.pow(offsetX, 2) + Math.pow(offsetY, 2));
            
            if (distance > maxOffset) {
                const ratio = maxOffset / distance;
                offsetX *= ratio;
                offsetY *= ratio;
            }
            
            // 更新圆球位置
            panBall.style.left = `${centerX + offsetX}px`;
            panBall.style.top = `${centerY + offsetY}px`;
            
            // 计算图片移动量（圆球偏移的反向映射到图片移动）
            const panSpeed = 5; // 移动速度系数
            panX += offsetX * panSpeed;
            panY += offsetY * panSpeed;
            
            updateTransform();
            
            // 重置起始点用于下一帧计算
            panStartX = e.clientX;
            panStartY = e.clientY;
            ballStartX = centerX + offsetX;
            ballStartY = centerY + offsetY;
        });
        
        document.addEventListener('mouseup', () => {
            if (isPanning) {
                isPanning = false;
                panArea.classList.remove('dragging');
                panBall.classList.remove('dragging');
            }
        });
        
        // 重置圆球位置到中心
        function resetPanBall() {
            const rect = panArea.getBoundingClientRect();
            const centerX = rect.width / 2 - panBall.offsetWidth / 2;
            const centerY = rect.height / 2 - panBall.offsetHeight / 2;
            panBall.style.left = `${centerX}px`;
            panBall.style.top = `${centerY}px`;
        }
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch(e.key.toLowerCase()) {
                case '+':
                case '=':
                    zoomIn();
                    break;
                case '-':
                case '_':
                    zoomOut();
                    break;
                case '0':
                    zoomReset();
                    break;
                case 'z':
                    undoLast();
                    break;
                case 'r':
                    resetFirstPoint();
                    break;
                case 'c':
                    clearBoxes();
                    break;
            }
        });
        
        // 保存标注
        async function saveAnnotation() {
            if (!currentImage) {
                alert('请先选择一张图片');
                return;
            }
            if (boxes.length === 0) {
                alert('请先标注至少一个笔记卡片');
                return;
            }
            
            const response = await fetch('/api/save_annotation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: currentImage, boxes: boxes })
            });
            
            const data = await response.json();
            if (data.success) {
                alert(data.message);
                clearBoxes();
                document.querySelector('.image-item.active')?.remove();
                currentImage = null;
                imageCanvas.src = '';
                imageInfo.style.display = 'none';
                zoom = 1;
                panX = 0;
                panY = 0;
                resetPanBall();
                updateZoomDisplay();
                updateTransform();
            } else {
                alert('保存失败: ' + data.message);
            }
        }
        
        // 跳过图片
        async function skipImage() {
            if (!currentImage) {
                alert('请先选择一张图片');
                return;
            }
            
            const response = await fetch('/api/skip_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: currentImage })
            });
            
            const data = await response.json();
            if (data.success) {
                clearBoxes();
                document.querySelector('.image-item.active')?.remove();
                currentImage = null;
                imageCanvas.src = '';
                imageInfo.style.display = 'none';
                zoom = 1;
                panX = 0;
                panY = 0;
                resetPanBall();
                updateZoomDisplay();
                updateTransform();
            }
        }
        
        // 初始化
        loadImages();
        resetPanBall();
    </script>
</body>
</html>'''
    
    with open(template_dir / 'label.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print('🚀 Web标注工具已启动!')
    print('📡 访问地址: http://localhost:5000')
    print('📁 将待标注图片放入 raw_screenshots 目录')
    app.run(host='0.0.0.0', port=5000, debug=True)