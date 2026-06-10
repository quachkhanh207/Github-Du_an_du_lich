# Github-Du_an_du_lich
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ứng dụng du lịch Việt Nam</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0D1B2A;
      --surface: #142030;
      --surface2: #1C2E42;
      --accent: #FF6B35;
      --accent2: #00C9A7;
      --gold: #F5A623;
      --text: #F0EBE3;
      --text2: #8FA3B1;
      --border: rgba(255,255,255,0.08);
      --r: 14px;
    }
    body { 
      background: #000; 
      display: flex; 
      justify-content: center; 
      align-items: center; 
      min-height: 100vh;
    }
    .app {
      width: 360px;
      height: 740px;
      background: var(--bg);
      font-family: 'Segoe UI', sans-serif;
      overflow: hidden;
      border-radius: 32px;
      border: 1px solid var(--border);
      position: relative;
      display: flex;
      flex-direction: column;
    }
    .status-bar {
      display: flex; justify-content: space-between; align-items: center;
      padding: 12px 20px 4px;
      font-size: 11px; color: var(--text2);
      position: relative; z-index: 10;
    }
    .screen-container {
      flex: 1;
      overflow-y: auto;
      padding-bottom: 80px;
      scrollbar-width: none;
    }
    .screen-container::-webkit-scrollbar { display: none; }
    .screen { display: none; }
    .screen.active { display: block; }
    .nav {
      position: absolute; bottom: 0; left: 0; right: 0;
      display: flex; background: var(--surface);
      border-top: 1px solid var(--border);
      border-radius: 0 0 32px 32px;
      overflow: hidden; z-index: 10;
    }
    .nav-btn {
      flex: 1; padding: 10px 0 12px;
      display: flex; flex-direction: column; align-items: center; gap: 3px;
      background: none; border: none; cursor: pointer; color: var(--text2);
      font-size: 10px; transition: color 0.2s;
    }
    .nav-btn i { font-size: 20px; }
    .nav-btn.active { color: var(--accent); }
    .nav-btn.active .nav-dot {
      width: 4px; height: 4px; background: var(--accent);
      border-radius: 50%; margin: 0 auto;
    }

    /* ---- HOME ---- */
    .hero {
      background: linear-gradient(160deg, #1a3a5c 0%, #0d1b2a 60%);
      padding: 20px 20px 28px;
      position: relative; overflow: hidden;
    }
    .hero::before {
      content: '';
      position: absolute; top: -40px; right: -40px;
      width: 200px; height: 200px;
      background: radial-gradient(circle, rgba(255,107,53,0.15) 0%, transparent 70%);
      border-radius: 50%;
    }
    .greeting { font-size: 12px; color: var(--text2); margin-bottom: 4px; }
    .hero-title { font-size: 22px; font-weight: 700; color: var(--text); line-height: 1.2; }
    .hero-title span { color: var(--accent); }
    .search-bar {
      margin-top: 16px;
      display: flex; align-items: center; gap: 10px;
      background: var(--surface2); border-radius: 12px;
      padding: 10px 14px; border: 1px solid var(--border);
    }
    .search-bar i { color: var(--text2); font-size: 16px; }
    .search-bar input {
      background: none; border: none; outline: none;
      color: var(--text); font-size: 13px; flex: 1;
    }
    .section-title {
      font-size: 13px; font-weight: 600; color: var(--text);
      padding: 16px 20px 10px; letter-spacing: 0.3px;
    }
    .dest-scroll {
      display: flex; gap: 12px; padding: 0 20px 4px;
      overflow-x: auto; scrollbar-width: none;
    }
    .dest-scroll::-webkit-scrollbar { display: none; }
    .dest-card {
      min-width: 130px; border-radius: var(--r);
      overflow: hidden; position: relative; cursor: pointer;
      border: 1px solid var(--border); flex-shrink: 0;
    }
    .dest-img {
      height: 90px;
      display: flex; align-items: center; justify-content: center;
      font-size: 36px;
    }
    .dest-img.ha-long { background: linear-gradient(135deg, #0f4c6e, #1a8fa0); }
    .dest-img.hoi-an { background: linear-gradient(135deg, #7a4f1c, #c4862f); }
    .dest-img.sapa { background: linear-gradient(135deg, #1a5c2a, #2ecc71); }
    .dest-img.phu-quoc { background: linear-gradient(135deg, #0077b6, #90e0ef); }
    .dest-label {
      background: var(--surface2); padding: 8px 10px;
    }
    .dest-name { font-size: 12px; font-weight: 600; color: var(--text); }
    .dest-sub { font-size: 10px; color: var(--text2); }
    .quick-actions {
      display: grid; grid-template-columns: 1fr 1fr;
      gap: 10px; padding: 0 20px;
    }
    .qa-card {
      background: var(--surface); border-radius: var(--r);
      padding: 14px; border: 1px solid var(--border); cursor: pointer;
      display: flex; align-items: center; gap: 10px;
      transition: border-color 0.2s;
    }
    .qa-card:hover { border-color: var(--accent); }
    .qa-icon {
      width: 38px; height: 38px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; flex-shrink: 0;
    }
    .qa-icon.orange { background: rgba(255,107,53,0.15); color: var(--accent); }
    .qa-icon.teal { background: rgba(0,201,167,0.15); color: var(--accent2); }
    .qa-icon.gold { background: rgba(245,166,35,0.15); color: var(--gold); }
    .qa-icon.blue { background: rgba(74,144,226,0.15); color: #4A90E2; }
    .qa-label { font-size: 12px; font-weight: 600; color: var(--text); }
    .qa-sub { font-size: 10px; color: var(--text2); margin-top: 2px; }

    /* ---- ITINERARY ---- */
    .itin-header {
      padding: 16px 20px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
    }
    .itin-title { font-size: 17px; font-weight: 700; color: var(--text); }
    .itin-sub { font-size: 11px; color: var(--text2); margin-top: 2px; }
    .trip-selector {
      display: flex; gap: 8px; padding: 14px 20px 0; overflow-x: auto; scrollbar-width: none;
    }
    .trip-selector::-webkit-scrollbar { display: none; }
    .trip-pill {
      padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border);
      background: var(--surface); color: var(--text2);
      font-size: 11px; cursor: pointer; white-space: nowrap; flex-shrink: 0;
      transition: all 0.2s;
    }
    .trip-pill.active { background: var(--accent); border-color: var(--accent); color: white; }
    .timeline { padding: 14px 20px; }
    .day-group { margin-bottom: 16px; }
    .day-label {
      font-size: 11px; font-weight: 700; color: var(--accent2);
      letter-spacing: 1px; text-transform: uppercase; margin-bottom: 10px;
    }
    .timeline-item {
      display: flex; gap: 12px; margin-bottom: 10px;
    }
    .tl-left {
      display: flex; flex-direction: column; align-items: center; width: 36px;
    }
    .tl-dot {
      width: 10px; height: 10px; border-radius: 50%;
      border: 2px solid var(--accent); background: var(--bg); flex-shrink: 0;
    }
    .tl-line { flex: 1; width: 2px; background: var(--border); margin: 2px 0; }
    .tl-card {
      flex: 1; background: var(--surface); border-radius: 10px;
      padding: 10px 12px; border: 1px solid var(--border);
    }
    .tl-time { font-size: 10px; color: var(--accent); margin-bottom: 2px; }
    .tl-name { font-size: 13px; font-weight: 600; color: var(--text); }
    .tl-note { font-size: 11px; color: var(--text2); margin-top: 2px; }
    .tl-tag {
      display: inline-block; font-size: 9px; padding: 2px 7px;
      border-radius: 6px; margin-top: 4px; font-weight: 600;
    }
    .tag-food { background: rgba(245,166,35,0.2); color: var(--gold); }
    .tag-sight { background: rgba(0,201,167,0.2); color: var(--accent2); }
    .tag-stay { background: rgba(74,144,226,0.2); color: #4A90E2; }
    .add-btn {
      margin: 0 20px; padding: 12px;
      background: rgba(255,107,53,0.12); border: 1px dashed rgba(255,107,53,0.4);
      border-radius: 12px; color: var(--accent); font-size: 13px;
      cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;
    }

    /* ---- CHATBOT ---- */
    .chat-header {
      display: flex; align-items: center; gap: 12px;
      padding: 16px 20px; background: var(--surface);
      border-bottom: 1px solid var(--border);
    }
    .bot-avatar {
      width: 38px; height: 38px; border-radius: 12px;
      background: linear-gradient(135deg, var(--accent), var(--gold));
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; color: white;
    }
    .bot-name { font-size: 14px; font-weight: 700; color: var(--text); }
    .bot-status { font-size: 11px; color: var(--accent2); }
    .chat-body {
      padding: 14px 16px;
      display: flex; flex-direction: column; gap: 10px;
      min-height: 280px;
    }
    .msg { display: flex; gap: 8px; max-width: 85%; }
    .msg.bot { align-self: flex-start; }
    .msg.user { align-self: flex-end; flex-direction: row-reverse; }
    .msg-avatar {
      width: 28px; height: 28px; border-radius: 8px;
      background: linear-gradient(135deg, var(--accent), var(--gold));
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; flex-shrink: 0;
    }
    .msg-bubble {
      padding: 9px 13px; border-radius: 14px;
      font-size: 12px; line-height: 1.5;
    }
    .msg.bot .msg-bubble {
      background: var(--surface2); color: var(--text);
      border-radius: 4px 14px 14px 14px;
    }
    .msg.user .msg-bubble {
      background: var(--accent); color: white;
      border-radius: 14px 4px 14px 14px;
    }
    .suggestions {
      display: flex; flex-wrap: wrap; gap: 6px; padding: 0 16px 8px;
    }
    .suggest-chip {
      padding: 6px 12px; border: 1px solid var(--border);
      border-radius: 20px; font-size: 11px; color: var(--text2);
      background: var(--surface); cursor: pointer;
      transition: all 0.2s;
    }
    .suggest-chip:hover { border-color: var(--accent); color: var(--accent); }
    .chat-input-bar {
      display: flex; gap: 8px; padding: 10px 16px;
      background: var(--surface); border-top: 1px solid var(--border);
    }
    .chat-input {
      flex: 1; background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; padding: 8px 12px;
      color: var(--text); font-size: 12px; outline: none;
    }
    .chat-send {
      width: 36px; height: 36px; border-radius: 10px;
      background: var(--accent); border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center; color: white;
    }

    /* ---- CAMERA ---- */
    .cam-header {
      padding: 16px 20px; display: flex; justify-content: space-between; align-items: center;
    }
    .cam-title { font-size: 17px; font-weight: 700; color: var(--text); }
    .cam-viewfinder {
      margin: 0 20px;
      height: 220px; border-radius: 18px;
      background: #000;
      border: 1px solid var(--border); position: relative; overflow: hidden;
      display: flex; align-items: center; justify-content: center;
    }
    
    /* Hiệu ứng chớp sáng camera */
    .camera-flash {
      position: absolute; inset: 0;
      background: white; opacity: 0;
      z-index: 3; pointer-events: none;
    }
    .camera-flash.active {
      animation: flashEffect 0.3s ease-out;
    }
    @keyframes flashEffect {
      0% { opacity: 0.85; }
      100% { opacity: 0; }
    }

    .cam-corner {
      position: absolute; width: 20px; height: 20px;
      border-color: var(--accent2); border-style: solid; opacity: 0.8; z-index: 2;
    }
    .cam-corner.tl { top: 12px; left: 12px; border-width: 2px 0 0 2px; }
    .cam-corner.tr { top: 12px; right: 12px; border-width: 2px 2px 0 0; }
    .cam-corner.bl { bottom: 12px; left: 12px; border-width: 0 0 2px 2px; }
    .cam-corner.br { bottom: 12px; right: 12px; border-width: 0 2px 2px 0; }
    .cam-label {
      position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
      font-size: 10px; color: var(--accent2); letter-spacing: 1px;
      background: rgba(0,0,0,0.6); padding: 3px 10px; border-radius: 20px; z-index: 2;
    }
    .cam-controls {
      display: flex; align-items: center; justify-content: center; gap: 24px;
      padding: 20px;
    }
    .cam-btn-sm {
      width: 44px; height: 44px; border-radius: 12px;
      background: var(--surface); border: 1px solid var(--border);
      display: flex; align-items: center; justify-content: center;
      color: var(--text2); font-size: 20px; cursor: pointer;
    }
    .cam-btn-main {
      width: 64px; height: 64px; border-radius: 50%;
      background: white; border: 4px solid rgba(255,255,255,0.3);
      cursor: pointer; position: relative;
    }
    .cam-btn-main::after {
      content: ''; position: absolute;
      inset: 4px; border-radius: 50%; background: white;
    }
    .photos-grid {
      display: grid; grid-template-columns: 1fr 1fr 1fr;
      gap: 6px; padding: 0 20px;
    }
    .photo-thumb {
      aspect-ratio: 1; border-radius: 8px; overflow: hidden;
      display: flex; align-items: center; justify-content: center;
      font-size: 24px; background: var(--surface2);
      border: 1px solid var(--border); cursor: pointer;
    }
    .photo-thumb img {
      width: 100%; height: 100%; object-fit: cover;
    }
    .ai-tag {
      margin: 10px 20px 0;
      background: rgba(0,201,167,0.1); border: 1px solid rgba(0,201,167,0.25);
      border-radius: 10px; padding: 10px 14px;
      display: flex; align-items: center; gap: 10px;
    }
    .ai-tag-icon { font-size: 20px; color: var(--accent2); }
    .ai-tag-text { font-size: 11px; color: var(--text2); }
    .ai-tag-title { font-size: 12px; font-weight: 600; color: var(--accent2); margin-bottom: 1px; }

    /* ---- ALBUM CARDS (XẾP CHỒNG) ---- */
    .albums-grid {
      display: grid; grid-template-columns: 1fr 1fr;
      gap: 16px; padding: 0 20px 16px;
    }
    .album-card {
      cursor: pointer; transition: transform 0.25s, box-shadow 0.25s;
    }
    .album-card:hover { transform: translateY(-3px); }
    .album-stack {
      position: relative; aspect-ratio: 1;
      margin-bottom: 8px;
    }
    .album-stack-img {
      position: absolute; width: 100%; height: 100%;
      border-radius: 12px; object-fit: cover;
      border: 1px solid var(--border);
      background: var(--surface2);
    }
    .album-stack-img.stack-back {
      transform: rotate(6deg) translate(5px, -5px) scale(0.88);
      opacity: 0.35; z-index: 1;
    }
    .album-stack-img.stack-mid {
      transform: rotate(-3deg) translate(-3px, -3px) scale(0.94);
      opacity: 0.6; z-index: 2;
    }
    .album-stack-img.stack-front {
      transform: none; opacity: 1; z-index: 3;
      box-shadow: 0 4px 14px rgba(0,0,0,0.5);
    }
    .album-count-badge {
      position: absolute; top: 8px; right: 8px; z-index: 4;
      background: rgba(0,0,0,0.6); color: white;
      font-size: 10px; font-weight: 700; padding: 3px 9px;
      border-radius: 12px; backdrop-filter: blur(6px);
      border: 1px solid rgba(255,255,255,0.1);
    }
    .album-info { padding: 0 2px; }
    .album-name {
      font-size: 12px; font-weight: 600; color: var(--text);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .album-date { font-size: 10px; color: var(--text2); margin-top: 2px; }

    /* ---- ALBUM DETAIL LAYER ---- */
    .album-detail-layer {
      position: absolute; inset: 0; background: var(--bg); z-index: 12;
      display: none; flex-direction: column;
    }
    .album-detail-layer.active { display: flex; }
    .album-detail-header {
      display: flex; align-items: center; gap: 12px;
      padding: 14px 16px; background: var(--surface);
      border-bottom: 1px solid var(--border); flex-shrink: 0;
    }
    .album-detail-back {
      width: 34px; height: 34px; border-radius: 10px;
      background: var(--surface2); border: 1px solid var(--border);
      display: flex; align-items: center; justify-content: center;
      color: var(--text); font-size: 16px; cursor: pointer;
    }
    .album-detail-title { font-size: 14px; font-weight: 700; color: var(--text); }
    .album-detail-sub { font-size: 11px; color: var(--text2); margin-top: 1px; }
    .album-detail-grid {
      flex: 1; overflow-y: auto; padding: 12px 16px 80px;
      display: grid; grid-template-columns: 1fr 1fr 1fr;
      gap: 6px; align-content: start;
      scrollbar-width: none;
    }
    .album-detail-grid::-webkit-scrollbar { display: none; }
    .album-empty {
      grid-column: 1 / -1; text-align: center;
      padding: 40px 20px; color: var(--text2); font-size: 12px;
    }

    /* MÀN HÌNH PREVIEW XEM LẠI ẢNH VỪA CHỤP */
    .cam-preview-layer {
      position: absolute; inset: 0; background: #000; z-index: 5;
      display: none; flex-direction: column;
    }
    .cam-preview-layer.active { display: flex; }
    .preview-img-container { width: 100%; height: 220px; margin-top: 53px; background: #222; }
    .preview-img-container img { width: 100%; height: 100%; object-fit: cover; }
    .preview-controls {
      display: flex; align-items: center; justify-content: space-between;
      padding: 20px 30px; margin-top: 10px;
    }

    /* MÀN HÌNH PHÓNG TO XEM CHI TIẾT ALBUM (CÓ THÔNG TIN & NÚT XÓA) */
    .lightbox-layer {
      position: absolute; inset: 0; background: rgba(0, 0, 0, 0.95); z-index: 15;
      display: none; flex-direction: column; justify-content: center; align-items: center;
    }
    .lightbox-layer.active { display: flex; }
    .lightbox-close {
      position: absolute; top: 50px; right: 20px;
      width: 36px; height: 36px; border-radius: 50%;
      background: rgba(255,255,255,0.1); border: none; color: white;
      display: flex; align-items: center; justify-content: center; font-size: 18px; cursor: pointer;
    }
    .lightbox-img-box { width: 100%; max-height: 380px; display: flex; align-items: center; justify-content: center; }
    .lightbox-img-box img { width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; }
    
    .lightbox-meta {
      text-align: center; margin-top: 14px; color: var(--text);
      display: flex; flex-direction: column; align-items: center; gap: 4px;
    }
    .lightbox-loc { font-size: 13px; font-weight: 600; color: var(--accent2); display: flex; align-items: center; gap: 4px; }
    .lightbox-date { font-size: 11px; color: var(--text2); display: flex; align-items: center; gap: 4px; }

    /* ---- LIGHTBOX NAVIGATION (SWIPE) ---- */
    .lightbox-counter {
      position: absolute; top: 52px; left: 50%; transform: translateX(-50%);
      font-size: 12px; color: rgba(255,255,255,0.7); font-weight: 600;
      background: rgba(0,0,0,0.5); padding: 4px 14px;
      border-radius: 12px; z-index: 2;
      backdrop-filter: blur(4px); display: none;
    }
    .lightbox-counter.visible { display: block; }
    .lightbox-nav {
      position: absolute; top: 50%; transform: translateY(-50%);
      width: 32px; height: 32px; border-radius: 50%;
      background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.12);
      display: none; align-items: center; justify-content: center;
      color: white; font-size: 14px; cursor: pointer;
      transition: background 0.2s; z-index: 2;
      backdrop-filter: blur(4px);
    }
    .lightbox-nav:hover { background: rgba(255,255,255,0.25); }
    .lightbox-nav.prev { left: 8px; }
    .lightbox-nav.next { right: 8px; }
    .lightbox-nav.visible { display: flex; }
    .lightbox-img-box.slide-left { animation: lbSlideLeft 0.22s ease-out; }
    .lightbox-img-box.slide-right { animation: lbSlideRight 0.22s ease-out; }
    @keyframes lbSlideLeft {
      0% { transform: translateX(50px); opacity: 0.2; }
      100% { transform: translateX(0); opacity: 1; }
    }
    @keyframes lbSlideRight {
      0% { transform: translateX(-50px); opacity: 0.2; }
      100% { transform: translateX(0); opacity: 1; }
    }

    /* ĐIỀU KHIỂN CHUNG NÚT BẤM */
    .btn-action-side {
      width: 50px; height: 50px; border-radius: 50%;
      background: var(--surface2); color: var(--text);
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; cursor: pointer; border: 1px solid var(--border);
    }
    .btn-action-side.cancel { color: #FC5C65; }
    .btn-action-side.save { color: #26DE81; background: rgba(38,222,129,0.1); border-color: rgba(38,222,129,0.3); }
    .btn-action-center {
      padding: 12px 24px; border-radius: 25px;
      background: linear-gradient(135deg, var(--accent), var(--gold));
      color: white; font-size: 13px; font-weight: 700; cursor: pointer;
      display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 15px rgba(255,107,53,0.3);
    }

    /* ---- GOOGLE LENS BUTTON ---- */
    .google-search-row {
      display: flex; justify-content: center; padding: 8px 30px 0;
    }
    .btn-google-lens {
      width: 100%; padding: 11px; border-radius: 12px;
      background: rgba(66,133,244,0.12); border: 1px solid rgba(66,133,244,0.3);
      color: #7aadff; font-size: 12px; font-weight: 600; cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      transition: all 0.2s;
    }
    .btn-google-lens:hover {
      background: rgba(66,133,244,0.2); border-color: rgba(66,133,244,0.5);
    }
    .btn-google-lens i { font-size: 16px; }

    /* ---- PROFILE ---- */
    .profile-hero {
      background: linear-gradient(160deg, #1a2d42, #0d1b2a);
      padding: 20px 20px 60px; text-align: center; position: relative;
    }
    .profile-bg-pattern {
      position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      background-image: radial-gradient(circle at 20% 20%, rgba(255,107,53,0.08) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(0,201,167,0.08) 0%, transparent 50%);
    }
    .profile-avatar {
      width: 72px; height: 72px; border-radius: 22px;
      background: linear-gradient(135deg, var(--accent), var(--gold));
      display: flex; align-items: center; justify-content: center;
      font-size: 32px; margin: 0 auto 10px; position: relative; z-index: 1;
      border: 3px solid rgba(255,255,255,0.15);
    }
    .profile-name { font-size: 18px; font-weight: 700; color: var(--text); position: relative; z-index: 1; }
    .profile-handle { font-size: 12px; color: var(--text2); position: relative; z-index: 1; margin-top: 2px; }
    .profile-stats {
      display: flex; justify-content: center; gap: 28px;
      margin-top: 14px; position: relative; z-index: 1;
    }
    .pstat { text-align: center; }
    .pstat-num { font-size: 18px; font-weight: 700; color: var(--text); }
    .pstat-label { font-size: 10px; color: var(--text2); }
    .profile-badges {
      margin: -20px 20px 0; position: relative; z-index: 2;
      display: flex; gap: 8px;
    }
    .badge {
      flex: 1; background: var(--surface); border-radius: 12px;
      border: 1px solid var(--border); padding: 10px 8px; text-align: center;
    }
    .badge-icon { font-size: 20px; margin-bottom: 2px; }
    .badge-name { font-size: 9px; color: var(--text2); }
    .profile-trips { padding: 14px 20px; }
    .trip-card {
      display: flex; gap: 12px; align-items: center;
      background: var(--surface); border-radius: 12px;
      padding: 12px 14px; border: 1px solid var(--border); margin-bottom: 8px;
    }
    .trip-thumb {
      width: 48px; height: 48px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 22px; flex-shrink: 0;
    }
    .trip-thumb.t1 { background: linear-gradient(135deg, #0f4c6e, #1a8fa0); }
    .trip-thumb.t2 { background: linear-gradient(135deg, #7a4f1c, #c4862f); }
    .trip-info { flex: 1; }
    .trip-tname { font-size: 13px; font-weight: 600; color: var(--text); }
    .trip-tdate { font-size: 11px; color: var(--text2); margin-top: 2px; }
    .trip-trating { font-size: 11px; color: var(--gold); }
  </style>
</head>
<body>

<div class="app">
  <div class="status-bar">
    <span>9:41</span>
    <span style="display:flex;gap:6px;align-items:center;">
      <i class="ti ti-wifi" style="font-size:13px"></i>
      <i class="ti ti-battery" style="font-size:13px"></i>
    </span>
  </div>

  <div class="screen-container">
    
    <div id="screen-home" class="screen active">
      <div class="hero">
        <div class="greeting">Xin chào, Minh Tuấn 👋</div>
        <div class="hero-title">Khám phá <span>Việt Nam</span><br>theo cách của bạn</div>
        <div class="search-bar">
          <i class="ti ti-search"></i>
          <input type="text" placeholder="Tìm điểm đến, tour, trải nghiệm..." />
          <i class="ti ti-adjustments-horizontal" style="color:var(--accent);font-size:16px;cursor:pointer"></i>
        </div>
      </div>

      <div class="section-title">🔥 Điểm đến nổi bật</div>
      <div class="dest-scroll">
        <div class="dest-card">
          <div class="dest-img ha-long">🏔️</div>
          <div class="dest-label">
            <div class="dest-name">Hạ Long</div>
            <div class="dest-sub">⭐ 4.9 · Quảng Ninh</div>
          </div>
        </div>
        <div class="dest-card">
          <div class="dest-img hoi-an">🏮</div>
          <div class="dest-label">
            <div class="dest-name">Hội An</div>
            <div class="dest-sub">⭐ 4.8 · Quảng Nam</div>
          </div>
        </div>
        <div class="dest-card">
          <div class="dest-img sapa">🌿</div>
          <div class="dest-label">
            <div class="dest-name">Sa Pa</div>
            <div class="dest-sub">⭐ 4.7 · Lào Cai</div>
          </div>
        </div>
        <div class="dest-card">
          <div class="dest-img phu-quoc">🏝️</div>
          <div class="dest-label">
            <div class="dest-name">Phú Quốc</div>
            <div class="dest-sub">⭐ 4.8 · Kiên Giang</div>
          </div>
        </div>
      </div>

      <div class="section-title">⚡ Chức năng</div>
      <div class="quick-actions">
        <div class="qa-card" onclick="switchScreen('itinerary')">
          <div class="qa-icon orange"><i class="ti ti-route"></i></div>
          <div><div class="qa-label">Lộ trình</div><div class="qa-sub">Xây dựng chuyến đi</div></div>
        </div>
        <div class="qa-card" onclick="switchScreen('chat')">
          <div class="qa-icon teal"><i class="ti ti-message-chatbot"></i></div>
          <div><div class="qa-label">Chatbot</div><div class="qa-sub">Hỏi đáp du lịch</div></div>
        </div>
        <div class="qa-card" onclick="switchScreen('camera')">
          <div class="qa-icon gold"><i class="ti ti-camera"></i></div>
          <div><div class="qa-label">Chụp ảnh</div><div class="qa-sub">Lưu kỷ niệm AI</div></div>
        </div>
        <div class="qa-card" onclick="switchScreen('profile')">
          <div class="qa-icon blue"><i class="ti ti-user-circle"></i></div>
          <div><div class="qa-label">Hồ sơ</div><div class="qa-sub">Trang cá nhân</div></div>
        </div>
      </div>
    </div>

    <div id="screen-itinerary" class="screen">
      <div class="itin-header">
        <div class="itin-title">🗺️ Lộ trình của tôi</div>
        <div class="itin-sub">3 chuyến đang lên kế hoạch</div>
      </div>
      <div class="trip-selector">
        <div class="trip-pill active">Hội An 5N</div>
        <div class="trip-pill">Hạ Long 3N</div>
        <div class="trip-pill">Sa Pa 4N</div>
        <div class="trip-pill" style="color:var(--accent);border-color:var(--accent)">+ Thêm mới</div>
      </div>
      <div class="timeline">
        <div class="day-group">
          <div class="day-label">Ngày 1 · 20/06</div>
          <div class="timeline-item">
            <div class="tl-left"><div class="tl-dot"></div><div class="tl-line"></div></div>
            <div class="tl-card">
              <div class="tl-time">08:00</div>
              <div class="tl-name">Phố cổ Hội An</div>
              <div class="tl-note">Dạo bộ, chụp ảnh buổi sáng sớm</div>
              <span class="tl-tag tag-sight">Tham quan</span>
            </div>
          </div>
          <div class="timeline-item">
            <div class="tl-left"><div class="tl-dot"></div><div class="tl-line"></div></div>
            <div class="tl-card">
              <div class="tl-time">12:00</div>
              <div class="tl-name">Cơm gà Bà Buội</div>
              <div class="tl-note">Đặc sản nổi tiếng, gần chợ Hội An</div>
              <span class="tl-tag tag-food">Ẩm thực</span>
            </div>
          </div>
          <div class="timeline-item">
            <div class="tl-left"><div class="tl-dot"></div></div>
            <div class="tl-card">
              <div class="tl-time">15:00</div>
              <div class="tl-name">Cầu Nhật Bản</div>
              <div class="tl-note">Di tích lịch sử, check-in nổi tiếng</div>
              <span class="tl-tag tag-sight">Tham quan</span>
            </div>
          </div>
        </div>
      </div>
      <div class="add-btn"><i class="ti ti-plus"></i> Thêm địa điểm</div>
    </div>

    <div id="screen-chat" class="screen">
      <div class="chat-header">
        <div class="bot-avatar">🤖</div>
        <div>
          <div class="bot-name">TravelBot AI</div>
          <div class="bot-status">● Đang trực tuyến</div>
        </div>
      </div>
      <div class="chat-body" id="chatBody">
        <div class="msg bot">
          <div class="msg-avatar">🤖</div>
          <div class="msg-bubble">Xin chào! Tôi là TravelBot 🌏 Tôi có thể giúp bạn lên kế hoạch, tìm địa điểm, gợi ý ẩm thực và mọi thứ về du lịch Việt Nam!</div>
        </div>
      </div>
      <div class="chat-input-bar">
        <input class="chat-input" id="chatInput" placeholder="Hỏi về điểm đến, ẩm thực..." onkeydown="if(event.key==='Enter')sendMsg()" />
        <button class="chat-send" onclick="sendMsg()"><i class="ti ti-send"></i></button>
      </div>
    </div>

    <div id="screen-camera" class="screen" style="position: relative;">
      
      <div class="cam-preview-layer" id="previewLayer">
        <div class="cam-header"><div class="cam-title">👀 Xem lại ảnh</div></div>
        <div class="preview-img-container"><img id="previewImg" src="" alt="Ảnh vừa chụp"></div>
        <div class="preview-controls">
          <div class="btn-action-side cancel" onclick="cancelPhoto()"><i class="ti ti-trash"></i></div>
          <div class="btn-action-center" onclick="askAIWithPhoto()"><i class="ti ti-sparkles"></i> Hỏi AI Địa Danh</div>
          <div class="btn-action-side save" onclick="savePhoto()"><i class="ti ti-check"></i></div>
        </div>
        <div class="google-search-row">
          <div class="btn-google-lens" onclick="searchGoogleWithPhoto()">
            <i class="ti ti-brand-google"></i>
            <span>Phân tích ảnh bằng Google</span>
          </div>
        </div>
      </div>

      <div class="lightbox-layer" id="lightboxLayer">
        <button class="lightbox-close" onclick="closeLightbox()"><i class="ti ti-x"></i></button>
        <div class="lightbox-counter" id="lightboxCounter"></div>
        <button class="lightbox-nav prev" id="lightboxPrev" onclick="lightboxGoPrev()"><i class="ti ti-chevron-left"></i></button>
        <button class="lightbox-nav next" id="lightboxNext" onclick="lightboxGoNext()"><i class="ti ti-chevron-right"></i></button>
        <div class="lightbox-img-box" id="lightboxImgBox">
          <img id="lightboxImg" src="" alt="Xem chi tiết kỷ niệm">
        </div>
        <div class="lightbox-meta">
          <div id="lightboxLoc" class="lightbox-loc"></div>
          <div id="lightboxDate" class="lightbox-date"></div>
          <div style="display:flex; gap:12px; margin-top:12px; align-items:center;">
            <button class="btn-action-side" onclick="searchGoogleLightbox()" style="width:42px;height:42px;font-size:16px;color:#4285F4;background:rgba(66,133,244,0.1);border-color:rgba(66,133,244,0.3);" title="Phân tích bằng Google">
              <i class="ti ti-brand-google"></i>
            </button>
            <button class="btn-action-side cancel" id="lightboxDeleteBtn" style="width:42px;height:42px;font-size:16px;">
              <i class="ti ti-trash"></i>
            </button>
          </div>
        </div>
      </div>

      <div class="cam-header">
        <div class="cam-title">📸 Kỷ niệm</div>
      </div>
      
      <div class="cam-viewfinder">
        <video id="webcam" autoplay playsinline style="width: 100%; height: 100%; object-fit: cover;"></video>
        <div class="camera-flash" id="cameraFlash"></div>
        <div class="cam-corner tl"></div><div class="cam-corner tr"></div>
        <div class="cam-corner bl"></div><div class="cam-corner br"></div>
        <div class="cam-label">AI · Nhận diện địa điểm</div>
      </div>

      <canvas id="photo-canvas" style="display: none;" width="640" height="480"></canvas>

      <div class="cam-controls">
        <div class="cam-btn-sm"><i class="ti ti-rotate"></i></div>
        <div class="cam-btn-main" onclick="takePhoto()"></div>
        <div class="cam-btn-sm"><i class="ti ti-sparkles"></i></div>
      </div>

      <div class="ai-tag">
        <div class="ai-tag-icon"><i class="ti ti-map-pin"></i></div>
        <div>
          <div class="ai-tag-title">AI nhận diện: Vịnh Hạ Long, Quảng Ninh</div>
          <div class="ai-tag-text">Tự động gắn thẻ vào lộ trình · Lưu vào album</div>
        </div>
      </div>
      
      <div class="section-title" style="padding-top:12px">📁 Album chuyến đi</div>
      <div class="albums-grid" id="albumGrid"></div>

      <div class="album-detail-layer" id="albumDetailLayer">
        <div class="album-detail-header">
          <button class="album-detail-back" onclick="closeAlbumDetail()"><i class="ti ti-arrow-left"></i></button>
          <div>
            <div class="album-detail-title" id="albumDetailTitle"></div>
            <div class="album-detail-sub" id="albumDetailSub"></div>
          </div>
        </div>
        <div class="album-detail-grid" id="albumDetailGrid"></div>
      </div>
    </div>

    <div id="screen-profile" class="screen">
      <div class="profile-hero">
        <div class="profile-bg-pattern"></div>
        <div class="profile-avatar">🧑</div>
        <div class="profile-name">Minh Tuấn</div>
        <div class="profile-handle">@minhtuantravel · Hà Nội</div>
        <div class="profile-stats">
          <div class="pstat"><div class="pstat-num">14</div><div class="pstat-label">Chuyến đi</div></div>
          <div class="pstat"><div class="pstat-num" id="profilePhotoCount">0</div><div class="pstat-label">Ảnh</div></div>
          <div class="pstat"><div class="pstat-num">52</div><div class="pstat-label">Địa điểm</div></div>
        </div>
      </div>
    </div>

  </div>

  <nav class="nav">
    <button class="nav-btn active" id="nav-home" onclick="switchScreen('home')"><i class="ti ti-home"></i><span>Trang chủ</span><div class="nav-dot"></div></button>
    <button class="nav-btn" id="nav-itinerary" onclick="switchScreen('itinerary')"><i class="ti ti-route"></i><span>Lộ trình</span></button>
    <button class="nav-btn" id="nav-chat" onclick="switchScreen('chat')"><i class="ti ti-message-chatbot"></i><span>Chatbot</span></button>
    <button class="nav-btn" id="nav-camera" onclick="switchScreen('camera')"><i class="ti ti-camera"></i><span>Ảnh</span></button>
    <button class="nav-btn" id="nav-profile" onclick="switchScreen('profile')"><i class="ti ti-user"></i><span>Hồ sơ</span></button>
  </nav>
</div>

<script>
// --- LOGIC ĐIỀU KHIỂN HỆ THỐNG CAMERA NÂNG CẤP ---
let cameraStream = null;
let latestCapturedPhotoData = null;

// Khởi tạo mảng dữ liệu (Tương thích thông minh với dữ liệu chuỗi cũ nếu có)
let savedPhotos = JSON.parse(localStorage.getItem('travel_app_photos')) || [];

// Dữ liệu điều hướng ảnh trong Lightbox (theo album)
let lightboxAlbumPhotos = [];
let lightboxCurrentIdx = -1;

// Nhóm ảnh theo Địa điểm + Ngày tạo Album
function groupPhotosByAlbum() {
  const albums = {};
  savedPhotos.forEach((photo, index) => {
    let location, dateShort;
    if (typeof photo === 'object') {
      location = (photo.location || 'Chưa xác định').trim();
      const fullDate = photo.date || '';
      dateShort = fullDate.split(' lúc')[0].trim() || 'Không rõ ngày';
    } else {
      location = 'Kỷ niệm';
      dateShort = 'Trước đây';
    }
    const albumKey = location + ' · ' + dateShort;
    if (!albums[albumKey]) {
      albums[albumKey] = { location, date: dateShort, key: albumKey, photos: [] };
    }
    albums[albumKey].photos.push({ data: photo, originalIndex: index });
  });
  return albums;
}

// Hàm render Album dạng xếp chồng nhóm theo địa điểm + ngày
function renderAlbum() {
  const albumGrid = document.getElementById('albumGrid');
  if (!albumGrid) return;
  albumGrid.innerHTML = '';

  if (savedPhotos.length === 0) {
    albumGrid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:30px 10px;color:var(--text2);font-size:12px;">
        <div style="font-size:36px;margin-bottom:8px;">📷</div>
        Chưa có ảnh nào.<br>Hãy chụp kỷ niệm đầu tiên!
      </div>`;
    const countEl = document.getElementById('profilePhotoCount');
    if (countEl) countEl.textContent = 0;
    return;
  }

  const albums = groupPhotosByAlbum();
  const keys = Object.keys(albums);

  keys.forEach(key => {
    const album = albums[key];
    const photos = album.photos;
    const count = photos.length;
    const card = document.createElement('div');
    card.className = 'album-card';

    const getSrc = (entry) => (typeof entry.data === 'object') ? entry.data.src : entry.data;
    let stackHTML = '';

    if (count >= 3) {
      stackHTML = `
        <img class="album-stack-img stack-back" src="${getSrc(photos[0])}" alt="">
        <img class="album-stack-img stack-mid" src="${getSrc(photos[1])}" alt="">
        <img class="album-stack-img stack-front" src="${getSrc(photos[count - 1])}" alt="">`;
    } else if (count === 2) {
      stackHTML = `
        <img class="album-stack-img stack-mid" src="${getSrc(photos[0])}" alt="">
        <img class="album-stack-img stack-front" src="${getSrc(photos[1])}" alt="">`;
    } else {
      stackHTML = `
        <img class="album-stack-img stack-front" src="${getSrc(photos[0])}" alt="">`;
    }

    card.innerHTML = `
      <div class="album-stack">
        ${stackHTML}
        <div class="album-count-badge">${count} ảnh</div>
      </div>
      <div class="album-info">
        <div class="album-name" title="${album.location}">${album.location}</div>
        <div class="album-date">${album.date}</div>
      </div>`;

    card.onclick = () => openAlbumDetail(key);
    albumGrid.appendChild(card);
  });

  const countEl = document.getElementById('profilePhotoCount');
  if (countEl) countEl.textContent = savedPhotos.length;
}

// Mở chi tiết Album — hiển thị tất cả ảnh bên trong (có swipe context)
function openAlbumDetail(albumKey) {
  const albums = groupPhotosByAlbum();
  const album = albums[albumKey];
  if (!album) return;

  document.getElementById('albumDetailTitle').textContent = album.location;
  document.getElementById('albumDetailSub').textContent = album.date + ' · ' + album.photos.length + ' ảnh';

  // Lưu ảnh theo thứ tự hiển thị (mới nhất trước) cho swipe navigation
  const displayPhotos = [...album.photos].reverse();
  lightboxAlbumPhotos = displayPhotos;

  const grid = document.getElementById('albumDetailGrid');
  grid.innerHTML = '';

  displayPhotos.forEach((entry, displayIdx) => {
    const photo = entry.data;
    const thumb = document.createElement('div');
    thumb.className = 'photo-thumb';
    const imgSrc = (typeof photo === 'object') ? photo.src : photo;
    thumb.innerHTML = '<img src="' + imgSrc + '" alt="Kỷ niệm">';
    thumb.onclick = function() { openLightboxAt(displayIdx); };
    grid.appendChild(thumb);
  });

  document.getElementById('albumDetailLayer').classList.add('active');
}

function closeAlbumDetail() {
  const el = document.getElementById('albumDetailLayer');
  if (el) el.classList.remove('active');
}

// Mở lightbox tại vị trí chỉ định trong album (có điều hướng swipe)
function openLightboxAt(displayIdx) {
  lightboxCurrentIdx = displayIdx;
  showCurrentLightboxPhoto();
  document.getElementById('lightboxLayer').classList.add('active');
}

// Hiển thị ảnh hiện tại + cập nhật metadata và nút điều hướng
function showCurrentLightboxPhoto(direction) {
  const entry = lightboxAlbumPhotos[lightboxCurrentIdx];
  if (!entry) return;
  const photo = entry.data;

  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxLoc = document.getElementById('lightboxLoc');
  const lightboxDate = document.getElementById('lightboxDate');
  const deleteBtn = document.getElementById('lightboxDeleteBtn');
  const imgBox = document.getElementById('lightboxImgBox');

  // Hiệu ứng slide animation khi chuyển ảnh
  if (direction && imgBox) {
    const cls = direction === 'left' ? 'slide-left' : 'slide-right';
    imgBox.classList.remove('slide-left', 'slide-right');
    void imgBox.offsetWidth;
    imgBox.classList.add(cls);
    setTimeout(() => imgBox.classList.remove(cls), 220);
  }

  if (typeof photo === 'object') {
    lightboxImg.src = photo.src;
    lightboxLoc.innerHTML = '<i class="ti ti-map-pin"></i> ' + (photo.location || 'Đang xác định...');
    lightboxDate.innerHTML = '<i class="ti ti-calendar"></i> ' + (photo.date || 'Không rõ thời gian');
  } else {
    lightboxImg.src = photo;
    lightboxLoc.innerHTML = '<i class="ti ti-map-pin"></i> Kỷ niệm chuyến đi';
    lightboxDate.innerHTML = '<i class="ti ti-calendar"></i> Trước đây';
  }

  deleteBtn.onclick = function() {
    if (confirm('Bạn có chắc chắn muốn xóa bức ảnh kỷ niệm này khỏi hệ thống?')) {
      deletePhoto(entry.originalIndex);
    }
  };

  updateLightboxNav();
}

// Cập nhật counter + nút prev/next dựa vào vị trí hiện tại
function updateLightboxNav() {
  const total = lightboxAlbumPhotos.length;
  const counter = document.getElementById('lightboxCounter');
  const prevBtn = document.getElementById('lightboxPrev');
  const nextBtn = document.getElementById('lightboxNext');

  if (total > 1) {
    counter.textContent = (lightboxCurrentIdx + 1) + ' / ' + total;
    counter.classList.add('visible');
    prevBtn.classList.toggle('visible', lightboxCurrentIdx > 0);
    nextBtn.classList.toggle('visible', lightboxCurrentIdx < total - 1);
  } else {
    counter.classList.remove('visible');
    prevBtn.classList.remove('visible');
    nextBtn.classList.remove('visible');
  }
}

function lightboxGoPrev() {
  if (lightboxCurrentIdx > 0) {
    lightboxCurrentIdx--;
    showCurrentLightboxPhoto('right');
  }
}

function lightboxGoNext() {
  if (lightboxCurrentIdx < lightboxAlbumPhotos.length - 1) {
    lightboxCurrentIdx++;
    showCurrentLightboxPhoto('left');
  }
}

// Hàm thực thi xóa ảnh
function deletePhoto(index) {
  savedPhotos.splice(index, 1);
  localStorage.setItem('travel_app_photos', JSON.stringify(savedPhotos));
  renderAlbum();
  closeLightbox();
  closeAlbumDetail();
}

function closeLightbox() {
  document.getElementById('lightboxLayer').classList.remove('active');
  var c = document.getElementById('lightboxCounter');
  var p = document.getElementById('lightboxPrev');
  var n = document.getElementById('lightboxNext');
  if (c) c.classList.remove('visible');
  if (p) p.classList.remove('visible');
  if (n) n.classList.remove('visible');
}

// ===== HỖ TRỢ VUỐT TRÊN MOBILE (TOUCH SWIPE) =====
(function() {
  var startX = 0, diffX = 0;
  var layer = document.getElementById('lightboxLayer');
  if (!layer) return;
  layer.addEventListener('touchstart', function(e) {
    startX = e.touches[0].clientX;
    diffX = 0;
  }, { passive: true });
  layer.addEventListener('touchmove', function(e) {
    diffX = e.touches[0].clientX - startX;
  }, { passive: true });
  layer.addEventListener('touchend', function() {
    if (Math.abs(diffX) > 50) {
      if (diffX < 0) lightboxGoNext();
      else lightboxGoPrev();
    }
  });
})();

// ===== HỖ TRỢ PHÍM MŨI TÊN TRÊN DESKTOP =====
document.addEventListener('keydown', function(e) {
  var layer = document.getElementById('lightboxLayer');
  if (!layer || !layer.classList.contains('active')) return;
  if (e.key === 'ArrowLeft') { e.preventDefault(); lightboxGoPrev(); }
  if (e.key === 'ArrowRight') { e.preventDefault(); lightboxGoNext(); }
  if (e.key === 'Escape') { e.preventDefault(); closeLightbox(); }
});

// Khởi chạy đồng bộ album lần đầu tiên
renderAlbum();

// Quản lý khởi động/Tắt luồng camera phần cứng
async function startCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    const video = document.getElementById('webcam');
    if (video) video.srcObject = cameraStream;
  } catch (error) {
    console.error("Lỗi khởi tạo máy ảnh:", error);
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
}

// Thực hiện chụp ảnh kết hợp hiệu ứng chớp sáng Shutter Flash
function takePhoto() {
  const video = document.getElementById('webcam');
  const canvas = document.getElementById('photo-canvas');
  const context = canvas.getContext('2d');
  const flash = document.getElementById('cameraFlash');

  if (video && video.srcObject) {
    // Kích hoạt hiệu ứng flash cơ điện tử mô phỏng
    if (flash) {
      flash.classList.add('active');
      setTimeout(() => flash.classList.remove('active'), 300);
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    latestCapturedPhotoData = canvas.toDataURL('image/png');
    
    document.getElementById('previewImg').src = latestCapturedPhotoData;
    document.getElementById('previewLayer').classList.add('active');
  }
}

// Lưu trữ ảnh nâng cấp có kèm cấu trúc Metadata
function savePhoto() {
  if (latestCapturedPhotoData) {
    // Trích xuất địa danh hiện hành trên khung AI Tag
    const aiTitleEl = document.querySelector('.ai-tag-title');
    const currentLocation = aiTitleEl ? aiTitleEl.textContent.replace('AI nhận diện: ', '') : 'Vịnh Hạ Long, Quảng Ninh';
    
    // Tạo chuỗi thời gian nội địa hoá chuẩn xác
    const now = new Date();
    const formattedDate = `${now.toLocaleDateString('vi-VN')} lúc ${now.toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'})}`;

    // Khởi tạo Object cấu trúc thông tin kỷ niệm mới
    const newPhotoObject = {
      id: Date.now(),
      src: latestCapturedPhotoData,
      location: currentLocation,
      date: formattedDate
    };

    savedPhotos.push(newPhotoObject);
    localStorage.setItem('travel_app_photos', JSON.stringify(savedPhotos));
    
    renderAlbum();
    closePreview();
  }
}

function cancelPhoto() {
  latestCapturedPhotoData = null;
  closePreview();
}

function closePreview() {
  document.getElementById('previewLayer').classList.remove('active');
}

function askAIWithPhoto() {
  if (latestCapturedPhotoData) {
    alert("🤖 AI đang phân tích địa danh từ bức ảnh của bạn...");
    switchScreen('chat');
    addMsg("📸 *[Đã gửi bức ảnh]* Địa danh này là ở đâu vậy TravelBot?", "user");
    setTimeout(() => {
      addMsg("🤖 Hệ thống AI nhận diện hình ảnh của bạn rất giống với **Vịnh Hạ Long**! Bạn có muốn tôi gợi ý các tour du thuyền không?", "bot");
    }, 1200);
    closePreview();
  }
}

// ===== TÍNH NĂNG PHÂN TÍCH ẢNH BẰNG GOOGLE SEARCH IMAGE =====
// Chuyển đổi Data URL (base64) sang đối tượng Blob để gửi qua form
function dataURLtoBlob(dataURL) {
  const parts = dataURL.split(',');
  const mime = parts[0].match(/:(.*?);/)[1];
  const bstr = atob(parts[1]);
  const u8arr = new Uint8Array(bstr.length);
  for (let i = 0; i < bstr.length; i++) u8arr[i] = bstr.charCodeAt(i);
  return new Blob([u8arr], { type: mime });
}

// Hàm lõi: POST ảnh lên Google Lens để phân tích nội dung hình ảnh
function searchGoogleWithImage(imageDataUrl) {
  try {
    const blob = dataURLtoBlob(imageDataUrl);

    // Tạo form ẩn để POST ảnh lên Google Lens
    const form = document.createElement('form');
    form.method = 'POST';
    form.enctype = 'multipart/form-data';
    form.action = 'https://lens.google.com/v3/upload';
    form.target = '_blank';
    form.style.display = 'none';

    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.name = 'encoded_image';

    // Gán file ảnh vào input thông qua DataTransfer API
    const dt = new DataTransfer();
    dt.items.add(new File([blob], 'captured_photo.png', { type: blob.type }));
    fileInput.files = dt.files;

    form.appendChild(fileInput);
    document.body.appendChild(form);
    form.submit();

    // Dọn dẹp form sau khi đã gửi
    setTimeout(() => document.body.removeChild(form), 2000);
  } catch(err) {
    console.error('Lỗi Google Search:', err);
    // Dự phòng: mở Google Lens trang chủ để tải ảnh thủ công
    window.open('https://lens.google.com/', '_blank');
  }
}

// Phân tích ảnh vừa chụp (từ màn hình Preview)
function searchGoogleWithPhoto() {
  if (latestCapturedPhotoData) {
    searchGoogleWithImage(latestCapturedPhotoData);
  }
}

// Phân tích ảnh đã lưu (từ Lightbox xem chi tiết album)
function searchGoogleLightbox() {
  const img = document.getElementById('lightboxImg');
  if (img && img.src && img.src.startsWith('data:')) {
    searchGoogleWithImage(img.src);
  }
}

// LOGIC ĐIỀU HƯỚNG TAB CHUNG
function switchScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => {
    b.classList.remove('active');
    const dot = b.querySelector('.nav-dot');
    if (dot) dot.remove();
  });
  
  document.getElementById('screen-' + name).classList.add('active');
  const btn = document.getElementById('nav-' + name);
  btn.classList.add('active');
  
  const dot = document.createElement('div');
  dot.className = 'nav-dot';
  btn.appendChild(dot);

  if (name === 'camera') {
    startCamera();
    renderAlbum();
  } else {
    stopCamera();
    closePreview();
    closeLightbox();
    closeAlbumDetail();
  }
}

// LOGIC CHATBOT
function sendMsg() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;
  addMsg(text, 'user');
  input.value = '';
  setTimeout(() => {
    addMsg('Câu hỏi hay đó! 😊 Hãy cung cấp thêm thông tin số ngày đi để tôi tư vấn rõ hơn nhé.', 'bot');
  }, 700);
}

function addMsg(text, type) {
  const body = document.getElementById('chatBody');
  const div = document.createElement('div');
  div.className = 'msg ' + type;
  div.innerHTML = type === 'bot'
    ? `<div class="msg-avatar">🤖</div><div class="msg-bubble">${text}</div>`
    : `<div class="msg-bubble">${text}</div>`;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
}
</script>
</body>
</html>
