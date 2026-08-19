
function buildDynamicDaysTemplate(numDays) {
    let tpl = "";
    for(let i=1; i<=numDays; i++) {
        tpl += `# NGÀY ${i}: (Tên chủ đề ngày ${i})\n- 08:30 | [Tên điểm sáng] | (1 câu ngắn trải nghiệm)\n- 12:00 | [Quán ăn trưa] | (1 câu món ngon)\n- 15:00 | [Tên điểm chiều] | (1 câu ngắn trải nghiệm)\n- 19:30 | [Tên điểm tối] | (1 câu ngắn trải nghiệm)\n\n`;
    }
    return tpl;
}



function parseChopJSON(raw) {
    let s = raw.trim();
    let start = s.indexOf('{');
    if (start === -1) throw new Error("No JSON object found");
    s = s.substring(start);
    s = s.replace(/[“”]/g, '"').replace(/[‘’]/g, "'");

    let lastError = null;
    
    // Try to parse by chopping off the end character by character if it fails
    for (let chop = 0; chop < 200; chop++) {
        let choppedStr = s.substring(0, s.length - chop);
        
        let inStr = false;
        let escape = false;
        let stack = [];
        for (let i = 0; i < choppedStr.length; i++) {
            let c = choppedStr[i];
            if (escape) { escape = false; continue; }
            if (c === '\\') { escape = true; continue; }
            if (c === '"') { inStr = !inStr; continue; }
            if (!inStr) {
                if (c === '{') stack.push('}');
                else if (c === '[') stack.push(']');
                else if (c === '}' && stack.length > 0 && stack[stack.length-1] === '}') stack.pop();
                else if (c === ']' && stack.length > 0 && stack[stack.length-1] === ']') stack.pop();
            }
        }
        
        let res = choppedStr;
        if (inStr) res += '"';
        
        res = res.trim();
        if (res.endsWith(',')) res = res.slice(0, -1);
        if (res.endsWith(':')) res += 'null';
        
        let tempStack = [...stack];
        while(tempStack.length > 0) {
            let expected = tempStack.pop();
            res = res.trim();
            if (res.endsWith(',')) res = res.slice(0, -1);
            res += expected;
        }
        
        try {
            return JSON.parse(res);
        } catch(e) {
            lastError = e;
            try {
                return new Function('return ' + res)();
            } catch(e2) {
                // Continue chopping
            }
        }
    }
    throw new Error("Could not parse JSON even after chopping. Last error: " + lastError.message);
}

/* ==========================================================================

   TripWise AI - Master Ecosystem Application Logic (app.js)

   ========================================================================== */



// Global State

let currentDestination = "danang";

let activeDay = 1;

let leafletMap = null;

let leafletMarkers = [];

let leafletPolyline = null;

let savedTripsCount = 0;
let savedPhotosCount = 0;

async function syncUserDashboardStats() {
    try {
        const token = localStorage.getItem("beenavi_token") || localStorage.getItem("token");
        const headers = token ? { "Authorization": `Bearer ${token}` } : {};
        const res = await fetch("/api/trips/statistics", { headers });
        if (res.ok) {
            const stats = await res.json();
            savedTripsCount = stats.total_trips || 0;
            savedPhotosCount = stats.total_photos || 0;
            const tripStatEl = document.getElementById("stat-trips-count") || document.querySelector(".stat-trips-val");
            if (tripStatEl) tripStatEl.innerText = savedTripsCount;
            const photoStatEl = document.getElementById("stat-photos-count") || document.querySelector(".stat-photos-val");
            if (photoStatEl) photoStatEl.innerText = savedPhotosCount;
        }
    } catch (e) {
        console.log("[Stats Sync] API skipped:", e);
    }
}

// Tự động đồng bộ thống kê khi khởi động app
if (typeof document !== 'undefined') {
    document.addEventListener("DOMContentLoaded", () => {
        syncUserDashboardStats();
    });
}



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
    ],
    tech: [
        { text: "Sạc dự phòng 20,000mAh & Cáp sạc", checked: true },
        { text: "Thuốc say xe & Thuốc cá nhân", checked: true },
        { text: "Túi chống nước điện thoại", checked: false },
        { text: "Máy ảnh / Gậy chụp hình Bluetooth", checked: false }
    ]
};



// Application Initialization

document.addEventListener("DOMContentLoaded", () => {
    checkAuthStatus();
    initLeafletMap();
    renderItineraryForDestination("danang");
    initChecklistEvents();
    initHeroEvents();
    initChatDrawerEvents();
});




window.selectInspirationDestination = function (destKey) {

    const destSelect = document.getElementById("prefDestinationSelect");

    if (destSelect) destSelect.value = destKey;



    const itSection = document.getElementById("itinerarySection");

    if (itSection) itSection.scrollIntoView({ behavior: "smooth" });



    showSkeletonAndRender(destKey);

};



/* Curated Pre-generated Itineraries Action on Home Page */
window.previewPrebuiltTrip = function (destKey) {
    window.switchMainTab('itinerary');
    if (typeof showSkeletonAndRender === 'function') {
        showSkeletonAndRender(destKey);
    }
    showToast(`🗺️ Đang mở lộ trình mẫu: ${destKey.toUpperCase()}`);
};

window.clonePrebuiltTrip = function (destKey, tripTitle) {
    if (!window.currentUser) {
        showToast("🔐 Vui lòng đăng nhập để Clone & Lưu trữ lộ trình AI về tài khoản!");
        window.openAuthModal('login');
        return;
    }

    window.switchMainTab('itinerary');
    if (typeof showSkeletonAndRender === 'function') {
        showSkeletonAndRender(destKey);
    }
    showToast(`🎉 Đã Clone thành công: "${tripTitle}"`);
    if (typeof openDrawerWithPrompt === 'function') {
        openDrawerWithPrompt(`Tôi vừa nhân bản (Clone) lịch trình: "${tripTitle}". Hãy giúp tôi điều chỉnh và tối ưu thêm chi phí cũng như các điểm check-in!`);
    }
};

window.filterCuratedTrips = function (category, btnEl) {
    document.querySelectorAll('.curated-pill-btn').forEach(btn => btn.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    const cards = document.querySelectorAll('.curated-trip-card');
    cards.forEach(card => {
        const cat = card.getAttribute('data-category');
        if (category === 'all' || cat === category) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
};

window.cloneCommunityTrip = window.clonePrebuiltTrip;





/* ==========================================================================

   MODULE 1: ITINERARY GENERATOR & LEAFLET MAP

   ========================================================================== */

let userLocation = { lat: 21.0285, lng: 105.8542 }; // Default Hanoi
let currentRouteLayer = null;
let userMarker = null;
let destMarker = null;

function initLeafletMap() {
    const mapEl = document.getElementById("leafletMap");
    if (!mapEl) return;

    // Default to Hanoi
    leafletMap = L.map('leafletMap').setView([userLocation.lat, userLocation.lng], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(leafletMap);

    // Xin quyền vị trí
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                userLocation.lat = position.coords.latitude;
                userLocation.lng = position.coords.longitude;
                leafletMap.setView([userLocation.lat, userLocation.lng], 13);
                
                // Icon Vị trí của bạn
                const userIcon = L.divIcon({
                    html: '<div style="background:#4285F4; width:16px; height:16px; border-radius:50%; border:3px solid white; box-shadow:0 0 5px rgba(0,0,0,0.5);"></div>',
                    className: '',
                    iconSize: [22, 22],
                    iconAnchor: [11, 11]
                });
                
                userMarker = L.marker([userLocation.lat, userLocation.lng], { icon: userIcon })
                    .addTo(leafletMap)
                    .bindPopup("<b>Vị trí của bạn</b>")
                    .openPopup();
            },
            function (error) {
                console.log("User denied location or error", error);
            }
        );
    }
}



function updateWeatherUI(wData, fallbackCity = "Hà Nội") {
    if (!wData) return;
    const wIcon = document.getElementById("weatherIcon");
    const wTemp = document.getElementById("weatherTemp");
    const wDesc = document.getElementById("weatherDesc");

    const cityName = wData.city || wData.destination || fallbackCity || "Điểm đến";
    const desc = wData.description || wData.desc || "Nắng ráo, thời tiết lý tưởng";
    const tag = (wData.weather_tag || "").toLowerCase();

    let tempText = "";
    if (wData.temp !== undefined && wData.temp !== null) {
        tempText = typeof wData.temp === "number" ? `${Math.round(wData.temp)}°C` : `${wData.temp}`;
        if (!tempText.endsWith("°C")) tempText += "°C";
    } else {
        tempText = wData.temp_str || "26°C";
    }

    let icon = wData.icon;
    if (!icon) {
        if (tag.includes("mưa lớn") || tag.includes("bão") || tag.includes("thunder")) icon = "⛈️";
        else if (tag.includes("mưa") || tag.includes("rain") || tag.includes("drizzle")) icon = "🌧️";
        else if (tag.includes("lạnh") || tag.includes("giá") || tag.includes("tuyết")) icon = "❄️";
        else if (tag.includes("nắng nóng") || tag.includes("hot")) icon = "🔥";
        else if (tag.includes("gió") || tag.includes("ẩm") || tag.includes("sương") || tag.includes("fog")) icon = "🌫️";
        else if (tag.includes("ấm") || tag.includes("mây") || tag.includes("cloud")) icon = "⛅";
        else icon = "☀️";
    }

    if (wIcon) wIcon.textContent = icon;
    if (wTemp) wTemp.textContent = tempText;
    if (wDesc) wDesc.textContent = `${cityName} • ${desc}`;

    const wTempText = document.getElementById("weatherTempText");
    const wSummaryText = document.getElementById("weatherSummaryText");
    if (wTempText) wTempText.textContent = tempText;
    if (wSummaryText) wSummaryText.textContent = `${cityName} • ${desc}`;
}
window.updateWeatherUI = updateWeatherUI;

async function fetchWeatherForCity(cityName) {
    if (!cityName) return null;
    try {
        const res = await fetch(`/api/weather?destination=${encodeURIComponent(cityName)}`);
        if (res.ok) {
            const data = await res.json();
            updateWeatherUI(data, cityName);
            return data;
        }
    } catch(e) {
        console.warn("[Weather] Fetch error:", e);
    }
    return null;
}
window.fetchWeatherForCity = fetchWeatherForCity;

function renderItineraryForDestination(destKey) {

    currentDestination = destKey;

    const destData = DESTINATIONS_DB[destKey] || DESTINATIONS_DB["danang"];

    const titleEl = document.getElementById("itinerarySectionTitle");

    const subTitleEl = document.getElementById("itinerarySectionSubtitle");

    const costAmount = document.getElementById("costAmountText");

    const costDetails = document.getElementById("costDetailsText");

    if (titleEl) titleEl.textContent = destData.title;

    if (subTitleEl) subTitleEl.textContent = destData.subtitle;

    if (destData.weather) {
        updateWeatherUI(destData.weather, destKey === "hanoi" ? "Hà Nội" : destKey === "sapa" ? "Sa Pa" : destKey === "phuquoc" ? "Phú Quốc" : destKey === "dalat" ? "Đà Lạt" : "Đà Nẵng");
    }

    // Tự động gọi API thời tiết thực tế theo điểm đến
    const queryCity = destKey === "hanoi" ? "Hà Nội" :
                      destKey === "sapa" ? "Sa Pa" :
                      destKey === "phuquoc" ? "Phú Quốc" :
                      destKey === "dalat" ? "Đà Lạt" : "Đà Nẵng";
    fetchWeatherForCity(queryCity);

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

    renderTripChecklist("trip_" + destKey, queryCity, destData.weather?.desc);

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

            if (act.lat && act.lng && !isNaN(act.lat) && !isNaN(act.lng)) {

                const marker = L.marker([act.lat, act.lng]).addTo(leafletMap)

                    .bindPopup(`<b>${act.title}</b><br>${act.desc}`);

                leafletMarkers.push(marker);

                polylineCoords.push([act.lat, act.lng]);

            }

        });

    });



    if (polylineCoords.length > 1) {

        leafletPolyline = L.polyline(polylineCoords, {

            color: '#E8B923',

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



window.focusMapLocation = async function (dummyLat, dummyLng, title) {
    if (!leafletMap) return;
    
    showToast("Đang tìm đường đi...");
    
    let finalLat = null;
    let finalLng = null;
    
    try {
        const res = await fetch(`/location?name=${encodeURIComponent(title)}`);
        if (res.ok) {
            const data = await res.json();
            if (data && data.lat) {
                finalLat = data.lat;
                finalLng = data.lon;
            }
        }
    } catch(e) {
        console.error("Lỗi lấy tọa độ", e);
    }
    
    if (!finalLat || !finalLng) {
        showToast(`❌ Tọa độ của "${title}" không có trong dữ liệu.`);
        return;
    }

    leafletMap.flyTo([finalLat, finalLng], 14, { duration: 1 });
    
    if (destMarker) leafletMap.removeLayer(destMarker);
    destMarker = L.marker([finalLat, finalLng])
        .addTo(leafletMap)
        .bindPopup(`<b>${title}</b>`)
        .openPopup();

    // Gọi OSRM Routing
    if (userLocation.lat && userLocation.lng) {
        try {
            const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${userLocation.lng},${userLocation.lat};${finalLng},${finalLat}?overview=full&geometries=geojson`;
            const routeRes = await fetch(osrmUrl);
            const routeData = await routeRes.json();
            
            if (routeData.code === "Ok" && routeData.routes.length > 0) {
                const routeGeoJson = routeData.routes[0].geometry;
                
                if (currentRouteLayer) {
                    leafletMap.removeLayer(currentRouteLayer);
                }
                
                currentRouteLayer = L.geoJSON(routeGeoJson, {
                    style: {
                        color: "#4285F4",
                        weight: 5,
                        opacity: 0.8
                    }
                }).addTo(leafletMap);
                
                // Fit bounds
                const bounds = L.latLngBounds([userLocation.lat, userLocation.lng], [finalLat, finalLng]);
                leafletMap.fitBounds(bounds, { padding: [50, 50] });
                
                const distanceKm = (routeData.routes[0].distance / 1000).toFixed(1);
                showToast(`Đã tìm thấy đường đi! Khoảng cách: ${distanceKm} km.`);
            }
        } catch(e) {
            console.error("Lỗi Routing OSRM", e);
            showToast("Không thể tìm đường lúc này.");
        }
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
            const userName = (window.currentUser && (window.currentUser.full_name || window.currentUser.username)) ? (window.currentUser.full_name || window.currentUser.username) : "bạn";
            const utter = new SpeechSynthesisUtterance(`Xin chào ${userName}, tôi đang lắng nghe bạn đàm thoại trực tiếp đây!`);
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
   MODULE: AUTHENTICATION & DYNAMIC PROFILE / DIARY (TRUONG VAN HOAN FLOW)
   ========================================================================== */

window.currentUser = null;

window.getAuthToken = function() {
    return localStorage.getItem('beenavi_token') || '';
};

window.getAuthHeaders = function() {
    const token = window.getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
};

window.checkAuthStatus = async function() {
    const token = window.getAuthToken();
    if (!token) {
        window.currentUser = null;
        window.updateNavbarAuthState();
        window.renderJournalView();
        return;
    }
    try {
        const res = await fetch('/api/users/profile', {
            headers: window.getAuthHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            window.currentUser = data;
        } else {
            window.currentUser = null;
            localStorage.removeItem('beenavi_token');
        }
    } catch (e) {
        window.currentUser = null;
    }
    window.updateNavbarAuthState();
    window.renderJournalView();
};

window.updateNavbarAuthState = function() {
    const navGuestBox = document.getElementById('navGuestBox');
    const navUserBox = document.getElementById('navUserBox');
    const navUserAvatarText = document.getElementById('navUserAvatarText');
    const navPanelAvatarInitial = document.getElementById('navPanelAvatarInitial');
    const navPanelUserName = document.getElementById('navPanelUserName');
    const navPanelUserEmail = document.getElementById('navPanelUserEmail');

    if (window.currentUser) {
        if (navGuestBox) navGuestBox.style.display = 'none';
        if (navUserBox) navUserBox.style.display = 'flex';
        const displayName = window.currentUser.full_name || window.currentUser.username || 'User';
        const initial = displayName.charAt(0).toUpperCase();
        if (navUserAvatarText) navUserAvatarText.textContent = initial;
        if (navPanelAvatarInitial) navPanelAvatarInitial.textContent = initial;
        if (navPanelUserName) navPanelUserName.innerHTML = `${displayName} <span class="vip-badge">MEMBER</span>`;
        if (navPanelUserEmail) navPanelUserEmail.textContent = window.currentUser.email || '';
    } else {
        if (navGuestBox) navGuestBox.style.display = 'flex';
        if (navUserBox) navUserBox.style.display = 'none';
    }
};

window.renderJournalView = async function() {
    const guestBox = document.getElementById('journalGuestState');
    const authBox = document.getElementById('journalAuthState');
    if (!guestBox || !authBox) return;

    if (!window.currentUser) {
        guestBox.style.display = 'block';
        authBox.style.display = 'none';
        return;
    }

    guestBox.style.display = 'none';
    authBox.style.display = 'block';

    const displayName = window.currentUser.full_name || window.currentUser.username || 'Bạn';
    const username = window.currentUser.username || 'user';
    const initial = displayName.charAt(0).toUpperCase();

    const headerName = document.getElementById('journalHeaderName');
    const dispName = document.getElementById('journalDisplayName');
    const userHandle = document.getElementById('journalUserHandle');
    const avatarBox = document.getElementById('journalAvatarBox');
    const bioText = document.getElementById('journalBioText');

    if (headerName) headerName.textContent = displayName;
    if (dispName) dispName.textContent = displayName;
    if (userHandle) userHandle.textContent = `@${username} • Thành Viên Beenavi Smart 🇻🇳`;
    if (avatarBox) avatarBox.textContent = initial;

    // Load dynamic statistics
    try {
        const res = await fetch('/api/trips/statistics', { headers: window.getAuthHeaders() });
        if (res.ok) {
            const stats = await res.json();
            const statTrips = document.getElementById('journalStatTrips');
            const statPhotos = document.getElementById('journalStatPhotos');
            const statDests = document.getElementById('journalStatDests');
            const statSpent = document.getElementById('journalStatSpent');

            if (statTrips) statTrips.textContent = stats.total_trips || 0;
            if (statPhotos) statPhotos.textContent = stats.total_photos || 0;
            if (statDests) statDests.textContent = stats.unique_destinations || 0;
            if (statSpent) statSpent.textContent = stats.total_spent ? `${stats.total_spent.toLocaleString('vi-VN')} đ` : "0 đ";
        }
    } catch(e) {}

    // Load dynamic trips into grid
    const grid = document.getElementById('journalTripsGrid');
    if (grid) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 30px; color: #64748B;">Đang nạp danh sách chuyến đi...</div>';
        try {
            const res = await fetch('/api/trips', { headers: window.getAuthHeaders() });
            if (res.ok) {
                const trips = await res.json();
                if (!trips || trips.length === 0) {
                    grid.innerHTML = `
                        <div class="journal-empty-trips-card" style="grid-column: 1/-1; background: var(--bg-card); border-radius: 18px; border: 1.5px dashed var(--border); padding: 40px 20px; text-align: center;">
                            <div style="font-size: 44px; margin-bottom: 12px;">🗺️</div>
                            <h4 style="font-size: 17px; font-weight: 700; color: var(--text-main); margin: 0 0 6px;">Chưa có chuyến đi nào trong nhật ký</h4>
                            <p style="font-size: 13.5px; color: var(--text-muted); margin: 0 0 16px;">Tạo kế hoạch du lịch mới bằng Trợ lý AI để tự động lưu vào đây!</p>
                            <button class="btn-primary" style="padding: 10px 22px; font-size: 13.5px; font-weight: 700;" onclick="switchMainTab('itinerary', event)">
                                ➕ Tạo Lịch Trình Đầu Tiên Ngay
                            </button>
                        </div>
                    `;
                    return;
                }

                const defaultImages = {
                    'danang': 'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=600&q=80',
                    'hagiang': 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80',
                    'phuquoc': 'https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?auto=format&fit=crop&w=600&q=80',
                    'dalat': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=600&q=80',
                    'sapa': 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80',
                    'hanoi': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=600&q=80',
                    'nhatrang': 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=600&q=80'
                };

                let cardsHtml = '';
                trips.forEach(t => {
                    const destLower = (t.destination || '').toLowerCase().replace(/đ/g, 'd').replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, 'a').replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, 'e').replace(/ì|í|ị|ỉ|ĩ/g, 'i').replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, 'o').replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, 'u').replace(/ỳ|ý|ỵ|ỷ|ỹ/g, 'y').replace(/\s+/g, '');
                    let imgUrl = defaultImages[destLower] || 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80';
                    const budgetFormatted = t.budget_limit ? `${t.budget_limit.toLocaleString('vi-VN')} đ` : 'Tiêu chuẩn';
                    const title = t.title || `Hành Trình ${t.destination}`;

                    cardsHtml += `
                        <div class="journal-history-card">
                            <img src="${imgUrl}" alt="${t.destination}" class="journal-card-img" onerror="this.src='https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80'">
                            <div class="journal-card-body">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                                    <span class="journal-badge-done">📍 ${t.destination} • ${t.number_of_days}N</span>
                                    <span style="font-size: 11.5px; color: #64748B;">${t.created_at ? t.created_at.substring(0, 10) : ''}</span>
                                </div>
                                <h4 style="font-size: 16px; font-weight: 800; color: var(--text-main); margin: 0 0 6px;">${title}</h4>
                                <div style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 12px;">
                                    Khởi hành: <b>${t.departure_location || 'Hà Nội'}</b> • Dự toán: <b style="color: var(--primary);">${budgetFormatted}</b>
                                </div>
                                <div style="display:flex; gap: 8px; align-items:center;">
                                    <button class="btn-secondary" style="flex:1; padding: 8px 12px; font-size: 12.5px;" onclick="loadJournalTripToPlanner('${t.id}')">🔄 Xem Lộ Trình</button>
                                    <button style="background:#FEE2E2; color:#EF4444; border:none; border-radius:10px; width:36px; height:36px; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:14px;" title="Xóa chuyến đi" onclick="deleteTripFromDB('${t.id}')">🗑️</button>
                                </div>
                            </div>
                        </div>
                    `;
                });
                grid.innerHTML = cardsHtml;
            }
        } catch(e) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 30px; color: #EF4444;">Lỗi khi tải danh sách chuyến đi.</div>';
        }
    }
};

window.openAuthModal = function(tab = 'login') {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
        window.switchAuthTab(tab);
    }
};

window.closeAuthModal = function() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
};

window.switchAuthTab = function(tab) {
    const btnLogin = document.getElementById('tabBtnLogin');
    const btnReg = document.getElementById('tabBtnRegister');
    const formLogin = document.getElementById('formLogin');
    const formRegister = document.getElementById('formRegister');
    const title = document.getElementById('authModalTitle');

    if (tab === 'login') {
        if (btnLogin) btnLogin.classList.add('active');
        if (btnReg) btnReg.classList.remove('active');
        if (formLogin) formLogin.style.display = 'block';
        if (formRegister) formRegister.style.display = 'none';
        if (title) title.textContent = 'Đăng Nhập BeeNavi';
    } else {
        if (btnLogin) btnLogin.classList.remove('active');
        if (btnReg) btnReg.classList.add('active');
        if (formLogin) formLogin.style.display = 'none';
        if (formRegister) formRegister.style.display = 'block';
        if (title) title.textContent = 'Tạo Tài Khoản Mới';
    }
};

window.handleLoginSubmit = async function(e) {
    if (e) e.preventDefault();
    const u = document.getElementById('loginUsername')?.value.trim();
    const p = document.getElementById('loginPassword')?.value;
    if (!u || !p) {
        showToast('⚠️ Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!');
        return;
    }

    const btn = document.getElementById('btnLoginSubmit');
    if (btn) { btn.disabled = true; btn.textContent = 'Đang đăng nhập...'; }

    try {
        const res = await fetch('/api/users/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (res.ok && data.token) {
            localStorage.setItem('beenavi_token', data.token);
            window.currentUser = data.user || { username: u, full_name: u };
            window.updateNavbarAuthState();
            window.renderJournalView();
            window.closeAuthModal();
            showToast(`🎉 Chào mừng trở lại, ${window.currentUser.full_name || u}!`);
        } else {
            showToast(`❌ ${data.detail || 'Sai tên đăng nhập hoặc mật khẩu!'}`);
        }
    } catch (err) {
        showToast('❌ Lỗi kết nối máy chủ!');
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Đăng Nhập Ngay'; }
    }
};

window.handleRegisterSubmit = async function(e) {
    if (e) e.preventDefault();
    const fullName = document.getElementById('regFullName')?.value.trim();
    const u = document.getElementById('regUsername')?.value.trim();
    const email = document.getElementById('regEmail')?.value.trim();
    const p = document.getElementById('regPassword')?.value;

    if (!fullName || !u || !email || !p) {
        showToast('⚠️ Vui lòng điền đầy đủ các trường!');
        return;
    }

    const btn = document.getElementById('btnRegisterSubmit');
    if (btn) { btn.disabled = true; btn.textContent = 'Đang tạo tài khoản...'; }

    try {
        const res = await fetch('/api/users/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: fullName, username: u, email: email, password: p })
        });
        const data = await res.json();
        if (res.ok && data.token) {
            localStorage.setItem('beenavi_token', data.token);
            window.currentUser = data.user || { username: u, full_name: fullName, email: email };
            window.updateNavbarAuthState();
            window.renderJournalView();
            window.closeAuthModal();
            showToast(`🎉 Chúc mừng ${fullName} đã đăng ký tài khoản thành công!`);
        } else {
            showToast(`❌ ${data.detail || 'Không thể đăng ký tài khoản!'}`);
        }
    } catch (err) {
        showToast('❌ Lỗi kết nối máy chủ!');
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Đăng Ký Tài Khoản'; }
    }
};

window.handleLogout = function() {
    localStorage.removeItem('beenavi_token');
    window.currentUser = null;
    window.updateNavbarAuthState();
    window.renderJournalView();
    window.closeZaloProfileModal();
    showToast('👋 Bạn đã đăng xuất an toàn.');
};

window.openZaloProfileModal = async function (tabKey = 'journal') {
    if (!window.currentUser) {
        showToast('🔐 Vui lòng đăng nhập để xem Hồ sơ & Nhật ký chuyến đi!');
        window.openAuthModal('login');
        return;
    }

    const modal = document.getElementById("zaloProfileModal");
    if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
        window.switchProfileTab(tabKey);
    }

    // Populate user profile info
    const pName = document.getElementById("profileUserName");
    const pHandle = document.getElementById("profileUserHandle");
    const pAvatar = document.getElementById("profileAvatarBox");
    const displayName = window.currentUser.full_name || window.currentUser.username || 'User';
    if (pName) pName.innerHTML = `${displayName} <span style="color: var(--primary); font-size: 16px;">✓</span>`;
    if (pHandle) pHandle.textContent = `@${window.currentUser.username || 'user'} • Thành Viên Beenavi Smart 🇻🇳`;
    if (pAvatar) pAvatar.textContent = displayName.charAt(0).toUpperCase();

    // Fetch and populate stats
    try {
        const res = await fetch('/api/trips/statistics', { headers: window.getAuthHeaders() });
        if (res.ok) {
            const stats = await res.json();
            const pTrips = document.getElementById("profileStatTrips");
            const pPhotos = document.getElementById("profileStatPhotos");
            const pDests = document.getElementById("profileStatDests");
            const pSpent = document.getElementById("profileStatSpent");

            if (pTrips) pTrips.textContent = stats.total_trips || 0;
            if (pPhotos) pPhotos.textContent = stats.total_photos || 0;
            if (pDests) pDests.textContent = stats.unique_destinations || 0;
            if (pSpent) pSpent.textContent = stats.total_spent ? `${stats.total_spent.toLocaleString('vi-VN')} đ` : "0 đ";
        }
    } catch(e) {}
};

window.closeZaloProfileModal = function () {
    const modal = document.getElementById("zaloProfileModal");
    if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
    }
};

window.switchProfileTab = async function (tabKey) {
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
        if (contentJournal) {
            contentJournal.style.display = "block";
            window.loadJournalPhotosFeed();
        }
    } else if (tabKey === 'trips') {
        if (btnTrips) btnTrips.classList.add("active");
        if (contentTrips) {
            contentTrips.style.display = "block";
            window.loadUserTripsList();
        }
    } else if (tabKey === 'pref') {
        if (btnPref) btnPref.classList.add("active");
        if (contentPref) {
            contentPref.style.display = "block";
            window.loadUserPreferencesIntoForm();
        }
    }
};

window.loadJournalPhotosFeed = async function() {
    const container = document.getElementById('journalFeedContainer');
    if (!container) return;
    try {
        const res = await fetch('/api/trips', { headers: window.getAuthHeaders() });
        if (res.ok) {
            const trips = await res.json();
            if (!trips || trips.length === 0) {
                container.innerHTML = `
                    <div class="profile-empty-state">
                        <div class="profile-empty-icon">📷</div>
                        <h4 style="margin:0 0 6px 0; color:#334155;">Chưa có ảnh kỷ niệm nào</h4>
                        <p style="margin:0; font-size:13px; color:#94A3B8;">Khi bạn tạo lịch trình và lưu lại, bạn có thể tải ảnh check-in lên đây!</p>
                    </div>
                `;
                return;
            }

            let html = '<div style="display:flex; flex-direction:column; gap:16px;">';
            trips.forEach(t => {
                html += `
                    <div style="background:var(--bg-page); border-radius:14px; border:1px solid var(--border); padding:16px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-size:12px; font-weight:700; color:var(--primary);">📍 ${t.destination} • ${t.number_of_days} ngày</span>
                            <span style="font-size:12px; color:#64748B;">${t.created_at ? t.created_at.substring(0, 10) : ''}</span>
                        </div>
                        <h4 style="margin:0 0 8px 0; font-size:15px; color:var(--text-main);">${t.title || 'Chuyến đi ' + t.destination}</h4>
                        <div style="display:flex; gap:8px;">
                            <button class="add-item-btn" style="padding:6px 12px; font-size:12px;" onclick="loadJournalTripToPlanner('${t.id}')">🔄 Tải Lên Bản Đồ</button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        }
    } catch(e) {
        container.innerHTML = '<div class="profile-empty-state">Không thể tải dữ liệu nhật ký.</div>';
    }
};

window.loadUserTripsList = async function() {
    const container = document.getElementById('savedTripsListContainer');
    if (!container) return;
    try {
        const res = await fetch('/api/trips', { headers: window.getAuthHeaders() });
        if (res.ok) {
            const trips = await res.json();
            if (!trips || trips.length === 0) {
                container.innerHTML = `
                    <div class="profile-empty-state">
                        <div class="profile-empty-icon">🗺️</div>
                        <h4 style="margin:0 0 6px 0; color:#334155;">Chưa có chuyến đi nào được lưu</h4>
                        <p style="margin:0; font-size:13px; color:#94A3B8;">Hãy chuyển sang tab "Lộ Trình AI" để tạo lịch trình đầu tiên của bạn!</p>
                    </div>
                `;
                return;
            }

            let html = '<div style="display:flex; flex-direction:column; gap:12px;">';
            trips.forEach(t => {
                html += `
                    <div style="background:var(--bg-page); padding:16px; border-radius:14px; border:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:12px; font-weight:700; color:var(--primary);">${t.number_of_days} Ngày • Dự toán: ${t.budget_limit ? t.budget_limit.toLocaleString('vi-VN') + ' đ' : 'Tiêu chuẩn'}</div>
                            <div style="font-size:15.5px; font-weight:800; color:var(--text-main); margin:3px 0;">${t.title || t.destination}</div>
                            <div style="font-size:12px; color:var(--text-muted);">Khởi hành từ: ${t.departure_location || 'Hà Nội/HCM'} • ${t.vehicle || 'Máy bay'}</div>
                        </div>
                        <div style="display:flex; gap:6px;">
                            <button class="add-item-btn" style="padding:6px 12px; font-size:12px;" onclick="loadJournalTripToPlanner('${t.id}')">🔄 Xem Lộ Trình</button>
                            <button style="background:#FEE2E2; color:#EF4444; border:none; border-radius:8px; padding:6px 10px; font-size:12px; cursor:pointer;" onclick="deleteTripFromDB('${t.id}')">🗑️</button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        }
    } catch(e) {
        container.innerHTML = '<div class="profile-empty-state">Không thể tải danh sách chuyến đi.</div>';
    }
};

window.deleteTripFromDB = async function(tripId) {
    if (!confirm('Bạn có chắc chắn muốn xóa chuyến đi này khỏi nhật ký?')) return;
    try {
        const res = await fetch(`/api/trips/${tripId}`, {
            method: 'DELETE',
            headers: window.getAuthHeaders()
        });
        if (res.ok) {
            showToast('🗑️ Đã xóa chuyến đi thành công!');
            if (typeof window.loadUserTripsList === 'function') window.loadUserTripsList();
            if (typeof window.renderJournalView === 'function') window.renderJournalView();
        }
    } catch(e) {}
};

window.loadUserPreferencesIntoForm = async function() {
    try {
        const res = await fetch('/api/users/profile', { headers: window.getAuthHeaders() });
        if (res.ok) {
            const profile = await res.json();
            const styles = profile.travel_style || [];
            const allergies = profile.food_allergies || [];
            const companions = profile.special_requirements || [];

            document.querySelectorAll('.user-pref-style').forEach(cb => {
                cb.checked = styles.includes(cb.value);
            });
            document.querySelectorAll('.user-pref-allergy').forEach(cb => {
                cb.checked = allergies.includes(cb.value);
            });
            document.querySelectorAll('.user-pref-companion').forEach(cb => {
                cb.checked = companions.includes(cb.value);
            });
        }
    } catch(e) {}
};

window.saveUserProfilePreferences = async function() {
    const selectedStyles = Array.from(document.querySelectorAll('.user-pref-style:checked')).map(c => c.value);
    const selectedAllergies = Array.from(document.querySelectorAll('.user-pref-allergy:checked')).map(c => c.value);
    const selectedCompanions = Array.from(document.querySelectorAll('.user-pref-companion:checked')).map(c => c.value);

    try {
        const res = await fetch('/api/users/profile', {
            method: 'PUT',
            headers: window.getAuthHeaders(),
            body: JSON.stringify({
                travel_style: selectedStyles,
                food_allergies: selectedAllergies,
                special_requirements: selectedCompanions
            })
        });
        if (res.ok) {
            showToast('💾 Đã lưu tùy chỉnh sở thích AI vào CSDL thành công!');
        } else {
            showToast('❌ Lỗi khi lưu cài đặt sở thích!');
        }
    } catch(e) {
        showToast('❌ Lỗi kết nối máy chủ!');
    }
};

window.promptAddPhotoToCheckin = function() {
    showToast('📷 Tính năng tải ảnh check-in đang sẵn sàng...');
};

window.loadJournalTripToPlanner = async function (tripId) {
    closeZaloProfileModal();
    if (tripId) {
        try {
            const res = await fetch(`/api/trips/${tripId}`, { headers: window.getAuthHeaders() });
            if (res.ok) {
                const trip = await res.json();
                window.currentChecklistTripId = trip.id;
                if (trip.days && trip.days.length > 0) {
                    if (typeof renderAIItinerary === 'function') {
                        renderAIItinerary({
                            tieu_de: trip.title || trip.destination,
                            tong_chi_phi: trip.budget_limit ? `${trip.budget_limit.toLocaleString('vi-VN')} VNĐ` : "Tùy chỉnh",
                            lich_trinh: trip.days
                        }, trip.destination);
                    }
                }
                if (trip.checklist && Array.isArray(trip.checklist) && trip.checklist.length > 0) {
                    renderTripChecklist(trip.checklist, trip.id);
                }

                // Đồng bộ vào Balo
                window.currentBackpack = {
                    tripId: trip.id,
                    title: trip.title || trip.destination,
                    destination: trip.destination,
                    cost: trip.budget_limit ? `${trip.budget_limit.toLocaleString('vi-VN')} VNĐ` : "Tùy chỉnh",
                    weather: "Nắng ráo",
                    days: trip.days || [],
                    checklist: trip.checklist || []
                };
                try {
                    localStorage.setItem("beenavi_backpack", JSON.stringify(window.currentBackpack));
                } catch(e) {}
                renderBackpackUI();
            }
        } catch(e) {
            console.warn("Load journal trip error:", e);
        }
    }
    const itSection = document.getElementById("itinerarySection");
    if (itSection) itSection.scrollIntoView({ behavior: "smooth" });
    showToast("🔄 Đã tải lại lộ trình & checklist lên bản đồ và Balo!");
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
   MODULE 4: SMART TRAVEL CHECKLIST & TRIP DB PERSISTENCE
   ========================================================================== */

window.currentChecklistTripId = null;

function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function renderChecklistItemHTML(item) {
    const isComp = !!(item.is_completed || item.checked);
    const compClass = isComp ? "completed" : "";
    const checkedAttr = isComp ? "checked" : "";
    const itemId = item.id || `chk_${Math.random().toString(36).substr(2, 9)}`;
    const text = item.item_name || item.text || "Đồ dùng";
    return `
        <label class="check-item ${compClass}" data-id="${itemId}">
            <input type="checkbox" ${checkedAttr} onchange="toggleChecklistItemStatus(this, '${itemId}')">
            <span>${escapeHtml(text)}</span>
            <button type="button" class="chk-del-btn" onclick="deleteChecklistItemUI(event, '${itemId}', this)" title="Xóa món đồ này" style="margin-left:auto; background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:16px; opacity:0.5; padding:0 4px; line-height:1;">&times;</button>
        </label>
    `;
}

async function renderTripChecklist(tripId, destName = "", weatherTag = "", vehicle = "") {
    window.currentChecklistTripId = tripId || `trip_${(destName || 'vietnam').toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    
    // Hiển thị checklist section
    const chkSection = document.getElementById("checklistSection");
    if (chkSection) chkSection.style.display = "block";

    const subtitleEl = document.getElementById("checklistSubtitle");
    if (subtitleEl && destName) {
        subtitleEl.textContent = `Tự động gợi ý danh sách chuẩn bị dựa trên thời tiết và phương tiện đi ${destName}.`;
    }

    // Xác định weather mapping phù hợp
    const wTag = (weatherTag || "").toLowerCase();
    let weatherKey = "sunny";
    if (wTag.includes("lạnh") || wTag.includes("giá") || wTag.includes("tuyết") || (destName && (destName.includes("Sa Pa") || destName.includes("Sapa") || destName.includes("Đà Lạt")))) {
        weatherKey = "cold";
    } else if (wTag.includes("mưa") || wTag.includes("ẩm") || wTag.includes("bão") || wTag.includes("dông")) {
        weatherKey = "rain";
    }
    const weatherSelect = document.getElementById("checklistWeatherSelect");
    if (weatherSelect) weatherSelect.value = weatherKey;

    // Xác định transport mapping phù hợp
    const vTag = (vehicle || "").toLowerCase();
    let transportKey = "plane";
    if (vTag.includes("máy") || vTag.includes("phượt")) {
        transportKey = "motorbike";
    } else if (vTag.includes("ô tô") || vTag.includes("khách") || vTag.includes("xe") || vTag.includes("car")) {
        transportKey = "car";
    }
    const transportSelect = document.getElementById("checklistTransportSelect");
    if (transportSelect) transportSelect.value = transportKey;

    // 1. Thử tải checklist từ Database của chuyến đi này
    let dbItems = [];
    try {
        const res = await fetch(`/api/trips/${window.currentChecklistTripId}/checklist`);
        if (res.ok) {
            dbItems = await res.json();
        }
    } catch(e) {
        console.warn("[Checklist] DB load notice:", e);
    }

    const weatherGroup = document.getElementById("weatherChecklistItems");
    const transportGroup = document.getElementById("transportChecklistItems");
    const techGroup = document.getElementById("techChecklistItems");

    if (dbItems && dbItems.length > 0) {
        // Phân loại items từ DB theo 3 nhóm
        let wHtml = "", tHtml = "", techHtml = "";
        dbItems.forEach(it => {
            const cat = (it.category || "").toLowerCase();
            if (cat.includes("thời tiết") || cat.includes("weather")) {
                wHtml += renderChecklistItemHTML(it);
            } else if (cat.includes("giấy tờ") || cat.includes("phương tiện") || cat.includes("transport")) {
                tHtml += renderChecklistItemHTML(it);
            } else {
                techHtml += renderChecklistItemHTML(it);
            }
        });
        if (weatherGroup) weatherGroup.innerHTML = wHtml || (CHECKLIST_DB[weatherKey] || []).map(renderChecklistItemHTML).join("");
        if (transportGroup) transportGroup.innerHTML = tHtml || (CHECKLIST_DB[transportKey] || []).map(renderChecklistItemHTML).join("");
        if (techGroup) techGroup.innerHTML = techHtml || (CHECKLIST_DB.tech || []).map(renderChecklistItemHTML).join("");
    } else {
        // Khởi tạo checklist ban đầu từ Rule Engine
        const wItems = (CHECKLIST_DB[weatherKey] || []).map(it => ({ ...it, category: "Theo Thời Tiết Điểm Đến" }));
        const tItems = (CHECKLIST_DB[transportKey] || []).map(it => ({ ...it, category: "Giấy Tờ & Phương Tiện" }));
        const techItems = (CHECKLIST_DB.tech || []).map(it => ({ ...it, category: "Công Nghệ & Đồ Cá Nhân" }));

        if (weatherGroup) weatherGroup.innerHTML = wItems.map(renderChecklistItemHTML).join("");
        if (transportGroup) transportGroup.innerHTML = tItems.map(renderChecklistItemHTML).join("");
        if (techGroup) techGroup.innerHTML = techItems.map(renderChecklistItemHTML).join("");

        // Lưu danh sách ban đầu vào CSDL chuyến đi
        const allInitial = [...wItems, ...tItems, ...techItems];
        saveTripChecklistBulk(window.currentChecklistTripId, allInitial);
    }

    updateChecklistProgress();
}
window.renderTripChecklist = renderTripChecklist;

async function saveTripChecklistBulk(tripId, items) {
    if (!tripId || !items || !items.length) return;
    try {
        await fetch(`/api/trips/${tripId}/checklist/bulk`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items: items })
        });
    } catch(e) {
        console.warn("[Checklist] Bulk save notice:", e);
    }
}

window.toggleChecklistItemStatus = function(checkbox, itemId) {
    const parent = checkbox.closest(".check-item");
    if (checkbox.checked) {
        if (parent) parent.classList.add("completed");
    } else {
        if (parent) parent.classList.remove("completed");
    }
    updateChecklistProgress();

    // Lưu trạng thái vào CSDL
    if (itemId && !itemId.startsWith("chk_")) {
        fetch(`/api/checklist/${itemId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_completed: checkbox.checked })
        }).catch(e => console.warn(e));
    }
};

window.deleteChecklistItemUI = function(event, itemId, btn) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const parent = btn ? btn.closest(".check-item") : null;
    if (parent) parent.remove();
    updateChecklistProgress();
    showToast("🗑️ Đã xóa món đồ khỏi Checklist!");

    if (itemId && !itemId.startsWith("chk_")) {
        fetch(`/api/checklist/${itemId}`, {
            method: "DELETE"
        }).catch(e => console.warn(e));
    }
};

window.addNewChecklistItem = function() {
    const addInput = document.getElementById("customChecklistInput");
    if (!addInput) return;
    const val = addInput.value.trim();
    if (!val) {
        addInput.focus();
        return;
    }

    const tempId = "chk_" + Date.now();
    const newItem = {
        id: tempId,
        item_name: val,
        category: "Công Nghệ & Đồ Cá Nhân",
        is_completed: 0
    };

    // Thêm ngay lập tức lên bảng Checklist
    let targetGroup = document.getElementById("techChecklistItems");
    if (!targetGroup) targetGroup = document.getElementById("weatherChecklistItems");
    if (!targetGroup) targetGroup = document.getElementById("transportChecklistItems");
    if (!targetGroup) targetGroup = document.querySelector(".checklist-items");

    if (targetGroup) {
        targetGroup.insertAdjacentHTML("beforeend", renderChecklistItemHTML(newItem));
    }

    addInput.value = "";
    addInput.focus();
    updateChecklistProgress();
    showToast(`✅ Đã thêm "${val}" vào Checklist!`);

    // Lưu vào CSDL riêng của chuyến đi
    const tripId = window.currentChecklistTripId || "default_trip";
    fetch(`/api/trips/${tripId}/checklist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newItem)
    }).then(r => r.json()).then(data => {
        if (data && data.id) {
            const addedLabel = document.querySelector(`.check-item[data-id="${tempId}"]`);
            if (addedLabel) {
                addedLabel.setAttribute("data-id", data.id);
                const chk = addedLabel.querySelector('input[type="checkbox"]');
                if (chk) chk.setAttribute("onchange", `toggleChecklistItemStatus(this, '${data.id}')`);
                const delBtn = addedLabel.querySelector('.chk-del-btn');
                if (delBtn) delBtn.setAttribute("onclick", `deleteChecklistItemUI(event, '${data.id}', this)`);
            }
        }
    }).catch(e => console.warn(e));
};

function initChecklistEvents() {
    updateChecklistProgress();

    const addBtn = document.getElementById("addChecklistBtn");
    const addInput = document.getElementById("customChecklistInput");

    if (addBtn) {
        addBtn.onclick = function(e) {
            e.preventDefault();
            addNewChecklistItem();
        };
    }

    if (addInput) {
        addInput.onkeydown = function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                addNewChecklistItem();
            }
        };
    }
}

window.updateChecklistMapping = function () {
    const weatherVal = document.getElementById("checklistWeatherSelect").value;
    const transportVal = document.getElementById("checklistTransportSelect").value;

    const weatherGroup = document.getElementById("weatherChecklistItems");
    const transportGroup = document.getElementById("transportChecklistItems");

    if (weatherGroup && CHECKLIST_DB[weatherVal]) {
        weatherGroup.innerHTML = CHECKLIST_DB[weatherVal].map(it => renderChecklistItemHTML({ ...it, category: "Theo Thời Tiết Điểm Đến" })).join("");
    }

    if (transportGroup && CHECKLIST_DB[transportVal]) {
        transportGroup.innerHTML = CHECKLIST_DB[transportVal].map(it => renderChecklistItemHTML({ ...it, category: "Giấy Tờ & Phương Tiện" })).join("");
    }

    updateChecklistProgress();
    showToast("⚡ AI Rule Engine đã cập nhật checklist đồ dùng!");

    // Đồng bộ lại vào CSDL của chuyến đi
    if (window.currentChecklistTripId) {
        const allItems = [];
        document.querySelectorAll(".checklist-items .check-item").forEach(itemEl => {
            const txt = itemEl.querySelector("span")?.textContent || "";
            const isComp = itemEl.classList.contains("completed") || itemEl.querySelector("input")?.checked;
            const cat = itemEl.closest(".checklist-group")?.querySelector(".group-title")?.textContent.trim() || "Đồ dùng";
            allItems.push({
                item_name: txt,
                category: cat,
                is_completed: isComp ? 1 : 0
            });
        });
        saveTripChecklistBulk(window.currentChecklistTripId, allItems);
    }
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
    const percentage = total > 0 ? Math.round((checkedCount / total) * 100) : 0;

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

window.saveCurrentTripToJournal = async function () {
    if (!window.currentUser) {
        showToast("🔐 Vui lòng đăng nhập để lưu chuyến đi vào Nhật Ký Cá Nhân!");
        window.openAuthModal('login');
        return;
    }

    // 1. Lấy thông tin chuyến đi đang hiển thị
    const currentData = window.currentAiData || {};
    const dest = document.getElementById("itinerarySectionTitle")?.textContent || "Chuyến đi mới";
    const costText = document.getElementById("costAmountText")?.textContent || "0";
    const weatherText = document.getElementById("weatherDesc")?.textContent || "Nắng ráo";
    
    let budgetNum = 0;
    try {
        budgetNum = parseFloat(costText.replace(/\D/g, '')) || 0;
    } catch(e) {}

    // 2. Thu thập danh sách checklist hiện tại ứng với chuyến đi
    const currentChecklist = [];
    document.querySelectorAll(".checklist-items .check-item").forEach(itemEl => {
        const txt = itemEl.querySelector("span")?.textContent?.trim() || "";
        const isComp = itemEl.classList.contains("completed") || !!itemEl.querySelector("input")?.checked;
        const cat = itemEl.closest(".checklist-group")?.querySelector(".group-title")?.textContent?.trim() || "Hành trang";
        const itemId = itemEl.getAttribute("data-id") || "";
        if (txt) {
            currentChecklist.push({
                id: itemId,
                name: txt,
                item_name: txt,
                category: cat,
                checked: isComp,
                is_completed: isComp ? 1 : 0
            });
        }
    });

    const destinationClean = dest.replace(/^Lịch Trình Chi Tiết\s*•?\s*/i, '')
                                 .replace(/^Lịch Trình\s*•?\s*/i, '')
                                 .replace(/^Khám phá tuyệt tác\s*/i, '')
                                 .replace(/^Khám phá\s*/i, '')
                                 .replace(/\(.*?\)/g, '')
                                 .split('•')[0]
                                 .trim() || 'Việt Nam';
    const daysList = currentData.lich_trinh || [];

    try {
        // 3. Lưu chuyến đi vào CSDL SQLite Nhật Ký Cá Nhân
        const res = await fetch('/api/trips', {
            method: 'POST',
            headers: window.getAuthHeaders(),
            body: JSON.stringify({
                title: dest,
                destination: destinationClean,
                budget_limit: budgetNum,
                number_of_days: daysList.length || 3,
                days: daysList
            })
        });

        if (res.ok) {
            const savedTrip = await res.json();
            const tripId = (savedTrip && savedTrip.id) ? savedTrip.id : (window.currentChecklistTripId || `trip_${Date.now()}`);
            window.currentChecklistTripId = tripId;

            // Lưu danh sách checklist vào CSDL cho chuyến đi này
            if (currentChecklist.length > 0) {
                fetch(`/api/trips/${tripId}/checklist/bulk`, {
                    method: 'POST',
                    headers: window.getAuthHeaders(),
                    body: JSON.stringify({ items: currentChecklist })
                }).catch(e => console.warn("Lỗi lưu checklist bulk:", e));
            }

            // 4. LƯU VÀO BALO HÀNH TRANG (Chỉ chứa chuyến đi và checklist vừa lưu)
            window.currentBackpack = {
                tripId: tripId,
                title: dest,
                destination: destinationClean,
                cost: costText,
                weather: weatherText,
                days: daysList,
                checklist: currentChecklist
            };

            try {
                localStorage.setItem("beenavi_backpack", JSON.stringify(window.currentBackpack));
            } catch(e) {}

            renderBackpackUI();

            // Hiệu ứng nhấp nháy thu hút sự chú ý vào nút Balo
            const bpBtn = document.getElementById("backpackToggleBtn");
            if (bpBtn) {
                bpBtn.classList.add("pulse-anim");
                setTimeout(() => bpBtn.classList.remove("pulse-anim"), 2500);
            }

            showToast("🎒 Đã lưu lịch trình & checklist vào Balo và Nhật Ký Cá Nhân!");
            openZaloProfileModal('trips');
        } else {
            showToast("❌ Không thể lưu chuyến đi, vui lòng thử lại!");
        }
    } catch(e) {
        console.warn("Save trip error:", e);
        showToast("❌ Lỗi kết nối khi lưu chuyến đi!");
    }
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
    const viewJournal = document.getElementById("viewJournal");

    if (viewHome) viewHome.style.display = "none";
    if (viewItinerary) viewItinerary.style.display = "none";
    if (viewJournal) viewJournal.style.display = "none";

    // 3. Handle Home view (Logo click or Trang Chủ tab)
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
    } else if (tabKey === 'journal') {
        if (viewJournal) viewJournal.style.display = "block";
        if (typeof window.renderJournalView === 'function') {
            window.renderJournalView();
        }
        showToast("📖 Đã chuyển sang giao diện độc lập: Nhật Ký Hành Trình");
    }



    // Always scroll page to top on view switch

    window.scrollTo({ top: 0, behavior: 'smooth' });

};




// --- NEW AI ITINERARY LOGIC ---
async function generateItinerary(event) {
    if (event) event.preventDefault();

    if (!window.currentUser) {
        showToast("🔐 Vui lòng đăng nhập để sử dụng tính năng Tạo Lộ Trình AI!");
        window.openAuthModal('login');
        return;
    }

    // 1. Gather inputs
    const dest = document.getElementById('prefDestinationSelect')?.value || 'Đà Nẵng';
    const days = document.getElementById('prefDaysSelect')?.value || '3 Ngày 2 Đêm';
    const budget = document.getElementById('prefBudgetSelect')?.value || 'Tiết Kiệm';
    const style = document.getElementById('prefStyleSelect')?.value || 'Sống Ảo';
    const extraInput = document.getElementById('heroAiInput')?.value || '';

    const origin = "Hà Nội"; const transport = "Máy bay/Ô tô";
    const prompt = `Hãy LÊN LỊCH TRÌNH du lịch: Từ ${origin} đi ${dest}, thời gian ${days}, ngân sách ${budget}, phong cách ${style}. Yêu cầu thêm: ${extraInput}.

BẮT BUỘC TRẢ VỀ ĐÚNG CẤU TRÚC MARKDOWN DƯỚI ĐÂY (KHÔNG TRẢ VỀ JSON).
TUYỆT ĐỐI KHÔNG COPY LẠI PHẦN HƯỚNG DẪN TRONG NGOẶC. BẠN PHẢI CHỌN ĐỊA ĐIỂM TỪ PHẦN "GỢI Ý ĐỊA ĐIỂM" BÊN DƯỚI ĐỂ ĐIỀN VÀO.

[TIÊU ĐỀ] Khám phá tuyệt tác ${dest || 'Điểm đến'}
[TỔNG CHI PHÍ] ${budget || 'Ngân sách'} VNĐ
[CHI TIẾT CHI PHÍ] Di chuyển: ... | Khách sạn: ... | Ăn uống & Vé: ...
[THỜI TIẾT] Mùa này thời tiết (Điền thời tiết)

${buildDynamicDaysTemplate(parseInt(days) || 3)}
(CHỈ VIẾT ĐÚNG ${days || 3} NGÀY, KHI VIẾT XONG NGÀY ${days || 3} THÌ GHI [KẾT THÚC] VÀ DỪNG LẠI. 100% TIẾNG VIỆT, KHÔNG DÙNG KÝ TỰ TIẾNG TRUNG.)
`;

    // 2. Show loading overlay
    const overlay = document.getElementById('aiLoadingOverlay');
    if (overlay) overlay.style.display = 'flex';

    try {
        // 3. Call backend API
        const formData = new FormData();
        formData.append('message', prompt);

        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        const rawAnswer = data.answer || '';
        
        // 4. Parse JSON (handle markdown code block wrapping)
        const aiData = parseMarkdownToItineraryJSON(rawAnswer);
        
        // 5. Render to UI
        renderAIItinerary(aiData, dest, data.weather);

        // 6. Switch tab
        switchMainTab('itinerary', event);
    } catch (err) {
        console.error('Lỗi khi sinh lịch trình:', err);
        alert('Có lỗi xảy ra khi tạo lịch trình. Vui lòng thử lại sau.');
    } finally {
        if (overlay) overlay.style.display = 'none';
    }
}

async function generateItineraryFromTab(event) {
    if (event) event.preventDefault();

    if (!window.currentUser) {
        showToast("🔐 Vui lòng đăng nhập để sử dụng tính năng Tạo Lộ Trình AI!");
        window.openAuthModal('login');
        return;
    }

    // Gather inputs from the new Empty State form
    const origin = document.getElementById('itineraryFormOrigin')?.value || 'Hà Nội';
    const dest = document.getElementById('itineraryFormDest')?.value || 'Đà Nẵng';
    const days = document.getElementById('itineraryFormDays')?.value || '3 Ngày 2 Đêm';
    const budget = document.getElementById('itineraryFormBudget')?.value || '5000000';
    const transport = document.getElementById('itineraryFormTransport')?.value || 'Thuê xe máy tự lái';
    const style = document.getElementById('itineraryFormStyle')?.value || 'Khám Phá & Trải Nghiệm';
    const extraInput = document.getElementById('itineraryFormExtra')?.value || '';

    const prompt = `Hãy LÊN LỊCH TRÌNH du lịch: Từ ${origin} đi ${dest}, thời gian ${days}, ngân sách ${budget}, phong cách ${style}. Yêu cầu thêm: ${extraInput}.

BẮT BUỘC TRẢ VỀ ĐÚNG CẤU TRÚC MARKDOWN DƯỚI ĐÂY (KHÔNG TRẢ VỀ JSON).
TUYỆT ĐỐI KHÔNG COPY LẠI PHẦN HƯỚNG DẪN TRONG NGOẶC. BẠN PHẢI CHỌN ĐỊA ĐIỂM TỪ PHẦN "GỢI Ý ĐỊA ĐIỂM" BÊN DƯỚI ĐỂ ĐIỀN VÀO.

[TIÊU ĐỀ] Khám phá tuyệt tác ${dest || 'Điểm đến'}
[TỔNG CHI PHÍ] ${budget || 'Ngân sách'} VNĐ
[CHI TIẾT CHI PHÍ] Di chuyển: ... | Khách sạn: ... | Ăn uống & Vé: ...
[THỜI TIẾT] Mùa này thời tiết (Điền thời tiết)

${buildDynamicDaysTemplate(parseInt(days) || 3)}
(CHỈ VIẾT ĐÚNG ${days || 3} NGÀY, KHI VIẾT XONG NGÀY ${days || 3} THÌ GHI [KẾT THÚC] VÀ DỪNG LẠI. 100% TIẾNG VIỆT, KHÔNG DÙNG KÝ TỰ TIẾNG TRUNG.)
`;

    const overlay = document.getElementById('aiLoadingOverlay');
    if (overlay) overlay.style.display = 'flex';

    try {
        const formData = new FormData();
        formData.append('message', prompt);

        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        const rawAnswer = data.answer || '';
        
        const aiData = parseChopJSON(rawAnswer);
        
        const emptyState = document.getElementById('emptyItineraryState');
        const itContent = document.getElementById('itineraryContent');
        if (emptyState) emptyState.style.display = 'none';
        if (itContent) itContent.style.display = 'block';
        
        renderAIItinerary(aiData);
    } catch (err) {
        console.error('Lỗi khi sinh lịch trình:', err);
        alert('Có lỗi xảy ra khi tạo lịch trình. Vui lòng thử lại sau.');
    } finally {
        if (overlay) overlay.style.display = 'none';
    }
}


// ==========================================
// SEARCH DESTINATION INFO (HOMEPAGE)
// ==========================================
window.currentSearchDestination = "";

window.searchDestinationInfo = async function(event) {
    if (event) event.preventDefault();
    
    const inputEl = document.getElementById('homeSearchInput');
    const dest = inputEl.value.trim();
    if (!dest) {
        alert("Vui lòng nhập tên địa danh bạn muốn tìm hiểu.");
        return;
    }
    
    window.currentSearchDestination = dest;
    
    // Reset and show modal
    const modal = document.getElementById('destInfoModal');
    const loading = document.getElementById('destInfoLoading');
    const content = document.getElementById('destInfoContent');
    const title = document.getElementById('destInfoTitle');
    
    title.textContent = "Đang tra cứu: " + dest + "...";
    loading.style.display = "flex";
    content.style.display = "none";
    modal.style.display = "flex";
    
    const prompt = `Hãy LÊN LỊCH TRÌNH du lịch: Từ ${origin} đi ${dest}, thời gian ${days}, ngân sách ${budget}, phong cách ${style}. Yêu cầu thêm: ${extraInput}.

BẮT BUỘC TRẢ VỀ ĐÚNG CẤU TRÚC MARKDOWN DƯỚI ĐÂY (KHÔNG TRẢ VỀ JSON).
TUYỆT ĐỐI KHÔNG COPY LẠI PHẦN HƯỚNG DẪN TRONG NGOẶC. BẠN PHẢI CHỌN ĐỊA ĐIỂM TỪ PHẦN "GỢI Ý ĐỊA ĐIỂM" BÊN DƯỚI ĐỂ ĐIỀN VÀO.

[TIÊU ĐỀ] Khám phá tuyệt tác ${dest || 'Điểm đến'}
[TỔNG CHI PHÍ] ${budget || 'Ngân sách'} VNĐ
[CHI TIẾT CHI PHÍ] Di chuyển: ... | Khách sạn: ... | Ăn uống & Vé: ...
[THỜI TIẾT] Mùa này thời tiết (Điền thời tiết)

${buildDynamicDaysTemplate(parseInt(days) || 3)}
(CHỈ VIẾT ĐÚNG ${days || 3} NGÀY, KHI VIẾT XONG NGÀY ${days || 3} THÌ GHI [KẾT THÚC] VÀ DỪNG LẠI. 100% TIẾNG VIỆT, KHÔNG DÙNG KÝ TỰ TIẾNG TRUNG.)
`;

    try {
        const formData = new FormData();
        formData.append('message', prompt);
        
        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        const rawAnswer = data.answer || '';
        
        let jsonStr = rawAnswer;
        if (jsonStr.includes('```json')) {
            jsonStr = jsonStr.split('```json')[1].split('```')[0];
        } else if (jsonStr.includes('```')) {
            jsonStr = jsonStr.split('```')[1].split('```')[0];
        }
        
        const info = JSON.parse(jsonStr.trim());
        
        // Render
        title.textContent = info.tieu_de || dest;
        document.getElementById('destInfoWeather').textContent = info.thoi_tiet || "Quanh năm đều có vẻ đẹp riêng.";
        
        const expEl = document.getElementById('destInfoExperience');
        expEl.innerHTML = '';
        if (info.trai_nghiem && Array.isArray(info.trai_nghiem)) {
            info.trai_nghiem.forEach(item => {
                const li = document.createElement('li');
                li.style.marginBottom = '6px';
                li.textContent = item;
                expEl.appendChild(li);
            });
        }
        
        const foodEl = document.getElementById('destInfoFood');
        foodEl.innerHTML = '';
        if (info.dac_san && Array.isArray(info.dac_san)) {
            info.dac_san.forEach(item => {
                const li = document.createElement('li');
                li.style.marginBottom = '6px';
                li.textContent = item;
                foodEl.appendChild(li);
            });
        }
        
        loading.style.display = "none";
        content.style.display = "block";
        
    } catch (err) {
        console.error(err);
        loading.style.display = "none";
        title.textContent = "Lỗi khi tải thông tin";
        alert("Có lỗi xảy ra khi gọi AI. Hãy thử lại!");
        modal.style.display = "none";
    }
}

window.createTripFromInfo = function() {
    const dest = window.currentSearchDestination || "";
    // Đóng modal
    document.getElementById('destInfoModal').style.display = 'none';
    
    // Đổ dữ liệu vào Form Lộ Trình tab (V3 Form)
    const destInput = document.getElementById('itineraryFormDest');
    if (destInput) {
        destInput.value = dest;
    }
    
    // Chuyển tab
    window.switchMainTab('itinerary');
}

/* ==========================================================================
   Wizard Logic
   ========================================================================== */
let currentWizardStep = 1;
const totalWizardSteps = 4;

function navigateWizard(direction) {
    const newStep = currentWizardStep + direction;
    if (newStep < 1 || newStep > totalWizardSteps) return;

    // Optional validation logic here
    if (direction === 1 && currentWizardStep === 1) {
        if (!document.getElementById('wizOrigin').value || !document.getElementById('wizDest').value) {
            alert('Vui lòng nhập đầy đủ Điểm xuất phát và Điểm đến!');
            return;
        }
    }

    // Hide old step
    document.getElementById(`wizardStep${currentWizardStep}`).classList.remove('active');
    document.querySelector(`.wizard-step-indicator[data-step="${currentWizardStep}"]`).classList.remove('active');
    if (direction === 1) {
        document.querySelector(`.wizard-step-indicator[data-step="${currentWizardStep}"]`).classList.add('completed');
    } else {
        document.querySelector(`.wizard-step-indicator[data-step="${newStep}"]`).classList.remove('completed');
    }

    currentWizardStep = newStep;

    // Show new step
    document.getElementById(`wizardStep${currentWizardStep}`).classList.add('active');
    document.querySelector(`.wizard-step-indicator[data-step="${currentWizardStep}"]`).classList.add('active');

    // Update Progress Bar
    const progressPercent = ((currentWizardStep - 1) / (totalWizardSteps - 1)) * 100;
    document.getElementById('wizardProgressBar').style.width = `${progressPercent}%`;

    // Update Buttons
    document.getElementById('wizBtnBack').style.visibility = currentWizardStep === 1 ? 'hidden' : 'visible';
    
    if (currentWizardStep === totalWizardSteps) {
        document.getElementById('wizBtnNext').style.display = 'none';
        document.getElementById('wizBtnSubmit').style.display = 'block';
    } else {
        document.getElementById('wizBtnNext').style.display = 'block';
        document.getElementById('wizBtnSubmit').style.display = 'none';
    }
}

async function generateItineraryFromWizard(event) {
    if (event) event.preventDefault();

    if (!window.currentUser) {
        showToast("🔐 Vui lòng đăng nhập để sử dụng tính năng Tạo Lộ Trình AI!");
        window.openAuthModal('login');
        return;
    }

    // Bước 1
    const origin = document.getElementById('wizOrigin')?.value || 'Hồ Chí Minh';
    const dest = document.getElementById('wizDest')?.value || 'Hà Nội';
    const days = document.getElementById('wizDays')?.value || '3';
    const budget = document.getElementById('wizBudget')?.value || '5000000';
    const arrivalTime = document.getElementById('wizArrivalTime')?.value || '08:00';
    const departureTime = document.getElementById('wizDepartureTime')?.value || '18:00';

    // Bước 2
    const objective = document.getElementById('wizObjective')?.value || 'Khám phá';
    const shopping = document.getElementById('wizShopping')?.value || 'Bình thường';
    const nightlife = document.getElementById('wizNightlife')?.value || 'Cà phê, Chợ đêm';
    const photo = document.getElementById('wizPhotography')?.value || 'Bình thường';

    // Bước 3
    const memberCheckboxes = document.querySelectorAll('.wiz-member-chk:checked');
    const specialMembersArr = Array.from(memberCheckboxes).map(cb => cb.value);
    const specialMembers = specialMembersArr.join(', ');
    const diningConstraints = document.getElementById('wizDiningConstraints')?.value || '';
    const pace = document.getElementById('wizPacing')?.value || 'Cân bằng';

    // Bước 4
    const mustVisit = document.getElementById('wizMustVisit')?.value || '';
    const mustAvoid = document.getElementById('wizMustAvoid')?.value || '';
    const extra = document.getElementById('wizExtra')?.value || '';

    // MỚI: Build trip_data JSON for RuleEngine
    const tripData = {
        destination: dest,
        origin: origin,
        number_of_days: parseInt(days) || 3,
        budget_limit: parseInt(budget) || 99999999,
        trip_objective: objective,
        must_visit_places: mustVisit.split(',').map(s => s.trim()).filter(s => s),
        must_avoid_places: mustAvoid.split(',').map(s => s.trim()).filter(s => s),
        dining_constraints: diningConstraints.split(',').map(s => s.trim()).filter(s => s),
        special_members: specialMembersArr,
        photography_preference: photo,
        nightlife_preference: nightlife,
        shopping_interest: shopping
    };

    const prompt = `Hãy LÊN LỊCH TRÌNH du lịch thật chi tiết và hấp dẫn:
[THÔNG TIN CƠ BẢN]
- Điểm xuất phát: ${origin}
- Điểm đến: ${dest}
- Thời gian: ${days} ngày
- Ngân sách tổng: ${budget} VNĐ
- Mục tiêu chính: ${objective}

[RÀNG BUỘC]
- Giờ đến: ${arrivalTime} | Giờ về: ${departureTime}
- Bắt buộc đi: ${mustVisit || 'Không'}
- Tuyệt đối không đi: ${mustAvoid || 'Không'}
- Dị ứng/Kiêng cữ: ${diningConstraints || 'Không'}

[SỞ THÍCH & NHỊP ĐỘ]
- Nhịp độ: ${pace}
- Chụp ảnh: ${photo}
- Chơi đêm: ${nightlife}
- Mua sắm: ${shopping}

[SỨC KHỎE & ĐẶC BIỆT]
- Thành viên đặc biệt: ${specialMembers || 'Không có'}
- Ghi chú thêm: ${extra}

BẮT BUỘC TRẢ VỀ ĐÚNG CẤU TRÚC MARKDOWN DƯỚI ĐÂY (KHÔNG TRẢ VỀ JSON).
TUYỆT ĐỐI KHÔNG COPY LẠI PHẦN HƯỚNG DẪN TRONG NGOẶC. BẠN PHẢI CHỌN ĐỊA ĐIỂM TỪ PHẦN "GỢI Ý ĐỊA ĐIỂM" BÊN DƯỚI ĐỂ ĐIỀN VÀO.

[TIÊU ĐỀ] Khám phá tuyệt tác ${dest || 'Điểm đến'}
[TỔNG CHI PHÍ] ${budget || 'Ngân sách'} VNĐ
[CHI TIẾT CHI PHÍ] Di chuyển: ... | Khách sạn: ... | Ăn uống & Vé: ...
[THỜI TIẾT] Mùa này thời tiết (Điền thời tiết)

${buildDynamicDaysTemplate(parseInt(days) || 3)}
(CHỈ VIẾT ĐÚNG ${days || 3} NGÀY, KHI VIẾT XONG NGÀY ${days || 3} THÌ GHI [KẾT THÚC] VÀ DỪNG LẠI. 100% TIẾNG VIỆT, KHÔNG DÙNG KÝ TỰ TIẾNG TRUNG.)
`;

    const overlay = document.getElementById('aiLoadingOverlay');
    if (overlay) overlay.style.display = 'flex';

    try {
        const formData = new FormData();
        formData.append('message', prompt);
        formData.append('trip_data', JSON.stringify(tripData));

        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        const rawAnswer = data.answer || data.text || '';
        
        const aiData = parseMarkdownToItineraryJSON(rawAnswer);
        
        const emptyState = document.getElementById('emptyItineraryState');
        const itContent = document.getElementById('itineraryContent');
        if (emptyState) emptyState.style.display = 'none';
        if (itContent) itContent.style.display = 'block';
        
        if (data.weather) {
            updateWeatherUI(data.weather, dest);
            if (typeof leafletMap !== 'undefined' && leafletMap && data.weather.lat && data.weather.lon) {
                leafletMap.setView([data.weather.lat, data.weather.lon], 13);
            }
        }

        renderAIItinerary(aiData, dest, data.weather);
        saveItineraryToHistory(aiData);
    } catch (err) {
        console.error('Lỗi khi sinh lịch trình:', err);
        showToast('❌ Có lỗi xảy ra, vui lòng thử lại!');
    } finally {
        if (overlay) overlay.style.display = 'none';
    }
}

async function renderAIItinerary(aiData, destName = "", weatherObj = null) {
    window.currentAiData = aiData;
    // Cập nhật tiêu đề, chi phí
    const titleEl = document.getElementById("itinerarySectionTitle");
    const costAmount = document.getElementById("costAmountText");
    const costDetails = document.getElementById("costDetailsText");
    
    if (titleEl && aiData.tieu_de) titleEl.textContent = aiData.tieu_de;
    if (costAmount && aiData.tong_chi_phi) costAmount.textContent = aiData.tong_chi_phi;
    if (costDetails && aiData.chi_tiet_chi_phi_str) costDetails.textContent = aiData.chi_tiet_chi_phi_str;

    // Cập nhật thời tiết ứng với địa điểm đến
    if (weatherObj) {
        updateWeatherUI(weatherObj, destName);
    } else {
        let destToQuery = destName;
        if (!destToQuery && aiData.tieu_de) {
            destToQuery = aiData.tieu_de
                .replace(/^Lịch Trình Chi Tiết\s*•?\s*/i, "")
                .replace(/^Lịch Trình\s*•?\s*/i, "")
                .replace(/^Khám phá tuyệt tác\s*/i, "")
                .replace(/^Khám phá\s*/i, "")
                .replace(/\(.*?\)/g, "")
                .split("•")[0]
                .split("-")[0]
                .trim();
        }
        if (destToQuery) {
            fetchWeatherForCity(destToQuery);
        } else if (aiData.thoi_tiet) {
            const wDesc = document.getElementById("weatherDesc");
            if (wDesc) wDesc.textContent = aiData.thoi_tiet;
        }
    }

    // Build timeline
    const container = document.getElementById("timelineAccordionContainer");
    if (!container) return;
    
    let html = '';
    
    if (aiData.lich_trinh && Array.isArray(aiData.lich_trinh)) {
        aiData.lich_trinh.forEach((day, index) => {
            const isActive = index === 0 ? "active" : "";
            html += `
            <div class="day-accordion ${isActive}" data-day="${index+1}">
                <div class="day-header" onclick="toggleAccordion(this)">
                    <div class="day-title-group">
                        <div class="day-badge">${day.ngay || 'Ngày ' + (index+1)}</div>
                        <div class="day-info">
                            <h3>${day.tieu_de_ngay || 'Khám phá'}</h3>
                            <p>${day.hoat_dong ? day.hoat_dong.length : 0} địa điểm</p>
                        </div>
                    </div>
                    <div class="accordion-toggle-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    </div>
                </div>
                <div class="day-body">
                    <div class="activities-list">
            `;
            
            if (day.hoat_dong && Array.isArray(day.hoat_dong)) {
                day.hoat_dong.forEach(act => {
                    const safeTitle = (act.ten_diem || 'Địa điểm').replace(/'/g, "\\'");
                    const desc = act.chi_tiet || 'Trải nghiệm không gian du lịch văn hóa và thưởng thức phong cảnh đặc trưng tại địa phương.';
                    html += `
                        <div class="activity-card" style="cursor: pointer;" onclick="focusMapLocation(21.0285, 105.8542, '${safeTitle}')">
                            <div class="activity-time"><span class="time-badge">${act.gio || '08:00'}</span></div>
                            <div class="activity-icon-box">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            </div>
                            <div class="activity-content">
                                <div class="activity-title">${act.ten_diem || 'Địa điểm'} <span class="location-tag">📍 Xem vị trí & Chỉ đường</span></div>
                                <p class="activity-desc">${desc}</p>
                            </div>
                        </div>
                    `;
                });
            }
            
            html += `
                    </div>
                </div>
            </div>
            `;
        });
    }
    container.innerHTML = html;

    // Tự động kích hoạt và nạp Checklist tương ứng với chuyến đi
    const tripId = aiData.id || aiData.trip_id || `trip_${(destName || 'ai').toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    renderTripChecklist(tripId, destName, weatherObj?.weather_tag, aiData.phuong_tien);

    setTimeout(() => {
        if (typeof leafletMap !== 'undefined' && leafletMap) {
            leafletMap.invalidateSize();
        }
    }, 400);
}


async function generateItineraryFromTab(event) {
    if (event) event.preventDefault();

    if (!window.currentUser) {
        showToast("🔐 Vui lòng đăng nhập để sử dụng tính năng Tạo Lộ Trình AI!");
        window.openAuthModal('login');
        return;
    }

    // Gather inputs from the new Empty State form
    const origin = document.getElementById('itineraryFormOrigin')?.value || 'Hà Nội';
    const dest = document.getElementById('itineraryFormDest')?.value || 'Đà Nẵng';
    const days = document.getElementById('itineraryFormDays')?.value || '3 Ngày 2 Đêm';
    const budget = document.getElementById('itineraryFormBudget')?.value || '5000000';
    const transport = document.getElementById('itineraryFormTransport')?.value || 'Thuê xe máy tự lái';
    const style = document.getElementById('itineraryFormStyle')?.value || 'Khám Phá & Trải Nghiệm';
    const extraInput = document.getElementById('itineraryFormExtra')?.value || '';

    const prompt = `Hãy LÊN LỊCH TRÌNH du lịch: Từ ${origin} đi ${dest}, thời gian ${days}, ngân sách ${budget}, phong cách ${style}. Yêu cầu thêm: ${extraInput}.

BẮT BUỘC TRẢ VỀ ĐÚNG CẤU TRÚC MARKDOWN DƯỚI ĐÂY (KHÔNG TRẢ VỀ JSON).
TUYỆT ĐỐI KHÔNG COPY LẠI PHẦN HƯỚNG DẪN TRONG NGOẶC. BẠN PHẢI CHỌN ĐỊA ĐIỂM TỪ PHẦN "GỢI Ý ĐỊA ĐIỂM" BÊN DƯỚI ĐỂ ĐIỀN VÀO.

[TIÊU ĐỀ] Khám phá tuyệt tác ${dest || 'Điểm đến'}
[TỔNG CHI PHÍ] ${budget || 'Ngân sách'} VNĐ
[CHI TIẾT CHI PHÍ] Di chuyển: ... | Khách sạn: ... | Ăn uống & Vé: ...
[THỜI TIẾT] Mùa này thời tiết (Điền thời tiết)

${buildDynamicDaysTemplate(parseInt(days) || 3)}
(CHỈ VIẾT ĐÚNG ${days || 3} NGÀY, KHI VIẾT XONG NGÀY ${days || 3} THÌ GHI [KẾT THÚC] VÀ DỪNG LẠI. 100% TIẾNG VIỆT, KHÔNG DÙNG KÝ TỰ TIẾNG TRUNG.)
`;

    const overlay = document.getElementById('aiLoadingOverlay');
    if (overlay) overlay.style.display = 'flex';

    try {
        const formData = new FormData();
        formData.append('message', prompt);

        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        const rawAnswer = data.answer || '';
        
        const aiData = parseChopJSON(rawAnswer);
        
        const emptyState = document.getElementById('emptyItineraryState');
        const itContent = document.getElementById('itineraryContent');
        if (emptyState) emptyState.style.display = 'none';
        if (itContent) itContent.style.display = 'block';
        
        if (data.weather) {
            updateWeatherUI(data.weather, dest);
        }
        renderAIItinerary(aiData, dest, data.weather);
    } catch (err) {
        console.error('Lỗi khi sinh lịch trình:', err);
        alert('Có lỗi xảy ra khi tạo lịch trình. Vui lòng thử lại sau.');
    } finally {
        if (overlay) overlay.style.display = 'none';
    }
}


// ==========================================
// SEARCH DESTINATION INFO (HOMEPAGE)
// ==========================================
window.currentSearchDestination = "";

window.searchDestinationInfo = async function(event) {
    if (event) event.preventDefault();
    
    const inputEl = document.getElementById('homeSearchInput');
    const dest = inputEl.value.trim();
    if (!dest) {
        alert("Vui lòng nhập tên địa danh bạn muốn tìm hiểu.");
        return;
    }
    
    window.currentSearchDestination = dest;
    
    // Reset and show modal
    const modal = document.getElementById('destInfoModal');
    const loading = document.getElementById('destInfoLoading');
    const content = document.getElementById('destInfoContent');
    const title = document.getElementById('destInfoTitle');
    
    title.textContent = "Đang tra cứu: " + dest + "...";
    loading.style.display = "flex";
    content.style.display = "none";
    modal.style.display = "flex";
    
    const prompt = `Hãy LÊN LỊCH TRÌNH du lịch: Từ ${origin} đi ${dest}, thời gian ${days}, ngân sách ${budget}, phong cách ${style}. Yêu cầu thêm: ${extraInput}.

BẮT BUỘC TRẢ VỀ ĐÚNG CẤU TRÚC MARKDOWN DƯỚI ĐÂY (KHÔNG TRẢ VỀ JSON).
TUYỆT ĐỐI KHÔNG COPY LẠI PHẦN HƯỚNG DẪN TRONG NGOẶC. BẠN PHẢI CHỌN ĐỊA ĐIỂM TỪ PHẦN "GỢI Ý ĐỊA ĐIỂM" BÊN DƯỚI ĐỂ ĐIỀN VÀO.

[TIÊU ĐỀ] Khám phá tuyệt tác ${dest || 'Điểm đến'}
[TỔNG CHI PHÍ] ${budget || 'Ngân sách'} VNĐ
[CHI TIẾT CHI PHÍ] Di chuyển: ... | Khách sạn: ... | Ăn uống & Vé: ...
[THỜI TIẾT] Mùa này thời tiết (Điền thời tiết)

${buildDynamicDaysTemplate(parseInt(days) || 3)}
(CHỈ VIẾT ĐÚNG ${days || 3} NGÀY, KHI VIẾT XONG NGÀY ${days || 3} THÌ GHI [KẾT THÚC] VÀ DỪNG LẠI. 100% TIẾNG VIỆT, KHÔNG DÙNG KÝ TỰ TIẾNG TRUNG.)
`;

    try {
        const formData = new FormData();
        formData.append('message', prompt);
        
        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        const rawAnswer = data.answer || '';
        
        let jsonStr = rawAnswer;
        if (jsonStr.includes('```json')) {
            jsonStr = jsonStr.split('```json')[1].split('```')[0];
        } else if (jsonStr.includes('```')) {
            jsonStr = jsonStr.split('```')[1].split('```')[0];
        }
        
        const info = JSON.parse(jsonStr.trim());
        
        // Render
        title.textContent = info.tieu_de || dest;
        document.getElementById('destInfoWeather').textContent = info.thoi_tiet || "Quanh năm đều có vẻ đẹp riêng.";
        
        const expEl = document.getElementById('destInfoExperience');
        expEl.innerHTML = '';
        if (info.trai_nghiem && Array.isArray(info.trai_nghiem)) {
            info.trai_nghiem.forEach(item => {
                const li = document.createElement('li');
                li.style.marginBottom = '6px';
                li.textContent = item;
                expEl.appendChild(li);
            });
        }
        
        const foodEl = document.getElementById('destInfoFood');
        foodEl.innerHTML = '';
        if (info.dac_san && Array.isArray(info.dac_san)) {
            info.dac_san.forEach(item => {
                const li = document.createElement('li');
                li.style.marginBottom = '6px';
                li.textContent = item;
                foodEl.appendChild(li);
            });
        }
        
        loading.style.display = "none";
        content.style.display = "block";
        
    } catch (err) {
        console.error(err);
        loading.style.display = "none";
        title.textContent = "Lỗi khi tải thông tin";
        alert("Có lỗi xảy ra khi gọi AI. Hãy thử lại!");
        modal.style.display = "none";
    }
}

window.createTripFromInfo = function() {
    const dest = window.currentSearchDestination || "";
    // Đóng modal
    document.getElementById('destInfoModal').style.display = 'none';
    
    // Đổ dữ liệu vào Form Lộ Trình tab (V3 Form)
    const destInput = document.getElementById('itineraryFormDest');
    if (destInput) {
        destInput.value = dest;
    }
    
    // Chuyển tab
    window.switchMainTab('itinerary');
}


// BỘ PARSER CHUYỂN MARKDOWN THÀNH JSON THÔNG MINH
function parseMarkdownToItineraryJSON(mdText) {
    const aiData = {
        tieu_de: "Lịch trình Du lịch Tối ưu",
        tong_chi_phi: "",
        chi_tiet_chi_phi: [],
        chi_tiet_chi_phi_str: "",
        thoi_tiet: "Thời tiết lý tưởng cho chuyến đi",
        lich_trinh: []
    };

    try {
        // 1. Extract meta fields - Tiêu đề
        const titleMatch = mdText.match(/\[TIÊU ĐỀ\]\s*:?\s*(.*?)(?=\n|$)/i) ||
                           mdText.match(/\*\*\[?TIÊU ĐỀ\]?\*\*\s*:?\s*(.*?)(?=\n|$)/i) ||
                           mdText.match(/#+\s*([^\n]+(?:Khám phá|Lịch trình|Hành trình)[^\n]*)/i);
        if (titleMatch) aiData.tieu_de = titleMatch[1].replace(/\[|\]|\*\*/g, '').trim();
        
        // 2. Extract meta fields - Tổng chi phí
        const costMatch = mdText.match(/\[TỔNG CHI PHÍ\]\s*:?\s*(.*?)(?=\n|$)/i) ||
                          mdText.match(/\*\*\[?TỔNG CHI PHÍ\]?\*\*\s*:?\s*(.*?)(?=\n|$)/i) ||
                          mdText.match(/(?:Tổng chi phí|Chi phí ước tính|Dự toán chi phí|Chi phí dự kiến)\s*:?\s*([^\n]+)/i);
        if (costMatch) {
            let cStr = costMatch[1].replace(/\[|\]|\*\*/g, '').trim();
            if (cStr && !cStr.toLowerCase().includes("tính toán")) {
                aiData.tong_chi_phi = cStr;
            }
        }
        
        // 3. Extract meta fields - Chi tiết chi phí
        const costDetailsMatch = mdText.match(/\[CHI TIẾT CHI PHÍ\]\s*:?\s*(.*?)(?=\n|$)/i) ||
                                 mdText.match(/\*\*\[?CHI TIẾT CHI PHÍ\]?\*\*\s*:?\s*(.*?)(?=\n|$)/i) ||
                                 mdText.match(/(?:Chi tiết chi phí|Các khoản chi)\s*:?\s*([^\n]+)/i);
        if (costDetailsMatch) {
            let cdStr = costDetailsMatch[1].replace(/\[|\]|\*\*/g, '').trim();
            aiData.chi_tiet_chi_phi_str = cdStr;
            aiData.chi_tiet_chi_phi = cdStr.split('|').map(s => s.trim());
        }
        
        // 4. Extract meta fields - Thời tiết
        const weatherMatch = mdText.match(/\[THỜI TIẾT\]\s*:?\s*(.*?)(?=\n|$)/i) ||
                             mdText.match(/\*\*\[?THỜI TIẾT\]?\*\*\s*:?\s*(.*?)(?=\n|$)/i);
        if (weatherMatch) aiData.thoi_tiet = weatherMatch[1].replace(/\[|\]|\*\*/g, '').trim();

        // Parse days using split
        const daysRaw = mdText.split(/#\s*NGÀY/i);
        
        for (let i = 1; i < daysRaw.length; i++) {
            const dayContent = daysRaw[i].trim();
            const lines = dayContent.split('\n');
            
            const firstLine = lines[0].trim();
            const colonIdx = firstLine.indexOf(':');
            let dayTitle = colonIdx !== -1 ? firstLine.substring(colonIdx + 1).trim() : "Khám phá";
            dayTitle = dayTitle.replace(/\[|\]|\(tiếp tục\)/gi, '').trim();
            
            // Tìm số ngày chuẩn (ví dụ: 1, 2, 3)
            const numMatch = firstLine.match(/(\d+)/);
            const dayNum = numMatch ? parseInt(numMatch[1]) : i;
            const dayLabel = "Ngày " + dayNum;
            
            // Tìm xem ngày này đã tồn tại trong danh sách chưa (để gộp hoạt động lại)
            let dayObj = aiData.lich_trinh.find(d => d.ngay === dayLabel);
            if (!dayObj) {
                dayObj = {
                    ngay: dayLabel,
                    tieu_de_ngay: dayTitle || "Khám phá & Trải nghiệm",
                    hoat_dong: []
                };
                aiData.lich_trinh.push(dayObj);
            }
            
            // Parse activities
            for (let j = 1; j < lines.length; j++) {
                const line = lines[j].trim();
                if (line.startsWith('-')) {
                    const parts = line.substring(1).split('|').map(s => s.trim());
                    if (parts.length >= 2) {
                        let timeStr = (parts[0] || '08:00').replace(/\*\*/g, '').trim();
                        let placeStr = (parts[1] || 'Điểm tham quan')
                            .replace(/\[|\]|\*\*/g, '')
                            .replace(/-?\s*(Hoạt động|Ăn|Khám phá|Trải nghiệm)?\s*(Sáng|Trưa|Chiều|Tối)/gi, '')
                            .trim();
                        let descStr = parts.slice(2).join(' | ')
                            .replace(/\[|\]|\*\*/g, '')
                            .trim();
                            
                        // Không giới hạn số lượng hoạt động, cho phép xuyên suốt sáng tới đêm
                        const isDuplicate = dayObj.hoat_dong.some(a => a.ten_diem.toLowerCase() === placeStr.toLowerCase());
                        if (placeStr && !isDuplicate) {
                            dayObj.hoat_dong.push({
                                gio: timeStr,
                                ten_diem: placeStr,
                                chi_tiet: descStr
                            });
                        }
                    }
                }
            }
        }
        
        // Sắp xếp lại thứ tự các ngày (Ngày 1 -> Ngày 2 -> Ngày 3)
        aiData.lich_trinh.sort((a, b) => {
            const numA = parseInt(a.ngay.replace(/\D/g, '')) || 0;
            const numB = parseInt(b.ngay.replace(/\D/g, '')) || 0;
            return numA - numB;
        });

        // Giới hạn đúng số ngày (ví dụ 3 ngày thì chỉ lấy tối đa 3 ngày đầu)
        if (aiData.lich_trinh.length > 5) {
            aiData.lich_trinh = aiData.lich_trinh.slice(0, 5);
        }

        // Fallback ngày nếu rỗng
        if (aiData.lich_trinh.length === 0) {
            aiData.lich_trinh.push({
                ngay: "Ngày 1",
                tieu_de_ngay: "Lộ trình AI",
                hoat_dong: [{ gio: "08:00", ten_diem: "Lộ trình chi tiết", chi_tiet: mdText }]
            });
        }

        // 5. Tự động chuẩn hóa và tính toán Chi Phí chuẩn xác nếu AI không sinh đủ
        const totalDays = aiData.lich_trinh.length || 3;
        if (!aiData.tong_chi_phi || aiData.tong_chi_phi.includes("tính toán") || aiData.tong_chi_phi.length < 3) {
            const inputBudget = document.getElementById('itineraryFormBudget')?.value ||
                                document.getElementById('prefBudgetSelect')?.value;
            let calculatedCost = 0;
            if (inputBudget && !isNaN(parseInt(inputBudget)) && parseInt(inputBudget) > 100000) {
                calculatedCost = parseInt(inputBudget);
            } else if (inputBudget && inputBudget.toLowerCase().includes("tiết kiệm")) {
                calculatedCost = totalDays * 850000;
            } else if (inputBudget && inputBudget.toLowerCase().includes("sang")) {
                calculatedCost = totalDays * 2200000;
            } else {
                calculatedCost = totalDays * 1150000;
            }
            aiData.tong_chi_phi = `${calculatedCost.toLocaleString('vi-VN')} VNĐ / người`;
            
            const hotelCost = Math.round(calculatedCost * 0.40 / 1000) * 1000;
            const foodCost = Math.round(calculatedCost * 0.35 / 1000) * 1000;
            const ticketCost = calculatedCost - hotelCost - foodCost;
            aiData.chi_tiet_chi_phi_str = `Khách sạn: ${(hotelCost/1000).toLocaleString('vi-VN')}k • Ăn uống: ${(foodCost/1000).toLocaleString('vi-VN')}k • Vé & Xe: ${(ticketCost/1000).toLocaleString('vi-VN')}k`;
        } else {
            if (!aiData.tong_chi_phi.toLowerCase().includes("vnđ") && !aiData.tong_chi_phi.toLowerCase().includes("đ")) {
                aiData.tong_chi_phi += " VNĐ / người";
            }
            if (!aiData.chi_tiet_chi_phi_str) {
                const numOnly = parseInt(aiData.tong_chi_phi.replace(/\D/g, '')) || (totalDays * 1150000);
                const hotelCost = Math.round(numOnly * 0.40 / 1000) * 1000;
                const foodCost = Math.round(numOnly * 0.35 / 1000) * 1000;
                const ticketCost = numOnly - hotelCost - foodCost;
                aiData.chi_tiet_chi_phi_str = `Khách sạn: ${(hotelCost/1000).toLocaleString('vi-VN')}k • Ăn uống: ${(foodCost/1000).toLocaleString('vi-VN')}k • Vé & Xe: ${(ticketCost/1000).toLocaleString('vi-VN')}k`;
            }
        }
    } catch (e) {
        console.error("Markdown Parser Error:", e);
    }

    return aiData;
}


// ==========================================================================
// Itinerary History Functions (LocalStorage)
// ==========================================================================
const HISTORY_KEY = 'beeNavi_ItineraryHistory';

function saveItineraryToHistory(aiData) {
    if (!aiData || !aiData.lich_trinh || aiData.lich_trinh.length === 0) return;
    
    try {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        
        // Add new item with timestamp and unique ID
        const newItem = {
            id: 'trip_' + Date.now(),
            timestamp: Date.now(),
            data: aiData
        };
        
        history.unshift(newItem); // Add to beginning
        
        // Limit to 20 items to avoid localStorage bloat
        if (history.length > 20) {
            history = history.slice(0, 20);
        }
        
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
        console.error("Lỗi khi lưu lịch sử:", e);
    }
}

window.showHistoryModal = function() {
    const modal = document.getElementById('historyModal');
    if (modal) modal.style.display = 'flex';
    renderHistoryList();
}

window.hideHistoryModal = function() {
    const modal = document.getElementById('historyModal');
    if (modal) modal.style.display = 'none';
}

function renderHistoryList() {
    const body = document.getElementById('historyModalBody');
    if (!body) return;
    
    try {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        
        if (history.length === 0) {
            body.innerHTML = '<div class="history-empty">Chưa có lịch sử lộ trình nào. Hãy tạo một lộ trình mới!</div>';
            return;
        }
        
        let html = '';
        history.forEach(item => {
            const dateStr = new Date(item.timestamp).toLocaleString('vi-VN');
            const title = item.data.tieu_de || 'Lộ trình AI';
            const daysCount = item.data.lich_trinh ? item.data.lich_trinh.length : 0;
            const cost = item.data.tong_chi_phi || 'Chưa rõ chi phí';
            
            html += `
                <div class="history-item" id="${item.id}">
                    <div class="history-item-info">
                        <h4>${title}</h4>
                        <p>🕒 ${dateStr} • ${daysCount} Ngày • ${cost}</p>
                    </div>
                    <div class="history-item-actions">
                        <button class="btn-history-restore" onclick="restoreHistoryItinerary('${item.id}')">Xem lại</button>
                        <button class="btn-history-delete" onclick="deleteHistoryItinerary('${item.id}')">Xóa</button>
                    </div>
                </div>
            `;
        });
        
        body.innerHTML = html;
    } catch (e) {
        body.innerHTML = '<div class="history-empty">Lỗi khi tải lịch sử.</div>';
    }
}

window.restoreHistoryItinerary = function(id) {
    try {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        const item = history.find(h => h.id === id);
        if (item && item.data) {
            hideHistoryModal();
            
            const emptyState = document.getElementById('emptyItineraryState');
            const itContent = document.getElementById('itineraryContent');
            if (emptyState) emptyState.style.display = 'none';
            if (itContent) itContent.style.display = 'block';
            
            renderAIItinerary(item.data);
            
            // Switch to AI tab if not already there
            document.querySelectorAll('.trv-link').forEach(l => l.classList.remove('active'));
            document.querySelector('.trv-link[onclick*="ai"]').classList.add('active');
            document.querySelectorAll('.trv-tab-content').forEach(c => c.style.display = 'none');
            document.getElementById('aiContent').style.display = 'block';
        }
    } catch (e) {
        console.error(e);
        alert("Không thể khôi phục lộ trình này.");
    }
}

window.deleteHistoryItinerary = function(id) {
    if (!confirm("Bạn có chắc chắn muốn xóa lộ trình này khỏi lịch sử?")) return;
    
    try {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        history = history.filter(h => h.id !== id);
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        
        // Remove from DOM with animation
        const itemEl = document.getElementById(id);
        if (itemEl) {
            itemEl.style.opacity = '0';
            setTimeout(() => {
                renderHistoryList();
            }, 300);
        } else {
            renderHistoryList();
        }
    } catch (e) {
        console.error(e);
    }
}

// ===== RESET TO WIZARD =====
function resetToWizard() {
    const emptyState = document.getElementById('emptyItineraryState');
    const contentState = document.getElementById('itineraryContent');
    const chkSection = document.getElementById('checklistSection');
    if (emptyState) emptyState.style.display = 'block';
    if (contentState) contentState.style.display = 'none';
    if (chkSection) chkSection.style.display = 'none';
    
    // Cuộn lên đầu trang
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
window.resetToWizard = resetToWizard;

window.parseMarkdownToItineraryJSON = parseMarkdownToItineraryJSON;
window.renderAIItinerary = renderAIItinerary;
// ===== ITINERARY ADJUSTMENT =====
window.prepareItineraryAdjustment = function() {
    if (!window.currentAiData || !window.currentAiData.lich_trinh) {
        if (window.openDrawerWithPrompt) {
            window.openDrawerWithPrompt('Vui lòng tạo lịch trình trước khi yêu cầu điều chỉnh.');
        }
        return;
    }
    
    // Construct hidden context
    const contextStr = "[YÊU CẦU ĐIỀU CHỈNH LỊCH TRÌNH]\nDưới đây là lịch trình hiện tại của tôi:\n" + JSON.stringify(window.currentAiData.lich_trinh);
    
    // Open Drawer
    if (typeof cbOpen === 'function') cbOpen();
    
    const input = document.getElementById("cbInput");
    if (input) {
        input.value = "Thêm địa điểm ăn tối vào ngày 1"; // ví dụ
        input.focus();
    }
    
    window.isItineraryAdjustmentMode = true;
    window.hiddenItineraryContext = contextStr;
    
    if (typeof cbAddMsg === 'function') {
        cbAddMsg("bot", "Tôi đã ghi nhận Lịch trình hiện tại. Bạn muốn thay đổi điều gì? (Ví dụ: Thêm điểm ăn tối, bỏ điểm tham quan buổi chiều...)");
    }
}

/* ============================================================
   INTERACTIVE ITINERARY PROPOSAL & SYNC HANDLERS
   ============================================================ */

window.pendingItineraryProposals = {};

window.confirmItineraryProposal = async function(proposalId) {
    const aiData = window.pendingItineraryProposals ? window.pendingItineraryProposals[proposalId] : null;
    const actionsEl = document.getElementById(`actions_${proposalId}`);

    if (actionsEl) {
        actionsEl.innerHTML = `
            <div class="proposal-status-confirmed">
                <span>✅ Đã xác nhận & Cập nhật CSDL</span>
            </div>
        `;
    }

    if (!aiData) {
        if (typeof showToast === 'function') showToast("⚠️ Không tìm thấy dữ liệu đề xuất.");
        return;
    }

    // 1. Cập nhật giao diện Lộ trình & Bản đồ Leaflet
    if (typeof window.renderAIItinerary === 'function') {
        window.renderAIItinerary(aiData);
    }

    // 2. Lưu/Đồng bộ vào SQLite Database
    try {
        const token = window.getAuthToken ? window.getAuthToken() : null;
        const res = await fetch('/api/trips/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
            },
            body: JSON.stringify(aiData)
        });
        if (res.ok) {
            if (typeof window.renderJournalView === 'function') {
                window.renderJournalView();
            }
            if (typeof showToast === 'function') {
                showToast("🎉 Đã cập nhật & lưu đồng bộ vào CSDL thành công!");
            }
        }
    } catch (e) {
        console.error("Sync Trip Error:", e);
    }

    if (typeof cbAddMsg === 'function') {
        cbAddMsg("bot", "🎉 Tuyệt vời! Tôi đã áp dụng các thay đổi lên màn hình Lộ Trình và lưu đồng bộ vào CSDL của bạn. Bạn có muốn hỏi thêm điều gì nữa không?");
    }
};

window.cancelItineraryProposal = function(proposalId) {
    const actionsEl = document.getElementById(`actions_${proposalId}`);
    if (actionsEl) {
        actionsEl.innerHTML = `
            <div class="proposal-status-cancelled">
                <span>❌ Đã hủy bỏ đề xuất - Giữ nguyên lộ trình cũ</span>
            </div>
        `;
    }
    if (typeof cbAddMsg === 'function') {
        cbAddMsg("bot", "👍 Đã giữ nguyên lộ trình ban đầu của bạn. Nếu cần thay đổi hay hỏi thêm bất kỳ điều gì, hãy cứ nhắn cho tôi nhé!");
    }
    if (typeof showToast === 'function') {
        showToast("👍 Giữ nguyên lộ trình hiện tại.");
    }
};


/* ==========================================================================
   MODULE: FLOATING BACKPACK (BALO HÀNH TRANG & LỘ TRÌNH GÓC TRÁI DƯỚI)
   ========================================================================== */

window.currentBackpack = {
    title: "",
    destination: "",
    cost: "",
    weather: "",
    days: [],
    checklist: []
};

// Khôi phục từ localStorage nếu có chuyến đi hợp lệ
try {
    const savedBp = localStorage.getItem("beenavi_backpack");
    if (savedBp) {
        const parsed = JSON.parse(savedBp);
        if (parsed && Array.isArray(parsed.days) && parsed.days.length > 0) {
            window.currentBackpack = parsed;
        }
    }
} catch (e) {
    console.error("Lỗi đọc balo từ localStorage", e);
}

window.toggleBackpackModal = function() {
    const drawer = document.getElementById("backpackDrawer");
    if (!drawer) return;
    if (drawer.style.display === "none" || drawer.style.display === "") {
        drawer.style.display = "flex";
        renderBackpackUI();
    } else {
        drawer.style.display = "none";
    }
};

window.switchBackpackTab = function(tabName) {
    const tabItinBtn = document.getElementById("bpTabItinerary");
    const tabChkBtn = document.getElementById("bpTabChecklist");
    const contentItin = document.getElementById("bpItineraryTabContent");
    const contentChk = document.getElementById("bpChecklistTabContent");

    if (tabName === "itinerary") {
        if (tabItinBtn) tabItinBtn.classList.add("active");
        if (tabChkBtn) tabChkBtn.classList.remove("active");
        if (contentItin) contentItin.style.display = "flex";
        if (contentChk) contentChk.style.display = "none";
    } else {
        if (tabChkBtn) tabChkBtn.classList.add("active");
        if (tabItinBtn) tabItinBtn.classList.remove("active");
        if (contentChk) contentChk.style.display = "flex";
        if (contentItin) contentItin.style.display = "none";
    }
};

window.updateBackpackData = function(itineraryData, checklistItems) {
    if (!itineraryData) return;

    if (itineraryData.title || itineraryData.tieu_de) {
        window.currentBackpack.title = itineraryData.title || itineraryData.tieu_de;
    }
    if (itineraryData.destination) {
        window.currentBackpack.destination = itineraryData.destination;
    }
    if (itineraryData.total_budget || itineraryData.tong_chi_phi) {
        const costVal = itineraryData.total_budget || itineraryData.tong_chi_phi;
        window.currentBackpack.cost = typeof costVal === "number" ? costVal.toLocaleString("vi-VN") + " đ" : costVal;
    }
    if (itineraryData.weather || itineraryData.thoi_tiet) {
        window.currentBackpack.weather = itineraryData.weather || itineraryData.thoi_tiet;
    }

    const days = itineraryData.days || itineraryData.lich_trinh || [];
    if (Array.isArray(days) && days.length > 0) {
        window.currentBackpack.days = days;
    }

    if (Array.isArray(checklistItems) && checklistItems.length > 0) {
        window.currentBackpack.checklist = checklistItems.map(item => ({
            name: typeof item === "string" ? item : (item.item_name || item.name),
            category: (item.category || "Hành trang"),
            checked: !!(item.is_packed || item.checked || item.is_completed)
        }));
    }

    try {
        localStorage.setItem("beenavi_backpack", JSON.stringify(window.currentBackpack));
    } catch (e) {}

    renderBackpackUI();
};

function renderBackpackUI() {
    const bp = window.currentBackpack;

    // Badge count
    const badge = document.getElementById("backpackBadge");
    const numDays = (bp.days && bp.days.length) || 0;
    const chkList = bp.checklist || [];
    if (badge) {
        badge.textContent = numDays > 0 ? `${numDays}N` : "0";
    }

    // Subtitle & Header
    const subTitle = document.getElementById("backpackSubtitle");
    if (subTitle) {
        subTitle.textContent = numDays > 0 ? `${bp.title} (${numDays} Ngày)` : "Lịch trình & Đồ dùng đã lưu của bạn";
    }

    const daysCount = document.getElementById("bpDaysCount");
    if (daysCount) daysCount.textContent = numDays;

    // Summary Card
    const tripTitle = document.getElementById("bpTripTitle");
    if (tripTitle) tripTitle.textContent = bp.title || "Chưa có lịch trình được lưu";

    const tripCost = document.getElementById("bpTripCost");
    if (tripCost) tripCost.textContent = `💰 Dự toán: ${bp.cost || "Chưa có"}`;

    const tripWeather = document.getElementById("bpTripWeather");
    if (tripWeather) tripWeather.textContent = `☀️ ${bp.weather || "Nắng ráo"}`;

    // Render Days List
    const daysList = document.getElementById("bpItineraryDaysList");
    if (daysList) {
        if (numDays === 0) {
            daysList.innerHTML = `
                <div class="bp-empty-state" style="text-align: center; padding: 32px 16px; color: var(--text-muted);">
                    <div style="font-size: 38px; margin-bottom: 8px;">🎒</div>
                    <h4 style="color: var(--text-main); font-size: 15px; margin: 0 0 6px;">Balo đang trống</h4>
                    <p style="font-size: 12.5px; line-height: 1.5; margin: 0;">Bấm nút <b>"Lưu Vào Nhật Ký Trong Trang Cá Nhân"</b> trên màn hình Lộ trình để lưu lịch trình và checklist vào Balo của bạn!</p>
                </div>
            `;
        } else {
            let html = "";
            bp.days.forEach((day, idx) => {
                const dayTitle = day.title || day.tieu_de_ngay || `Ngày ${idx + 1}`;
                const activities = day.activities || day.hoat_dong || [];
                html += `
                    <div class="bp-day-card">
                        <div class="bp-day-title">🗓️ ${day.day_number ? 'Ngày ' + day.day_number : (day.ngay || 'Ngày ' + (idx + 1))}: ${dayTitle}</div>
                `;
                activities.forEach(act => {
                    const time = act.time || act.thoi_gian || act.gio || "--:--";
                    const actTitle = act.title || act.dia_diem || act.ten_diem || act.hoat_dong || act;
                    html += `
                        <div class="bp-act-item">
                            <span class="bp-act-time">${time}</span>
                            <span>${actTitle}</span>
                        </div>
                    `;
                });
                html += `</div>`;
            });
            daysList.innerHTML = html;
        }
    }

    // Render Checklist & Progress
    const doneCount = chkList.filter(c => c.checked).length;
    const totalCount = chkList.length;
    const pct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

    const chkDoneEl = document.getElementById("bpChecklistDone");
    if (chkDoneEl) chkDoneEl.textContent = `${doneCount}/${totalCount}`;

    const progText = document.getElementById("bpProgressText");
    if (progText) progText.textContent = `${pct}% (${doneCount}/${totalCount} món)`;

    const progBar = document.getElementById("bpProgressBar");
    if (progBar) progBar.style.width = `${pct}%`;

    const chkListEl = document.getElementById("bpChecklistItemsList");
    if (chkListEl) {
        if (totalCount === 0) {
            chkListEl.innerHTML = `
                <div class="bp-empty-state" style="text-align: center; padding: 24px 16px; color: var(--text-muted);">
                    <p style="font-size: 12.5px; margin: 0;">Chưa có đồ dùng trong Balo. Hãy lưu lịch trình để tự động nạp checklist vào đây!</p>
                </div>
            `;
        } else {
            let chkHtml = "";
            chkList.forEach((item, idx) => {
                const isCompleted = item.checked ? "completed" : "";
                const isChecked = item.checked ? "checked" : "";
                chkHtml += `
                    <div class="bp-chk-item ${isCompleted}" onclick="toggleBackpackChecklistItem(${idx})">
                        <input type="checkbox" class="bp-chk-box" ${isChecked} onclick="event.stopPropagation(); toggleBackpackChecklistItem(${idx})">
                        <span class="bp-chk-name">${item.name}</span>
                        <span class="bp-chk-tag">${item.category || "Cần thiết"}</span>
                    </div>
                `;
            });
            chkListEl.innerHTML = chkHtml;
        }
    }
}

window.toggleBackpackChecklistItem = function(index) {
    if (!window.currentBackpack.checklist || !window.currentBackpack.checklist[index]) return;
    window.currentBackpack.checklist[index].checked = !window.currentBackpack.checklist[index].checked;
    try {
        localStorage.setItem("beenavi_backpack", JSON.stringify(window.currentBackpack));
    } catch (e) {}
    renderBackpackUI();
};

window.addCustomBackpackItem = function() {
    const input = document.getElementById("bpNewItemInput");
    if (!input) return;
    const val = input.value.trim();
    if (!val) return;

    if (!window.currentBackpack.checklist) window.currentBackpack.checklist = [];
    window.currentBackpack.checklist.unshift({
        name: val,
        category: "Cá nhân",
        checked: false
    });

    input.value = "";
    try {
        localStorage.setItem("beenavi_backpack", JSON.stringify(window.currentBackpack));
    } catch (e) {}
    renderBackpackUI();
};

window.pendingProposals = {};

window.confirmTripToBackpack = function(proposalId, btnEl) {
    const proposal = window.pendingProposals[proposalId];
    if (!proposal) {
        if (typeof showToast === 'function') showToast("⚠️ Không tìm thấy dữ liệu đề xuất!");
        return;
    }

    // 1. Cập nhật vào Balo
    if (window.updateBackpackData) {
        window.updateBackpackData(proposal.itinObj, proposal.smartChecklist);
    }
    if (window.renderAIItinerary) {
        window.renderAIItinerary(proposal.itinObj);
    }

    // Lưu vào CSDL Backend
    try {
        const tripPayload = {
            title: proposal.itinObj?.title || "Chuyến đi mới",
            destination: proposal.itinObj?.destination || "Điểm đến",
            number_of_days: proposal.itinObj?.days?.length || 3,
            budget_limit: proposal.budgetBreakdown?.total_estimated || proposal.itinObj?.total_budget || 0,
            days: proposal.itinObj?.days || []
        };
        fetch("/api/trips", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tripPayload)
        }).catch(() => {});
    } catch (e) {}

    // 2. Cập nhật giao diện nút
    if (btnEl) {
        btnEl.innerHTML = "✅ ĐÃ CHỐT ĐƠN & LƯU BALO";
        btnEl.style.background = "#059669";
        btnEl.style.color = "#FFFFFF";
        btnEl.disabled = true;
    }

    // 3. Thông báo cho người dùng
    if (typeof showToast === 'function') {
        showToast("🎉 Chúc mừng bạn đã chốt đơn chuyến đi! Lộ trình và hành trang đã lưu vào Balo.");
    }

    // 4. Mở Balo drawer để người dùng thấy thành quả
    setTimeout(() => {
        const drawer = document.getElementById("backpackDrawer");
        if (drawer) drawer.style.display = "block";
    }, 400);
};

window.requestTripAdjustment = function(promptText) {
    const input = document.getElementById("cbInput");
    if (input) {
        input.value = promptText || "Tôi muốn điều chỉnh: ";
        input.focus();
    }
};

window.syncBackpackToMap = function() {
    if (typeof switchMainTab === "function") {
        switchMainTab("itinerary");
    }
    const drawer = document.getElementById("backpackDrawer");
    if (drawer) drawer.style.display = "none";

    const bp = window.currentBackpack;
    if (bp && bp.days && bp.days.length > 0 && typeof renderAIItinerary === "function") {
        renderAIItinerary({
            tieu_de: bp.title,
            tong_chi_phi: bp.cost,
            thoi_tiet: bp.weather,
            lich_trinh: bp.days
        });
    }

    if (typeof showToast === "function") {
        showToast("📍 Đã đồng bộ lộ trình từ Balo lên Bản Đồ Live Map!");
    }
};

// Tự động nạp dữ liệu khởi tạo
document.addEventListener("DOMContentLoaded", function() {
    renderBackpackUI();
});


