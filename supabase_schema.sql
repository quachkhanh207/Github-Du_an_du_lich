-- ==============================================================================
-- 🐝 BEENAVI TRAVEL AI — CSDL SUPABASE (POSTGRESQL) - BẢN SỬA LỖI XUNG ĐỘT
-- ==============================================================================
-- Lưu ý: Bản này tự động xóa các bảng cũ bị lệch cấu trúc và tạo mới chuẩn 100%.
-- ==============================================================================

-- 0. KÍCH HOẠT EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- XÓA BẢNG CŨ (TRÁNH XUNG ĐỘT CỘT DỮ LIỆU CŨ)
DROP TABLE IF EXISTS public.photos CASCADE;
DROP TABLE IF EXISTS public.checklist_items CASCADE;
DROP TABLE IF EXISTS public.itineraries CASCADE;
DROP TABLE IF EXISTS public.trips CASCADE;
DROP TABLE IF EXISTS public.ai_itineraries CASCADE;
DROP TABLE IF EXISTS public.chat_messages CASCADE;
DROP TABLE IF EXISTS public.chat_sessions CASCADE;
DROP TABLE IF EXISTS public.user_feedbacks CASCADE;
DROP TABLE IF EXISTS public.announcements CASCADE;
DROP TABLE IF EXISTS public.pois CASCADE;
DROP TABLE IF EXISTS public.user_preferences CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- ==============================================================================
-- 1. PHÂN HỆ NGƯỜI DÙNG & HỒ SƠ (PROFILES & PREFERENCES)
-- ==============================================================================

CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    nickname TEXT,
    avatar_url TEXT,
    phone TEXT,
    gender TEXT,
    location TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE public.user_preferences (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    travel_style JSONB DEFAULT '[]'::jsonb,
    default_budget_tier TEXT DEFAULT 'Tiêu chuẩn',
    frequent_companion TEXT,
    food_allergies JSONB DEFAULT '[]'::jsonb,
    special_requirements JSONB DEFAULT '[]'::jsonb,
    niche_interests JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Trigger tự động tạo Profile khi User Đăng ký
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
        COALESCE(new.raw_user_meta_data->>'role', 'user')
    )
    ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name);

    INSERT INTO public.user_preferences (user_id)
    VALUES (new.id)
    ON CONFLICT (user_id) DO NOTHING;

    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- ==============================================================================
-- 2. PHÂN HỆ CHUYẾN ĐI & LỘ TRÌNH (TRIPS & ITINERARIES)
-- ==============================================================================

CREATE TABLE public.trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_location TEXT DEFAULT 'Hồ Chí Minh',
    start_date DATE,
    end_date DATE,
    number_of_days INTEGER DEFAULT 3,
    budget_limit NUMERIC DEFAULT 5000000,
    vehicle TEXT DEFAULT 'Máy bay',
    trip_type TEXT DEFAULT 'Khám phá',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    cover_image TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE public.itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
    days_data JSONB NOT NULL DEFAULT '[]'::jsonb,
    estimated_cost TEXT,
    cost_details TEXT,
    weather_info JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE public.ai_itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    destination TEXT NOT NULL,
    days INTEGER DEFAULT 3,
    style TEXT,
    budget TEXT,
    mode TEXT DEFAULT 'A',
    raw_result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 3. PHÂN HỆ CHECKLIST & ẢNH KỶ NIỆM (CHECKLIST & PHOTOS)
-- ==============================================================================

CREATE TABLE public.checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Đồ dùng chung',
    quantity INTEGER NOT NULL DEFAULT 1,
    priority TEXT NOT NULL DEFAULT 'Bắt buộc' CHECK (priority IN ('Bắt buộc', 'Nên có', 'Tùy chọn')),
    is_completed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE public.photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    caption TEXT,
    location_tag TEXT,
    taken_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 4. PHÂN HỆ HỘI THOẠI & TRỢ LÝ ẢO (CHAT SESSIONS & MESSAGES)
-- ==============================================================================

CREATE TABLE public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    audio_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 5. PHÂN HỆ PHẢN HỒI & THÔNG BÁO (FEEDBACKS & ANNOUNCEMENTS)
-- ==============================================================================

CREATE TABLE public.user_feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    user_email TEXT,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    category TEXT DEFAULT 'Trải nghiệm chung',
    comment TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE public.announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'info' CHECK (type IN ('info', 'warning', 'success', 'promo')),
    author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 6. PHÂN HỆ KHO DỮ LIỆU ĐỊA ĐIỂM DU LỊCH (POIS)
-- ==============================================================================

CREATE TABLE public.pois (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    address TEXT,
    province TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    description TEXT,
    image_url TEXT,
    price_range TEXT,
    opening_hours TEXT,
    rating DOUBLE PRECISION DEFAULT 4.5,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX idx_pois_name ON public.pois USING btree (name);
CREATE INDEX idx_pois_province ON public.pois USING btree (province);
CREATE INDEX idx_pois_category ON public.pois USING btree (category);
CREATE INDEX idx_pois_lat_lon ON public.pois USING btree (lat, lon);

-- ==============================================================================
-- 7. CẤU HÌNH SUPABASE STORAGE (BUCKETS)
-- ==============================================================================

INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('trip-photos', 'trip-photos', true),
    ('avatars', 'avatars', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- ==============================================================================
-- 8. THIẾT LẬP ROW LEVEL SECURITY (RLS) BẢO MẬT DỮ LIỆU
-- ==============================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.itineraries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_itineraries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.checklist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pois ENABLE ROW LEVEL SECURITY;

-- 8.1. Profiles
CREATE POLICY "Public profiles are viewable by everyone" ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- 8.2. Preferences
CREATE POLICY "Users can manage own preferences" ON public.user_preferences FOR ALL USING (auth.uid() = user_id);

-- 8.3. Trips & Itineraries
CREATE POLICY "Users can manage own trips" ON public.trips FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view itineraries of their trips" ON public.itineraries FOR ALL 
USING (EXISTS (SELECT 1 FROM public.trips WHERE trips.id = itineraries.trip_id AND trips.user_id = auth.uid()));

-- 8.4. Checklist & Photos
CREATE POLICY "Users can manage own checklist items" ON public.checklist_items FOR ALL 
USING (EXISTS (SELECT 1 FROM public.trips WHERE trips.id = checklist_items.trip_id AND trips.user_id = auth.uid()));
CREATE POLICY "Users can manage own photos" ON public.photos FOR ALL USING (auth.uid() = user_id);

-- 8.5. Chat Sessions & Messages
CREATE POLICY "Users can manage own chat sessions" ON public.chat_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own chat messages" ON public.chat_messages FOR ALL 
USING (EXISTS (SELECT 1 FROM public.chat_sessions WHERE chat_sessions.id = chat_messages.session_id AND chat_sessions.user_id = auth.uid()));

-- 8.6. Feedbacks & AI Itineraries
CREATE POLICY "Anyone can insert feedback" ON public.user_feedbacks FOR INSERT WITH CHECK (true);
CREATE POLICY "Admins or owners can view feedbacks" ON public.user_feedbacks FOR SELECT 
USING (auth.uid() = user_id OR EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));

CREATE POLICY "Anyone can create AI itinerary logs" ON public.ai_itineraries FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can view own AI itineraries" ON public.ai_itineraries FOR SELECT 
USING (auth.uid() = user_id OR user_id IS NULL OR EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));

-- 8.7. Announcements & POIs
CREATE POLICY "Announcements are viewable by everyone" ON public.announcements FOR SELECT USING (is_active = true);
CREATE POLICY "POIs are viewable by everyone" ON public.pois FOR SELECT USING (true);

-- ==============================================================================
-- 9. DỮ LIỆU MẪU BAN ĐẦU
-- ==============================================================================

INSERT INTO public.announcements (title, content, type, is_active)
VALUES 
    ('Chào mừng đến với BeeNavi AI v2.0! 🎉', 'Hệ thống đã nâng cấp thuật toán sinh lịch trình siêu tốc và hỗ trợ chế độ khám phá 2km.', 'success', true),
    ('Khám phá tính năng Checklist thông minh 🎒', 'Tự động gợi ý hành trang theo thời tiết thực tế và loại hình chuyến đi của bạn.', 'info', true);
