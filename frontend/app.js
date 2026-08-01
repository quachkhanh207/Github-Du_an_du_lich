/* ==========================================================================
   TripWise AI - Master Ecosystem Application Logic (app.js)
   ========================================================================== */

// Global State
let currentDestination = "danang";
let activeDay = 1;
let leafletMap = null;
let leafletMarkers = [];
let leafletPolyline = null;
let savedTripsCount = 4;
let savedPhotosCount = 38;

// Comprehensive Mock Travel Database for 5 Destinations
const DESTINATIONS_DB = {
    danang: {
        title: "Lịch Trình Chi Tiết • Đà Nẵng & Hội An",
        subtitle: "AI đã tối ưu hóa quãng đường di chuyển và thời điểm tham quan đẹp nhất.",
        weather: { icon: "☀️", temp: "29°C", desc: "Đà Nẵng • Nắng ráo, biển êm, sóng nhẹ" },
        cost: "2.850.000 VNĐ / người",
        costDetails: "Khách sạn: 1.200k • Ăn uống: 950k • Vé & Xe: 700k",
        center: [16.068, 108.230],
        days: [
            {
                dayNum: 1,
                title: "Khám phá Trung Tâm Đà Nẵng & Biển Mỹ Khê",
                subtitle: "4 địa điểm • Quãng đường di chuyển ~15 km",
                activities: [
                    { time: "08:00", title: "Ăn sáng Mì Quảng Bà Mua", desc: "Thưởng thức Mì Quảng ếch & tôm thịt đặc sản số 95 Nguyễn Chí Thanh.", lat: 16.068, lng: 108.222, img: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=300&q=80" },
                    { time: "10:00", title: "Tham quan Cầu Rồng & Cầu Tình Yêu", desc: "Check-in tượng Cá Chép Hóa Rồng và ngắm bờ sông Hàn thơ mộng.", lat: 16.061, lng: 108.227, img: "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=300&q=80" },
                    { time: "15:30", title: "Tắm biển & Dạo bờ biển Mỹ Khê", desc: "Top bãi biển quyến rũ nhất hành tinh. Thưởng thức dừa tươi bãi biển.", lat: 16.054, lng: 108.247, img: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=300&q=80" }
                ]
            },
            {
                dayNum: 2,
                title: "Chùa Linh Ứng Bán Đảo Sơn Trà & Sun World Bà Nà Hills",
                subtitle: "3 địa điểm • Quãng đường di chuyển ~32 km",
                activities: [
                    { time: "08:00", title: "Chùa Linh Ứng Sơn Trà", desc: "Chiêm bái Phật Quan Thế Âm cao 67m ngắm toàn cảnh vịnh Đà Nẵng.", lat: 16.100, lng: 108.277, img: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=300&q=80" },
                    { time: "11:00", title: "Sun World Bà Nà Hills & Cầu Vàng", desc: "Đi cáp treo đạt kỷ lục thế giới, check-in Cầu Vàng nổi tiếng và Làng Pháp.", lat: 15.996, lng: 107.986, img: "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=300&q=80" }
                ]
            },
            {
                dayNum: 3,
                title: "Phố Cổ Hội An & Mua Sắm Đặc Sản",
                subtitle: "3 địa điểm • Quãng đường di chuyển ~28 km",
                activities: [
                    { time: "14:30", title: "Tản bộ Phố Cổ Hội An & Chùa Cầu", desc: "Ngắm lồng đèn phố cổ, thả hoa đăng sông Hoài và ăn Cao Lầu.", lat: 15.877, lng: 108.326, img: "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=300&q=80" }
                ]
            }
        ]
    },
    phuquoc: {
        title: "Lịch Trình Chi Tiết • Phú Quốc Đảo Ngọc (4N3Đ)",
        subtitle: "Lịch trình nghỉ dưỡng biển đảo cao cấp kết hợp vui chơi giải trí không ngủ.",
        weather: { icon: "🌤️", temp: "31°C", desc: "Phú Quốc • Biển trong xanh, nắng rực rỡ" },
        cost: "4.500.000 VNĐ / người",
        costDetails: "Khách sạn 4*: 2.200k • Hải sản: 1.300k • Vé VinWonders: 1.000k",
        center: [10.224, 103.958],
        days: [
            {
                dayNum: 1,
                title: "Check-in Resort & Hoàng Hôn Sunset Sanato",
                subtitle: "3 địa điểm • Quãng đường di chuyển ~12 km",
                activities: [
                    { time: "14:00", title: "Nhận phòng Resort Dương Đông", desc: "Nghỉ ngơi và thư giãn bên bể bơi hướng biển.", lat: 10.217, lng: 103.959, img: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=300&q=80" },
                    { time: "17:00", title: "Ngắm hoàng hôn Sunset Sanato Beach", desc: "Chụp ảnh cùng các tượng voi chân dài biểu tượng hoàng hôn Phú Quốc.", lat: 10.180, lng: 103.966, img: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=300&q=80" }
                ]
            }
        ]
    },
    sapa: {
        title: "Lịch Trình Chi Tiết • Sa Pa - Fansipan Săn Mây (3N2Đ)",
        subtitle: "Khám phá bản làng H'Mông và chinh phục Nóc nhà Đông Dương.",
        weather: { icon: "🌫️", temp: "16°C", desc: "Sa Pa • Se lạnh, sương mù nhẹ về đêm" },
        cost: "3.200.000 VNĐ / người",
        costDetails: "Homestay view thung lũng: 1.100k • Vé Fansipan: 850k • Lẩu thắng cố: 1.250k",
        center: [22.336, 103.843],
        days: [
            {
                dayNum: 1,
                title: "Check-in Thị Trấn Sa Pa & Bản Cát Cát",
                subtitle: "3 địa điểm • Quãng đường ~8 km",
                activities: [
                    { time: "09:00", title: "Nhà Thờ Đá & Nhà Sàn Sa Pa", desc: "Check-in biểu tượng kiến trúc Pháp cổ trung tâm thị trấn.", lat: 22.334, lng: 103.841, img: "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=300&q=80" }
                ]
            }
        ]
    },
    hanoi: {
        title: "Lịch Trình Chi Tiết • Hà Nội Food Tour 36 Phố Phường (2N1Đ)",
        subtitle: "Thưởng thức các món ngon truyền thống và khám phá nghìn năm văn hiến.",
        weather: { icon: "⛅", temp: "26°C", desc: "Hà Nội • Thời tiết mùa thu mát mẻ" },
        cost: "1.800.000 VNĐ / người",
        costDetails: "Khách sạn Phố Cổ: 800k • Foodtour 10 món: 600k • Vé tham quan: 400k",
        center: [21.028, 105.852],
        days: [
            {
                dayNum: 1,
                title: "Foodtour Phố Cổ & Hồ Hoàn Kiếm",
                subtitle: "5 món ngon • Quãng đường di chuyển tản bộ ~5 km",
                activities: [
                    { time: "08:00", title: "Phở Thìn Lò Đúc / Bờ Hồ", desc: "Thưởng thức bát phở tái lăn béo ngậy thơm nức tiếng Hà Thành.", lat: 21.028, lng: 105.854, img: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=300&q=80" }
                ]
            }
        ]
    },
    dalat: {
        title: "Lịch Trình Chi Tiết • Đà Lạt Mộng Mơ & Cà Phê Săn Mây (3N2Đ)",
        subtitle: "Nghỉ dưỡng thung lũng ngàn hoa, check-in đồi chè và quán cà phê view đẹp.",
        weather: { icon: "🌲", temp: "18°C", desc: "Đà Lạt • Nắng dịu, không khí trong lành" },
        cost: "2.900.000 VNĐ / người",
        costDetails: "Villa Homestay: 1.200k • Cà phê & Ăn uống: 1.100k • Xe máy: 600k",
        center: [11.940, 108.458],
        days: [
            {
                dayNum: 1,
                title: "Quảng Trường Lâm Viên & Chợ Đêm Đà Lạt",
                subtitle: "3 địa điểm • Quãng đường di chuyển ~6 km",
                activities: [
                    { time: "15:00", title: "Check-in Nụ Hoa Atiso Quảng Trường", desc: "Chụp ảnh cùng biểu tượng hoa Dã Quỳ và nụ hoa Atiso khổng lồ.", lat: 11.936, lng: 108.444, img: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=300&q=80" }
                ]
            }
        ]
    }
};

/* Checklist Rule Engine Datasets */
const CHECKLIST_DB = {
    sunny: [
        { text: "Kem chống nắng SPF 50+ & Xịt khoáng", checked: true },
        { text: "Kính mát chống tia UV & Mũ rộng vành", checked: true },
        { text: "Đồ bơi & Khăn tắm biển", checked: false },
        { text: "Dép đi biển chống trượt & Túi cót", checked: false }
    ],
    cold: [
        { text: "Áo khoác giữ nhiệt / Áo phao siêu nhẹ", checked: true },
        { text: "Khăn quàng cổ, găng tay & Miếng dán giữ nhiệt", checked: true },
        { text: "Kem dưỡng ẩm da & Son dưỡng môi", checked: false },
        { text: "Giày thể thao leo núi cổ cao", checked: false }
    ],
    rain: [
        { text: "Áo mưa bộ tiện lợi & Ô/Dù gấp gọn", checked: true },
        { text: "Bọc giày chống nước & Túi chống ẩm tech", checked: true },
        { text: "Quần áo mau khô & Khăn lau nhanh", checked: false }
    ],
    plane: [
        { text: "CCCD / Hộ chiếu bản gốc còn hạn", checked: true },
        { text: "Vé máy bay điện tử (Mobile Boarding Pass)", checked: true },
        { text: "Xác nhận đặt phòng khách sạn & Tour", checked: true },
        { text: "Bằng lái xe & Bảo hiểm du lịch", checked: false }
    ],
    motorbike: [
        { text: "Bằng lái xe máy & Giấy tờ xe gốc", checked: true },
        { text: "Mũ bảo hiểm đạt chuẩn & Giáp bảo vệ", checked: true },
        { text: "Túi bọc balo chống nước & Dây chằng", checked: false }
    ],
    car: [
        { text: "Gối cổ cao su non & Chăn mỏng", checked: true },
        { text: "Thuốc say xe & Nước uống đóng chai", checked: true }
    ]
};

/* ==========================================================================
   BEENAVI AI CHATBOT — Kết nối WebSocket thật tới FastAPI backend (/ws)
   Nhắm đúng vào khung chat #cbPanel đã có sẵn trong index.html
   ========================================================================== */
let cbSocket = null;
let cbReconnectTimer = null;
let cbCurrentBotBubble = null;   // bubble đang stream câu trả lời (text chat)
let cbCurrentCallBubble = null;  // bubble đang stream câu trả lời (đàm thoại)
let cbMediaRecorder = null;
let cbMicStream = null;
let cbIsCallActive = false;
let cbCallStopTimer = null;

function cbConnectWS() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    cbSocket = new WebSocket(wsUrl);

    cbSocket.onopen = () => {
        clearTimeout(cbReconnectTimer);
    };

    cbSocket.onclose = () => {
        clearTimeout(cbReconnectTimer);
        cbReconnectTimer = setTimeout(cbConnectWS, 2000);
    };

    cbSocket.onerror = () => {
        cbSocket.close();
    };

    cbSocket.onmessage = (event) => {
        let payload;
        try {
            payload = JSON.parse(event.data);
        } catch (e) {
            return;
        }
        cbHandleServerMessage(payload);
    };
}

function cbEnsureConnected() {
    if (cbSocket && cbSocket.readyState === WebSocket.OPEN) return true;
    showToast("⚠️ Đang kết nối lại tới máy chủ AI...");
    cbConnectWS();
    return false;
}

function cbHandleServerMessage(payload) {
    switch (payload.type) {
        case "partial_transcript": {
            const box = document.getElementById("cbVoiceTranscript");
            if (cbIsCallActive && box) box.textContent = payload.text;
            break;
        }

        case "transcript": {
            if (cbIsCallActive) {
                const box = document.getElementById("cbVoiceTranscript");
                if (box) box.textContent = payload.text;
                const status = document.getElementById("cbVoiceStatus");
                if (status) status.textContent = "Beenavi AI đang trả lời...";
            } else {
                cbAddMessage("user", payload.text);
                cbShowTyping();
            }
            break;
        }

        case "stt_empty":
            if (cbIsCallActive) {
                const status = document.getElementById("cbVoiceStatus");
                if (status) status.textContent = "Không nghe rõ, mời bạn nói lại...";
            } else {
                showToast("🎙️ Không nhận diện được giọng nói, vui lòng thử lại.");
            }
            break;

        case "answer": {
            // Server gửi toàn bộ câu trả lời tích lũy mỗi lần (không phải delta)
            if (cbIsCallActive) {
                const status = document.getElementById("cbVoiceStatus");
                cbCurrentCallBubble = payload.text;
                if (status) status.textContent = "Beenavi AI đang trả lời...";
            } else {
                cbHideTyping();
                if (!cbCurrentBotBubble) {
                    cbCurrentBotBubble = cbAddMessage("bot", payload.text);
                } else {
                    cbCurrentBotBubble.querySelector("p").textContent = payload.text;
                    cbScrollToBottom();
                }
            }
            break;
        }

        case "done":
            if (cbIsCallActive) {
                cbSpeakText(cbCurrentCallBubble);
                cbCurrentCallBubble = null;
            } else {
                cbCurrentBotBubble = null;
                cbHideTyping();
            }
            break;

        case "error":
            cbHideTyping();
            cbCurrentBotBubble = null;
            showToast(`⚠️ Lỗi: ${payload.message || "Không thể xử lý yêu cầu"}`);
            break;

        default:
            break;
    }
}

/* --- Mở/đóng khung chat --- */
window.cbToggle = function () {
    const panel = document.getElementById("cbPanel");
    if (!panel) return;
    panel.classList.toggle("cb-open");
    if (panel.classList.contains("cb-open")) {
        cbEnsureConnected();
        cbScrollToBottom();
    }
};

window.cbOpen = function () {
    const panel = document.getElementById("cbPanel");
    if (!panel) return;
    if (!panel.classList.contains("cb-open")) {
        panel.classList.add("cb-open");
    }
    cbEnsureConnected();
    cbScrollToBottom();
};

// Gửi tin nhắn bằng code (VD: từ thanh tìm kiếm hero) thay vì đọc từ ô input
window.cbSendProgrammaticText = function (text) {
    text = (text || "").trim();
    if (!text) return;

    cbAddMessage("user", text);
    cbCurrentBotBubble = null;
    cbShowTyping();

    if (!cbEnsureConnected()) return;
    cbSocket.send(JSON.stringify({ type: "text", text }));
};

window.cbScrollToBottom = function () {
    const body = document.getElementById("cbBody");
    if (body) body.scrollTop = body.scrollHeight;
};

function cbShowTyping() {
    const typing = document.getElementById("cbTyping");
    if (typing) typing.style.display = "block";
    cbScrollToBottom();
}

function cbHideTyping() {
    const typing = document.getElementById("cbTyping");
    if (typing) typing.style.display = "none";
}

function cbAddMessage(role, text) {
    const body = document.getElementById("cbBody");
    if (!body) return null;

    const msgDiv = document.createElement("div");
    msgDiv.className = `cb-msg ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "cb-bubble";

    const p = document.createElement("p");
    p.textContent = text;
    bubble.appendChild(p);

    msgDiv.appendChild(bubble);
    body.appendChild(msgDiv);
    cbScrollToBottom();

    return bubble;
}

/* --- Gửi tin nhắn văn bản --- */
window.cbSendText = function () {
    const input = document.getElementById("cbInput");
    if (!input) return;

    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    cbSendProgrammaticText(text);
};

/* --- Ghi âm 1 lần (nút Micro) --- */
window.cbToggleMic = function () {
    const micBtn = document.getElementById("cbMicBtn");

    if (cbMediaRecorder && cbMediaRecorder.state === "recording") {
        cbMediaRecorder.stop();
        return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showToast("🎙️ Trình duyệt không hỗ trợ ghi âm.");
        return;
    }
    if (!cbEnsureConnected()) return;

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then((stream) => {
            cbMicStream = stream;
            cbMediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

            if (micBtn) micBtn.classList.add("cb-recording");
            showToast("🎙️ Đang lắng nghe giọng nói của bạn...");
            cbSocket.send(JSON.stringify({ type: "audio_start" }));

            cbMediaRecorder.ondataavailable = async (e) => {
                if (e.data.size === 0) return;
                const buffer = await e.data.arrayBuffer();
                const base64 = cbBufferToBase64(buffer);
                if (cbSocket && cbSocket.readyState === WebSocket.OPEN) {
                    cbSocket.send(JSON.stringify({ type: "audio_chunk", data: base64 }));
                }
            };

            cbMediaRecorder.onstop = () => {
                if (micBtn) micBtn.classList.remove("cb-recording");
                cbSocket.send(JSON.stringify({ type: "audio_end" }));
                if (cbMicStream) {
                    cbMicStream.getTracks().forEach((t) => t.stop());
                    cbMicStream = null;
                }
            };

            cbMediaRecorder.start(250);

            // Tự dừng sau 15s để tránh ghi âm quá dài
            setTimeout(() => {
                if (cbMediaRecorder && cbMediaRecorder.state === "recording") {
                    cbMediaRecorder.stop();
                }
            }, 15000);
        })
        .catch((err) => {
            console.warn("Không truy cập được microphone:", err);
            showToast("🎙️ Vui lòng cấp quyền truy cập microphone để dùng giọng nói.");
        });
};

function cbBufferToBase64(buffer) {
    let binary = "";
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    return btoa(binary);
}

/* --- Đàm thoại trực tiếp (ghi âm liên tục theo từng lượt) --- */
window.cbToggleVoiceCall = function () {
    const overlay = document.getElementById("cbVoiceOverlay");
    if (!overlay) return;
    if (!cbEnsureConnected()) return;

    cbIsCallActive = true;
    overlay.classList.add("cb-voice-active");
    const status = document.getElementById("cbVoiceStatus");
    if (status) status.textContent = "Đang lắng nghe...";
    const transcript = document.getElementById("cbVoiceTranscript");
    if (transcript) transcript.textContent = "";

    cbStartCallTurn();
};

window.cbStopVoiceCall = function () {
    const overlay = document.getElementById("cbVoiceOverlay");
    cbIsCallActive = false;
    clearTimeout(cbCallStopTimer);
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (cbMediaRecorder && cbMediaRecorder.state === "recording") {
        cbMediaRecorder.stop();
    }
    if (overlay) overlay.classList.remove("cb-voice-active");
};

function cbStartCallTurn() {
    if (!cbIsCallActive) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showToast("🎙️ Trình duyệt không hỗ trợ ghi âm.");
        cbStopVoiceCall();
        return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then((stream) => {
            cbMicStream = stream;
            cbMediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            cbSocket.send(JSON.stringify({ type: "audio_start" }));

            cbMediaRecorder.ondataavailable = async (e) => {
                if (e.data.size === 0) return;
                const buffer = await e.data.arrayBuffer();
                const base64 = cbBufferToBase64(buffer);
                if (cbSocket && cbSocket.readyState === WebSocket.OPEN) {
                    cbSocket.send(JSON.stringify({ type: "audio_chunk", data: base64 }));
                }
            };

            cbMediaRecorder.onstop = () => {
                cbSocket.send(JSON.stringify({ type: "audio_end" }));
                if (cbMicStream) {
                    cbMicStream.getTracks().forEach((t) => t.stop());
                    cbMicStream = null;
                }
            };

            cbMediaRecorder.start(250);

            // Mỗi lượt nói tối đa 8s, sau đó tự gửi và chờ AI trả lời
            cbCallStopTimer = setTimeout(() => {
                if (cbMediaRecorder && cbMediaRecorder.state === "recording") {
                    cbMediaRecorder.stop();
                }
            }, 8000);
        })
        .catch((err) => {
            console.warn("Không truy cập được microphone:", err);
            showToast("🎙️ Vui lòng cấp quyền truy cập microphone để dùng đàm thoại.");
            cbStopVoiceCall();
        });
}

function cbSpeakText(text) {
    if (!text || !cbIsCallActive) {
        if (cbIsCallActive) cbStartCallTurn();
        return;
    }
    if (!("speechSynthesis" in window)) {
        cbStartCallTurn();
        return;
    }

    const overlay = document.getElementById("cbVoiceOverlay");
    const status = document.getElementById("cbVoiceStatus");
    if (overlay) overlay.classList.add("cb-speaking");
    if (status) status.textContent = "Beenavi AI đang nói...";

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "vi-VN";
    utter.onend = () => {
        if (overlay) overlay.classList.remove("cb-speaking");
        if (!cbIsCallActive) return;
        const s = document.getElementById("cbVoiceStatus");
        if (s) s.textContent = "Đang lắng nghe...";
        cbStartCallTurn();
    };
    window.speechSynthesis.speak(utter);
}

/* --- Chụp ảnh / đăng ảnh ---
   LƯU Ý: backend hiện chưa có endpoint AI Vision phân tích ảnh
   (chỉ có /chat, /transcribe, /ws xử lý text + giọng nói).
   Ảnh sẽ hiển thị trong khung chat, nhưng để AI phân tích được nội
   dung ảnh, cần bổ sung endpoint Vision riêng ở backend trước. */
window.cbOpenCamera = function () {
    const modal = document.getElementById("cbCameraModal");
    const video = document.getElementById("cbVideoStream");
    if (!modal || !video) return;

    modal.style.display = "flex";
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
            .then((stream) => {
                cbCameraStream = stream;
                video.srcObject = stream;
            })
            .catch(() => showToast("📷 Vui lòng cấp quyền truy cập máy ảnh."));
    }
};

let cbCameraStream = null;

window.cbCloseCamera = function () {
    const modal = document.getElementById("cbCameraModal");
    const video = document.getElementById("cbVideoStream");
    if (modal) modal.style.display = "none";
    if (cbCameraStream) {
        cbCameraStream.getTracks().forEach((t) => t.stop());
        cbCameraStream = null;
    }
    if (video) video.srcObject = null;
};

window.cbCapturePhoto = function () {
    const video = document.getElementById("cbVideoStream");
    const canvas = document.getElementById("cbCaptureCanvas");
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    const imgData = canvas.toDataURL("image/jpeg");

    cbCloseCamera();
    cbAddImageMessage(imgData);
};

window.cbHandleImageUpload = function (event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => cbAddImageMessage(e.target.result);
    reader.readAsDataURL(file);
    event.target.value = "";
};

function cbAddImageMessage(imgDataUrl) {
    const body = document.getElementById("cbBody");
    if (!body) return;

    const msgDiv = document.createElement("div");
    msgDiv.className = "cb-msg user";
    const bubble = document.createElement("div");
    bubble.className = "cb-bubble";
    bubble.innerHTML = `<img src="${imgDataUrl}" style="max-width:100%;border-radius:8px;display:block;margin-bottom:6px;">`;
    msgDiv.appendChild(bubble);
    body.appendChild(msgDiv);

    cbAddMessage("bot", "Mình đã nhận được ảnh! Hiện backend chưa có tính năng AI Vision phân tích ảnh — bạn mô tả giúp mình bằng lời để tư vấn chính xác hơn nhé.");
    cbScrollToBottom();
}

// Application Initialization
document.addEventListener("DOMContentLoaded", () => {
    initLeafletMap();
    renderItineraryForDestination("danang");
    initChecklistEvents();
    initHeroEvents();
    initChatDrawerEvents();
    cbConnectWS();
});

window.selectInspirationDestination = function (destKey) {
    const destSelect = document.getElementById("prefDestinationSelect");
    if (destSelect) destSelect.value = destKey;

    const itSection = document.getElementById("itinerarySection");
    if (itSection) itSection.scrollIntoView({ behavior: "smooth" });

    showSkeletonAndRender(destKey);
};

/* Clone Community Trip Action */
window.cloneCommunityTrip = function (destKey, tripTitle) {
    showToast(`🚀 Đã Clone & Nhân bản thành công lịch trình: "${tripTitle}"`);
    
    const itSection = document.getElementById("itinerarySection");
    if (itSection) itSection.scrollIntoView({ behavior: "smooth" });

    showSkeletonAndRender(destKey);
    openDrawerWithPrompt(`Tôi vừa nhân bản (Clone) lịch trình cộng đồng: "${tripTitle}". Hãy giúp tôi tùy chỉnh tối ưu thêm dựa trên sở thích cá nhân của tôi!`);
};


/* ==========================================================================
   MODULE 1: ITINERARY GENERATOR & LEAFLET MAP
   ========================================================================== */
function initLeafletMap() {
    const mapEl = document.getElementById("leafletMap");
    if (!mapEl) return;

    leafletMap = L.map('leafletMap').setView([16.068, 108.230], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(leafletMap);
}

function renderItineraryForDestination(destKey) {
    currentDestination = destKey;
    const destData = DESTINATIONS_DB[destKey] || DESTINATIONS_DB["danang"];

    const titleEl = document.getElementById("itinerarySectionTitle");
    const subTitleEl = document.getElementById("itinerarySectionSubtitle");
    const weatherIcon = document.getElementById("weatherIcon");
    const weatherTemp = document.getElementById("weatherTemp");
    const weatherDesc = document.getElementById("weatherDesc");
    const costAmount = document.getElementById("costAmountText");
    const costDetails = document.getElementById("costDetailsText");

    if (titleEl) titleEl.textContent = destData.title;
    if (subTitleEl) subTitleEl.textContent = destData.subtitle;
    if (weatherIcon) weatherIcon.textContent = destData.weather.icon;
    if (weatherTemp) weatherTemp.textContent = destData.weather.temp;
    if (weatherDesc) weatherDesc.textContent = destData.weather.desc;
    if (costAmount) costAmount.textContent = destData.cost;
    if (costDetails) costDetails.textContent = destData.costDetails;

    const container = document.getElementById("timelineAccordionContainer");
    if (!container) return;

    let html = "";
    destData.days.forEach((day, idx) => {
        const isActive = idx === 0 ? "active" : "";
        html += `
            <div class="day-accordion ${isActive}" data-day="${day.dayNum}">
                <div class="day-header" onclick="toggleAccordion(this)">
                    <div class="day-title-group">
                        <div class="day-badge">Ngày ${day.dayNum}</div>
                        <div class="day-info">
                            <h3>${day.title}</h3>
                            <p>${day.subtitle}</p>
                        </div>
                    </div>
                    <div class="accordion-toggle-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    </div>
                </div>
                <div class="day-body">
                    <div class="activities-list">
                        ${day.activities.map(act => `
                            <div class="activity-card" onclick="focusMapLocation(${act.lat}, ${act.lng}, '${act.title}')">
                                <div class="activity-time"><span class="time-badge">${act.time}</span></div>
                                <div class="activity-icon-box">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                                </div>
                                <div class="activity-content">
                                    <div class="activity-title">
                                        ${act.title}
                                        <span class="location-tag">📍 Xem vị trí</span>
                                    </div>
                                    <p class="activity-desc">${act.desc}</p>
                                </div>
                                <img src="${act.img}" class="activity-img" alt="${act.title}">
                            </div>
                        `).join("")}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    updateMapForDestination(destData);
}

function updateMapForDestination(destData) {
    if (!leafletMap) return;

    leafletMarkers.forEach(m => leafletMap.removeLayer(m));
    leafletMarkers = [];
    if (leafletPolyline) leafletMap.removeLayer(leafletPolyline);

    leafletMap.flyTo(destData.center, 12, { duration: 1.2 });

    const polylineCoords = [];
    destData.days.forEach(day => {
        day.activities.forEach(act => {
            const marker = L.marker([act.lat, act.lng]).addTo(leafletMap)
                .bindPopup(`<b>${act.title}</b><br>${act.desc}`);
            leafletMarkers.push(marker);
            polylineCoords.push([act.lat, act.lng]);
        });
    });

    if (polylineCoords.length > 1) {
        leafletPolyline = L.polyline(polylineCoords, {
            color: '#0194F3',
            weight: 4,
            opacity: 0.8,
            dashArray: '8, 8'
        }).addTo(leafletMap);
    }
}

window.toggleAccordion = function (headerEl) {
    const acc = headerEl.closest(".day-accordion");
    const isActive = acc.classList.contains("active");
    document.querySelectorAll(".day-accordion").forEach(a => a.classList.remove("active"));
    if (!isActive) {
        acc.classList.add("active");
        const dayNum = acc.getAttribute("data-day");
        const label = document.getElementById("activeMapDayLabel");
        if (label) label.textContent = `Ngày ${dayNum}`;
    }
};

window.focusMapLocation = function (lat, lng, title) {
    if (leafletMap) {
        leafletMap.flyTo([lat, lng], 14, { duration: 1 });
        L.popup()
            .setLatLng([lat, lng])
            .setContent(`<b>${title}</b>`)
            .openOn(leafletMap);
    }
};

window.applyPreferenceFilter = function () {
    const destSelect = document.getElementById("prefDestinationSelect");
    if (destSelect) {
        const key = destSelect.value;
        showSkeletonAndRender(key);
    }
};

function showSkeletonAndRender(destKey) {
    const container = document.getElementById("timelineAccordionContainer");
    if (container) {
        container.innerHTML = `
            <div class="skeleton skeleton-accordion"></div>
            <div class="skeleton skeleton-accordion"></div>
            <div class="skeleton skeleton-accordion"></div>
        `;
        setTimeout(() => {
            renderItineraryForDestination(destKey);
            showToast("Đã tạo lịch trình AI mới phù hợp nhu cầu!");
        }, 800);
    }
}


/* ==========================================================================
   MODULE 2: CHATBOT AI & VISION LANDMARK ANALYSIS IN CHAT
   ========================================================================== */
function initHeroEvents() {
    const heroInput = document.getElementById("heroAiInput");
    const heroSendBtn = document.getElementById("heroSendBtn");
    const heroMicBtn = document.getElementById("heroMicBtn");

    if (heroSendBtn && heroInput) {
        heroSendBtn.addEventListener("click", () => {
            const query = heroInput.value.trim();
            if (query) {
                handleAiSearchQuery(query);
                heroInput.value = "";
            }
        });
        heroInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const query = heroInput.value.trim();
                if (query) {
                    handleAiSearchQuery(query);
                    heroInput.value = "";
                }
            }
        });
    }

    if (heroMicBtn) {
        heroMicBtn.addEventListener("click", () => {
            cbOpen();
            cbToggleMic();
        });
    }
}

function handleAiSearchQuery(query) {
    let matchedDest = "danang";
    const qLower = query.toLowerCase();
    if (qLower.includes("phú quốc")) matchedDest = "phuquoc";
    if (qLower.includes("sa pa") || qLower.includes("sapa")) matchedDest = "sapa";
    if (qLower.includes("hà nội")) matchedDest = "hanoi";
    if (qLower.includes("đà lạt")) matchedDest = "dalat";

    const itSection = document.getElementById("itinerarySection");
    if (itSection) itSection.scrollIntoView({ behavior: "smooth" });

    showSkeletonAndRender(matchedDest);
    cbOpen();
    cbSendProgrammaticText(query);
}

function simulateVoiceStt(buttonEl) {
    if (buttonEl) buttonEl.classList.add("recording");
    showToast("🎙️ Đang lắng nghe giọng nói của bạn...");

    openDrawer();
    const transcriptBox = document.getElementById("drawerTranscriptBox");
    if (transcriptBox) {
        transcriptBox.classList.add("active");
        transcriptBox.innerHTML = `Giọng nói: <i>Đang nhận diện âm thanh giọng nói tiếng Việt...</i>`;
    }

    setTimeout(() => {
        if (buttonEl) buttonEl.classList.remove("recording");
        const recognizedText = "Tạo cho tôi lịch trình du lịch Đà Nẵng 3 ngày 2 đêm ăn hải sản ngon";
        if (transcriptBox) {
            transcriptBox.innerHTML = `Giọng nói: <b>"${recognizedText}"</b>`;
        }
        setTimeout(() => {
            if (transcriptBox) transcriptBox.classList.remove("active");
            sendTextMessage(recognizedText);
        }, 1000);
    }, 2000);
}

function initChatDrawerEvents() {
    const openBtn = document.getElementById("openChatDrawerBtn");
    const closeBtn = document.getElementById("closeChatDrawerBtn");
    const overlay = document.getElementById("chatDrawerOverlay");
    const drawerInput = document.getElementById("drawerChatInput");
    const drawerSendBtn = document.getElementById("drawerSendBtn");
    const drawerMicBtn = document.getElementById("drawerMicBtn");

    if (openBtn) openBtn.addEventListener("click", openDrawer);
    if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
    if (overlay) overlay.addEventListener("click", closeDrawer);

    if (drawerSendBtn && drawerInput) {
        drawerSendBtn.addEventListener("click", () => {
            const val = drawerInput.value.trim();
            if (val) {
                sendTextMessage(val);
                drawerInput.value = "";
            }
        });
        drawerInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const val = drawerInput.value.trim();
                if (val) {
                    sendTextMessage(val);
                    drawerInput.value = "";
                }
            }
        });
    }

    if (drawerMicBtn) {
        drawerMicBtn.addEventListener("click", () => {
            simulateVoiceStt(drawerMicBtn);
        });
    }
}

/* Chat Image Analysis (Vision) functions */
window.triggerChatVisionUpload = function () {
    openDrawer();
    const fileInput = document.getElementById("chatVisionFileInput");
    if (fileInput) fileInput.click();
};

window.handleChatVisionFileSelect = function (event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    openDrawer();
    const reader = new FileReader();
    reader.onload = (e) => {
        const imgDataUrl = e.target.result;
        
        addChatImageBubble("user", imgDataUrl, "Ảnh địa danh gửi phân tích AI Vision");

        const wsStatus = document.getElementById("wsStatus");
        if (wsStatus) wsStatus.textContent = "AI Vision đang phân tích hình ảnh...";

        setTimeout(() => {
            const visionReply = `📸 **Kết quả Phân Tích AI Vision:**\n• **Địa danh:** Cầu Vàng (Golden Bridge) - Sun World Bà Nà Hills, Đà Nẵng.\n• **Kiến trúc:** Đôi bàn tay khổng lồ rêu phong nâng đỡ dải lụa vàng giữa mây ngàn độ cao 1,414m.\n• **Kinh nghiệm AI:** Thời điểm chụp ảnh đẹp nhất là 07:30 - 09:00 sáng. Nên kết hợp đi cáp treo Bà Nà Hills và chụp ảnh tại Làng Pháp!`;
            addChatBubble("assistant", visionReply);
            if (wsStatus) wsStatus.textContent = "Sẵn sàng hỗ trợ 24/7";
            showToast("📸 AI Vision đã nhận diện thành công ảnh địa danh trong chat!");
        }, 1200);
    };
    reader.readAsDataURL(file);
};

function addChatImageBubble(role, imgSrc, caption) {
    const chatBody = document.getElementById("drawerChatBody");
    if (!chatBody) return;

    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-msg ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.innerHTML = `
        <img src="${imgSrc}" class="chat-attached-img" alt="Attached image">
        <p>${caption}</p>
    `;

    msgDiv.appendChild(bubble);
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

window.toggleDrawer = function () {
    const drawer = document.getElementById("chatDrawer");
    const overlay = document.getElementById("chatDrawerOverlay");
    if (drawer) {
        const isActive = drawer.classList.contains("active");
        if (isActive) {
            drawer.classList.remove("active");
            if (overlay) overlay.classList.remove("active");
        } else {
            drawer.classList.add("active");
        }
    }
};

window.openDrawer = function () {
    const drawer = document.getElementById("chatDrawer");
    const overlay = document.getElementById("chatDrawerOverlay");
    if (drawer) {
        drawer.classList.add("active");
    }
};

window.closeDrawer = function () {
    const drawer = document.getElementById("chatDrawer");
    const overlay = document.getElementById("chatDrawerOverlay");
    if (drawer) {
        drawer.classList.remove("active");
        if (overlay) overlay.classList.remove("active");
    }
};

window.openDrawerWithPrompt = function (promptText) {
    cbOpen();
    cbSendProgrammaticText(promptText);
};

window.sendTextMessage = function (text) {
    text = (text || "").trim();
    if (!text) return;

    openDrawer();
    addChatBubble("user", text);

    const wsStatus = document.getElementById("wsStatus");
    if (wsStatus) wsStatus.textContent = "Beenavi AI đang suy nghĩ...";

    setTimeout(() => {
        let reply = `Tôi đã nhận yêu cầu "${text}". Lịch trình và các đề xuất đã được cập nhật trực quan trên màn hình!`;
        const tLower = text.toLowerCase();

        if (tLower.includes("hải sản") || tLower.includes("ăn") || tLower.includes("món ngon")) {
            reply = `🦀 Gợi ý Top 3 Quán Hải Sản Ngon Rẻ ở Đà Nẵng:\n1. Hải sản Năm Đảnh (K139/H59/38 Trần Quang Khải) - Đồng giá 60k - 100k.\n2. Hải sản Bé Mặn (Lô 11 Võ Nguyên Giáp) - Tươi sống ngắm biển Mỹ Khê.\n3. Quán Mộc Quán (26 Tô Hiến Thành) - Không gian đẹp, lẩu hải sản siêu ngon!`;
        } else if (tLower.includes("sửa") || tLower.includes("day 1")) {
            reply = `✨ Đã điều chỉnh Ngày 1! Bổ sung điểm dừng chân Chợ Đêm Sơn Trà (19:30) để bạn tha hồ thưởng thức hải sản nướng và quà lưu niệm.`;
        } else if (tLower.includes("thêm ngày") || tLower.includes("tăng")) {
            reply = `🗓️ Đã cập nhật lộ trình thành 4 Ngày 3 Đêm! Bổ sung thêm ngày khám phá Cù Lao Chàm lặn ngắm san hô bãi Chồng.`;
        } else if (tLower.includes("checklist") || tLower.includes("chuẩn bị")) {
            reply = `🎒 Đã tự động kích hoạt Rule Engine bổ sung checklist kính mát, kem chống nắng SPF50+ và túi chống nước điện thoại vào mục Checklist!`;
        } else if (tLower.includes("thời tiết")) {
            reply = `🌤️ Dự báo thời tiết 3 ngày tới tại điểm đến: Nắng ráo nhiệt độ 28°C - 31°C, rất thích hợp tắm biển và đi cáp treo Bà Nà Hills!`;
        }

        addChatBubble("assistant", reply);
        if (wsStatus) wsStatus.textContent = "Sẵn sàng hỗ trợ 24/7";
    }, 900);
};

function addChatBubble(role, text) {
    const chatBody = document.getElementById("drawerChatBody");
    if (!chatBody) return null;

    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-msg ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = text;

    msgDiv.appendChild(bubble);
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    return bubble;
}

/* ==========================================================================
   CAMERA LIVE PHOTO CAPTURE & REALTIME VOICE CALL HANDLERS
   ========================================================================== */
let cameraStream = null;
let isRealtimeCallActive = false;

window.openCameraCaptureModal = function () {
    const modal = document.getElementById("cameraCaptureModal");
    const video = document.getElementById("cameraVideo");
    if (!modal || !video) return;

    modal.style.display = "flex";
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } })
            .then(stream => {
                cameraStream = stream;
                video.srcObject = stream;
            })
            .catch(err => {
                console.warn("Camera access denied or unavailable, fallback simulated stream:", err);
                showToast("📷 Vui lòng cấp quyền truy cập máy ảnh để chụp hình!");
            });
    } else {
        showToast("📷 Trình duyệt không hỗ trợ trực tiếp máy ảnh.");
    }
};

window.closeCameraCaptureModal = function () {
    const modal = document.getElementById("cameraCaptureModal");
    const video = document.getElementById("cameraVideo");
    if (modal) modal.style.display = "none";
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    if (video) video.srcObject = null;
};

window.takeCameraPhotoAndSend = function () {
    const video = document.getElementById("cameraVideo");
    const canvas = document.getElementById("cameraCanvas");

    let imgData = "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80"; // fallback photo

    if (video && canvas && cameraStream) {
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext("2d");
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        imgData = canvas.toDataURL("image/jpeg");
    }

    closeCameraCaptureModal();
    openDrawer();

    addChatImageBubble("user", imgData, "📸 Ảnh chụp trực tiếp từ camera");
    showToast("🔍 AI Vision đang phân tích hình ảnh camera vừa chụp...");

    setTimeout(() => {
        addChatBubble("assistant", "✨ AI Vision đã nhận diện: Bạn vừa chụp hình ảnh món ăn / điểm đến du lịch! Đây là đặc sản hải sản hấp dẫn với đánh giá 4.8/5 sao tại điểm đến của bạn. Bạn có muốn thêm địa điểm này vào lịch trình?");
    }, 1200);
};

window.toggleRealtimeVoiceCall = function () {
    const overlay = document.getElementById("realtimeVoiceOverlay");
    if (!overlay) return;

    openDrawer();
    isRealtimeCallActive = !isRealtimeCallActive;

    if (isRealtimeCallActive) {
        overlay.style.display = "flex";
        showToast("🎧 Đã kết nối đàm thoại giọng nói trực tiếp với AI!");

        if ('speechSynthesis' in window) {
            const synth = window.speechSynthesis;
            const utter = new SpeechSynthesisUtterance("Xin chào Tiến, tôi đang lắng nghe bạn đàm thoại trực tiếp đây!");
            utter.lang = "vi-VN";
            synth.speak(utter);
        }
    } else {
        overlay.style.display = "none";
        showToast("🔇 Đã kết thúc đàm thoại giọng nói.");
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
    }
};


/* ==========================================================================
   TRANG CÁ NHÂN & NHẬT KÝ HÀNH TRÌNH (USER PROFILE & TRAVEL JOURNAL)
   ========================================================================== */
window.openZaloProfileModal = function (tabKey = 'journal') {
    const modal = document.getElementById("zaloProfileModal");
    if (modal) {
        modal.classList.add("active");
        switchProfileTab(tabKey);
    }
};

window.closeZaloProfileModal = function () {
    const modal = document.getElementById("zaloProfileModal");
    if (modal) modal.classList.remove("active");
};

window.switchProfileTab = function (tabKey) {
    const btnJournal = document.getElementById("profileTabJournal");
    const btnTrips = document.getElementById("profileTabTrips");
    const btnPref = document.getElementById("profileTabPref");

    const contentJournal = document.getElementById("profileContentJournal");
    const contentTrips = document.getElementById("profileContentTrips");
    const contentPref = document.getElementById("profileContentPref");

    [btnJournal, btnTrips, btnPref].forEach(b => { if (b) b.classList.remove("active"); });
    [contentJournal, contentTrips, contentPref].forEach(c => { if (c) c.style.display = "none"; });

    if (tabKey === 'journal') {
        if (btnJournal) btnJournal.classList.add("active");
        if (contentJournal) contentJournal.style.display = "block";
    } else if (tabKey === 'trips') {
        if (btnTrips) btnTrips.classList.add("active");
        if (contentTrips) contentTrips.style.display = "block";
    } else if (tabKey === 'pref') {
        if (btnPref) btnPref.classList.add("active");
        if (contentPref) contentPref.style.display = "block";
    }
};

window.saveUserProfileSettings = function () {
    showToast("💾 Đã lưu tùy chỉnh hồ sơ sở thích AI thành công!");
};

window.loadJournalTripToPlanner = function () {
    closeZaloProfileModal();
    showSkeletonAndRender("danang");
    const itSection = document.getElementById("itinerarySection");
    if (itSection) itSection.scrollIntoView({ behavior: "smooth" });
    showToast("🔄 Đã tải lại lộ trình kỷ niệm lên bản đồ tương tác!");
};

window.toggleNotificationsDrawer = function () {
    const drawer = document.getElementById("notificationsDrawer");
    const overlay = document.getElementById("notificationsOverlay");
    if (drawer && overlay) {
        drawer.classList.toggle("active");
        overlay.classList.toggle("active");
    }
};


/* ==========================================================================
   MODULE 4: SMART TRAVEL CHECKLIST
   ========================================================================== */
function initChecklistEvents() {
    updateChecklistProgress();

    const addBtn = document.getElementById("addChecklistBtn");
    const addInput = document.getElementById("customChecklistInput");

    if (addBtn && addInput) {
        addBtn.addEventListener("click", () => {
            const val = addInput.value.trim();
            if (!val) return;

            const weatherGroup = document.getElementById("weatherChecklistItems");
            if (weatherGroup) {
                const label = document.createElement("label");
                label.className = "check-item";
                label.innerHTML = `<input type="checkbox" onchange="updateChecklistProgress()"><span>${val}</span>`;
                weatherGroup.appendChild(label);
                addInput.value = "";
                updateChecklistProgress();
                showToast("Đã thêm item mới vào Checklist!");
            }
        });
    }
}

window.updateChecklistMapping = function () {
    const weatherVal = document.getElementById("checklistWeatherSelect").value;
    const transportVal = document.getElementById("checklistTransportSelect").value;

    const weatherGroup = document.getElementById("weatherChecklistItems");
    const transportGroup = document.getElementById("transportChecklistItems");

    if (weatherGroup && CHECKLIST_DB[weatherVal]) {
        weatherGroup.innerHTML = CHECKLIST_DB[weatherVal].map(item => `
            <label class="check-item ${item.checked ? 'completed' : ''}">
                <input type="checkbox" ${item.checked ? 'checked' : ''} onchange="updateChecklistProgress()">
                <span>${item.text}</span>
            </label>
        `).join("");
    }

    if (transportGroup && CHECKLIST_DB[transportVal]) {
        transportGroup.innerHTML = CHECKLIST_DB[transportVal].map(item => `
            <label class="check-item ${item.checked ? 'completed' : ''}">
                <input type="checkbox" ${item.checked ? 'checked' : ''} onchange="updateChecklistProgress()">
                <span>${item.text}</span>
            </label>
        `).join("");
    }

    updateChecklistProgress();
    showToast("⚡ AI Rule Engine đã cập nhật checklist đồ dùng!");
};

window.updateChecklistProgress = function () {
    const allCheckboxes = document.querySelectorAll(".checklist-items input[type='checkbox']");
    if (!allCheckboxes.length) return;

    let checkedCount = 0;
    allCheckboxes.forEach(cb => {
        const parent = cb.closest(".check-item");
        if (cb.checked) {
            checkedCount++;
            if (parent) parent.classList.add("completed");
        } else {
            if (parent) parent.classList.remove("completed");
        }
    });

    const total = allCheckboxes.length;
    const percentage = Math.round((checkedCount / total) * 100);

    const progressText = document.getElementById("progressText");
    const progressPercentage = document.getElementById("progressPercentage");
    const progressBarFill = document.getElementById("progressBarFill");

    if (progressText) progressText.textContent = `Đã chuẩn bị ${checkedCount}/${total} đồ dùng`;
    if (progressPercentage) progressPercentage.textContent = `${percentage}%`;
    if (progressBarFill) progressBarFill.style.width = `${percentage}%`;
};

window.toggleReminder = function (inputEl) {
    if (inputEl.checked) {
        showToast("🔔 Đã bật nhắc nhở hành trang trước giờ khởi hành 24h!");
    } else {
        showToast("🔕 Đã tắt nhắc nhở hành trang.");
    }
};


/* ==========================================================================
   MODULE 5: SAVE TRIP TO JOURNAL
   ========================================================================== */
window.saveCurrentTripToJournal = function () {
    savedTripsCount++;
    savedPhotosCount += 3;

    const profileStatTrips = document.getElementById("profileStatTrips");
    const profileStatPhotos = document.getElementById("profileStatPhotos");

    if (profileStatTrips) profileStatTrips.textContent = `${savedTripsCount}`;
    if (profileStatPhotos) profileStatPhotos.textContent = `${savedPhotosCount}`;

    openZaloProfileModal('journal');
    showToast("🎉 Đã lưu lịch trình chuyến đi vào Nhật Ký Trong Trang Cá Nhân thành công!");
};

/* Toast Helper */
window.showToast = function (msg) {
    let toast = document.getElementById("toastNotification");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2800);
};

/* Traveloka Tab Interactivity Initialization */
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".trv-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".trv-tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const tabName = btn.textContent.trim().replace("New!", "");
            showToast(`📍 Đã chuyển sang danh mục: ${tabName}`);
        });
    });

    document.querySelectorAll(".trv-sub-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".trv-sub-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
        });
    });

    // Sticky Header Scroll Listener (Glassmorphism & Height Shrink)
    const headerEl = document.getElementById("mainHeader") || document.querySelector(".navbar-traveloka");
    if (headerEl) {
        window.addEventListener("scroll", () => {
            if (window.scrollY > 20) {
                headerEl.classList.add("scrolled");
            } else {
                headerEl.classList.remove("scrolled");
            }
        });
    }
});

/* ==========================================================================
   HAMBURGER 3-BAR MENU & COUNTRY SELECTOR LOGIC
   ========================================================================== */

window.toggleHamburgerMenu = function (e) {
    if (e) e.stopPropagation();
    const panel = document.getElementById("hamburgerPanel");
    const btn = document.getElementById("hamburgerBtn");
    if (!panel) return;

    const isActive = panel.classList.contains("active");
    if (isActive) {
        window.closeHamburgerMenu();
    } else {
        panel.classList.add("active");
        if (btn) btn.classList.add("active");
    }
};

window.closeHamburgerMenu = function () {
    const panel = document.getElementById("hamburgerPanel");
    const btn = document.getElementById("hamburgerBtn");
    if (panel) panel.classList.remove("active");
    if (btn) btn.classList.remove("active");
};

// Close panel when clicking outside
document.addEventListener("click", (e) => {
    const container = document.querySelector(".hamburger-menu-container");
    if (container && !container.contains(e.target)) {
        window.closeHamburgerMenu();
    }
});

// Dynamic Country Switcher (Flag + Country Name Only)
window.selectCountry = function (flag, countryName, btnEl) {
    const sFlag = document.getElementById("selectedFlag");
    const sName = document.getElementById("selectedCountryName");

    if (sFlag) sFlag.textContent = flag;
    if (sName) sName.textContent = countryName;

    document.querySelectorAll(".country-option-btn").forEach(b => b.classList.remove("active"));
    if (btnEl) btnEl.classList.add("active");

    showToast(`🌐 Đã chọn quốc gia: ${flag} ${countryName}`);
};

/* Main Header Navigation SPA Tab View Switcher */
window.switchMainTab = function (tabKey, event) {
    if (event) event.preventDefault();

    // 1. Clear active underline class from all header menu links
    document.querySelectorAll(".traveloka-nav-links .trv-link").forEach(link => {
        link.classList.remove("active");
    });

    // 2. Hide all page views
    const viewHome = document.getElementById("viewHome");
    const viewItinerary = document.getElementById("viewItinerary");
    const viewCommunity = document.getElementById("viewCommunity");
    const viewJournal = document.getElementById("viewJournal");

    if (viewHome) viewHome.style.display = "none";
    if (viewItinerary) viewItinerary.style.display = "none";
    if (viewCommunity) viewCommunity.style.display = "none";
    if (viewJournal) viewJournal.style.display = "none";

    // 3. Handle Home view (Logo click)
    if (tabKey === 'home') {
        if (viewHome) viewHome.style.display = "block";
        window.scrollTo({ top: 0, behavior: 'smooth' });
        showToast("🏠 Đã trở về Trang Chủ Beenavi");
        return;
    }

    // 4. Add active underline to clicked header tab
    if (event && event.currentTarget) {
        if (event.currentTarget.classList.contains("dropdown-item")) {
            const dropTrigger = document.querySelector(".trv-dropdown-trigger");
            if (dropTrigger) dropTrigger.classList.add("active");
        } else {
            event.currentTarget.classList.add("active");
        }
    }

    // 5. Switch to target dedicated page view
    if (tabKey === 'itinerary' || tabKey === 'service') {
        if (viewItinerary) viewItinerary.style.display = "block";
        if (typeof leafletMap !== 'undefined' && leafletMap) {
            setTimeout(() => { leafletMap.invalidateSize(); }, 150);
        }
        showToast("🗺️ Đã chuyển sang giao diện độc lập: Lộ Trình AI");
    } else if (tabKey === 'community') {
        if (viewCommunity) viewCommunity.style.display = "block";
        showToast("👥 Đã chuyển sang giao diện độc lập: Cộng Đồng Du Lịch");
    } else if (tabKey === 'journal') {
        if (viewJournal) viewJournal.style.display = "block";
        showToast("📖 Đã chuyển sang giao diện độc lập: Nhật Ký Hành Trình");
    }

    // Always scroll page to top on view switch
    window.scrollTo({ top: 0, behavior: 'smooth' });
};
