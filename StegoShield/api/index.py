# Vercel Python Handler - 完整前端版
import json
import os

def handler(environ, start_response):
    """WSGI 兼容处理器"""
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # 根路径 - 返回完整前端页面
    if path == '/' or path == '':
        status = '200 OK'
        
        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StegoShield - 图片隐写</title>
  <style>
    :root { --primary: #6366f1; --primary-light: #818cf8; --success: #22c55e; --warning: #f59e0b; --error: #ef4444; --bg: #0f172a; --bg-card: #1e293b; --text: #f8fafc; --text-muted: #94a3b8; --border: #334155; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .app-container { width: 100%; max-width: 480px; }
    .header { text-align: center; margin-bottom: 32px; }
    .header h1 { font-size: 28px; font-weight: 700; background: linear-gradient(135deg, var(--primary), var(--primary-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .header p { color: var(--text-muted); font-size: 14px; margin-top: 8px; }
    .card { background: var(--bg-card); border-radius: 16px; padding: 24px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3); }
    .tabs { display: flex; gap: 8px; margin-bottom: 24px; }
    .tab-btn { flex: 1; padding: 12px; border: none; border-radius: 8px; background: var(--bg); color: var(--text-muted); font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; }
    .tab-btn.active { background: var(--primary); color: white; }
    .embed-section { display: block !important; }
    .embed-section.hidden { display: none !important; }
    .extract-section { display: none; }
    .extract-section:not(.hidden) { display: block; }
    .upload-area { border: 2px dashed var(--border); border-radius: 12px; padding: 40px 20px; text-align: center; cursor: pointer; transition: all 0.3s ease; }
    .upload-area:hover { border-color: var(--primary); background: rgba(99, 102, 241, 0.1); }
    .upload-area.has-image { padding: 20px; }
    .upload-icon { width: 48px; height: 48px; margin: 0 auto 16px; color: var(--primary); }
    .upload-text { font-size: 16px; margin-bottom: 8px; }
    .upload-hint { font-size: 12px; color: var(--text-muted); }
    .btn { width: 100%; padding: 14px 24px; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; border: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-light); }
    .btn-primary:disabled { background: var(--border); cursor: not-allowed; }
    .hidden { display: none !important; }
    select { margin-left: 8px; padding: 8px 12px; background: var(--bg-card); color: var(--text); border: 1px solid var(--border); border-radius: 6px; font-size: 14px; }
    .step-container { animation: slideIn 0.4s ease; }
    @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .preview-container { display: none; text-align: center; }
    .preview-container.show { display: block; }
    .preview-img { max-width: 100%; max-height: 200px; border-radius: 8px; margin-bottom: 12px; }
    .input-type-selector { display: flex; gap: 12px; margin-bottom: 20px; }
    .type-btn { flex: 1; padding: 12px; border: 2px solid var(--border); border-radius: 8px; background: transparent; color: var(--text-muted); font-size: 14px; cursor: pointer; }
    .type-btn.active { border-color: var(--primary); background: rgba(99, 102, 241, 0.2); color: var(--text); }
    .text-area { width: 100%; padding: 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 14px; resize: none; min-height: 120px; }
    .text-area:focus { outline: none; border-color: var(--primary); }
    .toggle { position: relative; display: inline-block; width: 48px; height: 24px; }
    .toggle input { opacity: 0; width: 0; height: 0; }
    .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--border); transition: 0.3s; border-radius: 24px; }
    .toggle-slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: 0.3s; border-radius: 50%; }
    .toggle input:checked + .toggle-slider { background-color: var(--primary); }
    .toggle input:checked + .toggle-slider:before { transform: translateX(24px); }
    .result-preview { margin: 20px auto; max-width: 180px; border-radius: 12px; overflow: hidden; border: 2px solid var(--primary); }
    .result-preview img { width: 100%; display: block; min-height: 120px; object-fit: contain; }
    .key-section { background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 8px; padding: 16px; margin-bottom: 20px; }
    .key-label { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
    .key-value-row { display: flex; align-items: center; gap: 8px; }
    .key-value { flex: 1; font-family: monospace; font-size: 12px; color: var(--primary-light); background: var(--bg); padding: 8px 12px; border-radius: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .btn-copy { padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; }
    .result-actions { display: flex; gap: 12px; }
    .btn-download { flex: 1; background: var(--success); color: white; }
    .btn-reset { flex: 1; background: var(--bg); color: var(--text); border: 1px solid var(--border); }
    .process-step { font-size: 13px; color: var(--text-muted); display: flex; align-items: center; gap: 8px; justify-content: center; margin: 8px 0; }
    .process-step .dot { width: 6px; height: 6px; background: var(--primary); border-radius: 50%; animation: pulse 1s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 0.4; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1); } }
    .error-detail { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px; margin-top: 12px; }
    .error-code { font-family: monospace; font-size: 12px; color: #ef4444; margin-bottom: 4px; }
    .error-message { font-size: 14px; color: var(--text); }
    .extract-result { margin-top: 20px; padding: 16px; background: var(--bg); border-radius: 8px; border: 1px solid var(--border); }
    .extract-result-label { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
    .extract-result-content { font-size: 14px; word-break: break-all; max-height: 150px; overflow-y: auto; }
  </style>
</head>
<body>
  <div class="app-container">
    <header class="header">
      <h1>StegoShield</h1>
      <p>图片隐写工具</p>
    </header>
    <div class="tabs">
      <button class="tab-btn active" id="tab-embed" onclick="switchTab('embed')">嵌入数据</button>
      <button class="tab-btn" id="tab-extract" onclick="switchTab('extract')">提取数据</button>
    </div>
    <div class="card">
      <div class="embed-section" id="embed-section">
        <div class="step-container" id="embed-step-1">
          <div class="upload-area" id="upload-area" onclick="document.getElementById('file-input').click()">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/><path d="M21 15l-5-5L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            <p class="upload-text">点击选择图片</p>
            <p class="upload-hint">支持 PNG、JPG、BMP</p>
          </div>
          <div style="margin-top: 16px; text-align: center;">
            <span style="color: var(--text-muted); font-size: 14px;">隐写方法：</span>
            <select id="method-select"><option value="lsb">LSB (PNG 推荐)</option><option value="dct">DCT (JPEG 支持)</option></select>
          </div>
          <input type="file" id="file-input" accept="image/*" style="display: none;" onchange="handleFileSelect(event)">
          <div class="preview-container" id="preview-container"><img id="preview-img" class="preview-img" alt="预览"><p class="preview-info" id="preview-info"></p></div>
          <button class="btn btn-primary" id="next-1-btn" style="margin-top: 20px;" disabled onclick="goToStep(2)">下一步</button>
        </div>
        <div class="step-container hidden" id="embed-step-2">
          <div class="input-type-selector"><button class="type-btn active" data-type="text" onclick="selectInputType('text')">文字</button><button class="type-btn" data-type="file" onclick="selectInputType('file')">文件</button></div>
          <div id="text-input-section"><textarea class="text-area" id="secret-text" placeholder="输入要隐藏的内容..."></textarea></div>
          <div id="file-input-section" class="hidden"><div class="upload-area" id="file-upload-area" onclick="document.getElementById('secret-file-input').click()"><svg class="upload-icon" viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/></svg><p class="upload-text">点击选择文件</p><p class="upload-hint" id="file-name-hint"></p></div><input type="file" id="secret-file-input" style="display: none;" onchange="handleSecretFile(event)"></div>
          <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin: 20px 0;"><span style="color: var(--text-muted);">启用加密</span><label class="toggle"><input type="checkbox" id="encrypt-toggle" onchange="toggleEncrypt(this)"><span class="toggle-slider"></span></label></div>
          <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 20px;"><span style="color: var(--text-muted);">抗压缩</span><label class="toggle"><input type="checkbox" id="compress-toggle" onchange="toggleCompress(this)"><span class="toggle-slider"></span></label></div>
          <button class="btn btn-primary" id="execute-btn" onclick="executeEmbed()">开始嵌入</button>
          <button class="btn" style="margin-top: 12px; background: transparent; color: var(--text-muted); border: 1px solid var(--border);" onclick="goToStep(1)">返回上一步</button>
        </div>
        <div class="step-container hidden" id="embed-step-3">
          <div class="processing-section" style="text-align: center; padding: 20px 0;">
            <div class="processing-icon"><div class="processing-circle"></div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg></div>
            <p class="processing-title">正在处理...</p>
            <div class="processing-steps"><span class="process-step"><span class="dot"></span>准备数据</span><span class="process-step"><span class="dot"></span>嵌入隐写数据</span><span class="process-step"><span class="dot"></span>生成图片</span></div>
          </div>
        </div>
        <div class="step-container hidden" id="embed-step-4">
          <div class="result-section" style="text-align: center;">
            <svg class="result-icon" style="width: 64px; height: 64px; margin: 0 auto 16px; color: var(--success);" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <p class="result-title">嵌入成功</p>
            <p class="result-desc" id="result-desc">图片已生成，可下载保存</p>
            <div class="result-preview" id="result-preview"><img id="result-img" alt="结果"></div>
            <div class="key-section hidden" id="key-section"><p class="key-label">加密密钥 (请妥善保存)</p><div class="key-value-row"><p class="key-value" id="key-value"></p><button class="btn-copy" onclick="copyKey()">复制</button></div></div>
            <div class="result-actions"><button class="btn btn-download" onclick="downloadResult()">下载图片</button><button class="btn btn-reset" onclick="resetEmbed()">重新嵌入</button></div>
          </div>
        </div>
      </div>
      <div class="extract-section" id="extract-section">
        <div class="step-container" id="extract-step-1">
          <div class="upload-area" id="extract-upload-area" onclick="document.getElementById('extract-file-input').click()">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/><path d="M21 15l-5-5L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            <p class="upload-text">点击选择图片</p>
            <p class="upload-hint">选择包含隐写数据的图片</p>
          </div>
          <input type="file" id="extract-file-input" accept="image/*" style="display: none;" onchange="handleExtractFile(event)">
          <div class="preview-container" id="extract-preview-container"><img id="extract-preview-img" class="preview-img" alt="预览"><p class="preview-info" id="extract-preview-info"></p></div>
          <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin: 20px 0;"><span style="color: var(--text-muted);">启用解密</span><label class="toggle"><input type="checkbox" id="decrypt-toggle" onchange="toggleDecrypt(this)"><span class="toggle-slider"></span></label></div>
          <input type="text" id="decrypt-key" placeholder="输入解密密钥" style="width: 100%; padding: 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 14px; display: none; margin-bottom: 20px;">
          <button class="btn btn-primary" id="extract-btn" onclick="executeExtract()" disabled>开始提取</button>
        </div>
        <div class="step-container hidden" id="extract-step-2">
          <div class="processing-section" style="text-align: center; padding: 20px 0;">
            <div class="processing-icon"><div class="processing-circle"></div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></div>
            <p class="processing-title">正在提取...</p>
          </div>
        </div>
        <div class="step-container hidden" id="extract-step-3">
          <div class="result-section" style="text-align: center;">
            <svg class="result-icon" style="width: 64px; height: 64px; margin: 0 auto 16px; color: var(--success);" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <p class="result-title">提取成功</p>
            <p class="result-desc" id="extract-result-desc">提取到以下内容：</p>
            <div id="extract-error-section" class="error-detail hidden"><div class="error-code" id="extract-error-code"></div><div class="error-message" id="extract-error-message"></div></div>
            <div class="extract-result" id="text-result-section"><div class="extract-result-label">提取的文本内容</div><div class="extract-result-content" id="extracted-text"></div><button class="btn" style="margin-top: 12px; background: var(--primary); color: white;" onclick="copyExtractedText()">复制文本</button></div>
            <div class="extract-result hidden" id="file-result-section"><div class="extract-result-label">提取的文件</div><div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(34, 197, 94, 0.1); border-radius: 8px; margin-top: 12px;"><svg style="width: 40px; height: 40px; color: var(--success);" viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/></svg><div style="flex: 1; text-align: left;"><p class="extract-file-name" id="extracted-filename" style="font-weight: 600; font-size: 14px;"></p><p class="extract-file-size" id="extracted-filesize" style="font-size: 12px; color: var(--text-muted);"></p></div><button class="btn" style="background: var(--success); color: white; padding: 8px 16px;" onclick="downloadExtractedFile()">下载</button></div></div>
            <button class="btn btn-reset" style="margin-top: 20px;" onclick="resetExtract()">继续提取</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <script>
    const API_BASE = '/api';
    const embedState = { image: null, imageName: '', method: 'lsb', inputType: 'text', secretText: '', secretFile: null, secretFileName: '', useEncrypt: false, useCompress: false, resultImage: '', resultKey: '' };
    const extractState = { image: null, imageName: '', useDecrypt: false, decryptKey: '', isFile: false, extractedData: '', extractedFilename: '' };
    
    function switchTab(tab) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + tab).classList.add('active');
      document.getElementById('embed-section').classList.toggle('hidden', tab !== 'embed');
      document.getElementById('extract-section').classList.toggle('hidden', tab !== 'extract');
    }
    
    function handleFileSelect(e) {
      const file = e.target.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = function(evt) {
        embedState.image = evt.target.result.split(',')[1];
        embedState.imageName = file.name;
        document.getElementById('preview-img').src = evt.target.result;
        document.getElementById('preview-container').classList.add('show');
        document.getElementById('preview-info').textContent = file.name + ' (' + Math.round(file.size/1024) + ' KB)';
        document.getElementById('next-1-btn').disabled = false;
      };
      reader.readAsDataURL(file);
    }
    
    function goToStep(step) {
      document.querySelectorAll('#embed-section .step-container').forEach(s => s.classList.add('hidden'));
      document.getElementById('embed-step-' + step).classList.remove('hidden');
    }
    
    function selectInputType(type) {
      embedState.inputType = type;
      document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById('text-input-section').classList.toggle('hidden', type !== 'text');
      document.getElementById('file-input-section').classList.toggle('hidden', type !== 'file');
    }
    
    function handleSecretFile(e) {
      const file = e.target.files[0]; if (!file) return;
      embedState.secretFileName = file.name;
      document.getElementById('file-name-hint').textContent = file.name + ' (' + Math.round(file.size/1024) + ' KB)';
      const reader = new FileReader();
      reader.onload = function(evt) { embedState.secretFile = evt.target.result.split(',')[1]; };
      reader.readAsDataURL(file);
    }
    
    function toggleEncrypt(cb) { embedState.useEncrypt = cb.checked; }
    function toggleCompress(cb) { embedState.useCompress = cb.checked; }
    
    async function executeEmbed() {
      if (!embedState.image) return alert('请先选择图片');
      if (embedState.inputType === 'text') embedState.secretText = document.getElementById('secret-text').value;
      if (!embedState.secretText && !embedState.secretFile) return alert('请输入要隐藏的内容');
      
      goToStep(3);
      const payload = { image: embedState.image, type: embedState.inputType, content: embedState.inputType === 'text' ? {text: embedState.secretText} : {fileName: embedState.secretFileName, fileData: embedState.secretFile}, encryption: {enabled: embedState.useEncrypt}, method: embedState.method, compressResistant: embedState.useCompress };
      
      try {
        const resp = await fetch(API_BASE + '/embed', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
        const result = await resp.json();
        if (result.success) {
          embedState.resultImage = result.data.image;
          embedState.resultKey = result.data.encryption?.key || '';
          document.getElementById('result-img').src = 'data:image/png;base64,' + embedState.resultImage;
          document.getElementById('key-section').classList.toggle('hidden', !embedState.resultKey);
          document.getElementById('key-value').textContent = embedState.resultKey;
          goToStep(4);
        } else { alert('嵌入失败: ' + result.error.message); goToStep(2); }
      } catch (e) { alert('请求失败'); goToStep(2); }
    }
    
    function copyKey() { navigator.clipboard.writeText(embedState.resultKey); alert('已复制'); }
    function downloadResult() {
      const link = document.createElement('a'); link.href = 'data:image/png;base64,' + embedState.resultImage; link.download = 'stego_image.png'; link.click();
    }
    function resetEmbed() { location.reload(); }
    
    function handleExtractFile(e) {
      const file = e.target.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = function(evt) {
        extractState.image = evt.target.result.split(',')[1];
        extractState.imageName = file.name;
        document.getElementById('extract-preview-img').src = evt.target.result;
        document.getElementById('extract-preview-container').classList.add('show');
        document.getElementById('extract-preview-info').textContent = file.name;
        document.getElementById('extract-btn').disabled = false;
      };
      reader.readAsDataURL(file);
    }
    
    function toggleDecrypt(cb) {
      extractState.useDecrypt = cb.checked;
      document.getElementById('decrypt-key').style.display = cb.checked ? 'block' : 'none';
    }
    
    async function executeExtract() {
      if (!extractState.image) return;
      extractState.decryptKey = document.getElementById('decrypt-key').value;
      document.getElementById('extract-step-1').classList.add('hidden');
      document.getElementById('extract-step-2').classList.remove('hidden');
      
      const payload = { image: extractState.image, decryption: {enabled: extractState.useDecrypt, key: extractState.decryptKey} };
      
      try {
        const resp = await fetch(API_BASE + '/extract', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
        const result = await resp.json();
        document.getElementById('extract-step-2').classList.add('hidden');
        document.getElementById('extract-step-3').classList.remove('hidden');
        
        if (result.success) {
          const data = result.data;
          if (data.type === 'file') {
            extractState.isFile = true;
            extractState.extractedData = data.fileData;
            extractState.extractedFilename = data.fileName;
            document.getElementById('file-result-section').classList.remove('hidden');
            document.getElementById('text-result-section').classList.add('hidden');
            document.getElementById('extracted-filename').textContent = data.fileName;
            document.getElementById('extracted-filesize').textContent = data.fileData ? Math.round(data.fileData.length * 3 / 4) + ' bytes' : '-';
          } else {
            document.getElementById('text-result-section').classList.remove('hidden');
            document.getElementById('file-result-section').classList.add('hidden');
            document.getElementById('extracted-text').textContent = data.text || '(无内容)';
          }
        } else {
          document.getElementById('extract-error-section').classList.remove('hidden');
          document.getElementById('extract-error-code').textContent = result.error.code;
          document.getElementById('extract-error-message').textContent = result.error.message;
        }
      } catch (e) { alert('请求失败'); document.getElementById('extract-step-2').classList.add('hidden'); document.getElementById('extract-step-1').classList.remove('hidden'); }
    }
    
    function copyExtractedText() { navigator.clipboard.writeText(document.getElementById('extracted-text').textContent); alert('已复制'); }
    function downloadExtractedFile() {
      const link = document.createElement('a'); link.href = 'data:application/octet-stream;base64,' + extractState.extractedData; link.download = extractState.extractedFilename; link.click();
    }
    function resetExtract() { location.reload(); }
  </script>
</body>
</html>'''
        
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        return [html.encode('utf-8')]
    
    # API 路径
    if path == '/api/health':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        body = json.dumps({'success': True, 'data': {'status': 'ok'}})
        start_response(status, headers)
        return [body.encode()]
    
    if path == '/api/embed' and method == 'POST':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        body = json.dumps({'success': False, 'error': {'code': 'DEMO_MODE', 'message': '演示模式 - 请在本地运行完整功能: cd backend && python run.py'}})
        start_response(status, headers)
        return [body.encode()]
    
    if path == '/api/extract' and method == 'POST':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        body = json.dumps({'success': False, 'error': {'code': 'DEMO_MODE', 'message': '演示模式 - 请在本地运行完整功能'}})
        start_response(status, headers)
        return [body.encode()]
    
    # 404
    status = '404 Not Found'
    headers = [('Content-Type', 'text/plain')]
    body = 'Not Found'
    start_response(status, headers)
    return [body.encode()]

app = handler
application = handler