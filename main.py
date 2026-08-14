import cv2
import numpy as np
import mediapipe as mp
import math
import time
import screen_brightness_control as sbc

# --- MEDIAPIPE KURULUMU ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# --- DEĞİŞKENLER VE AYARLAR ---
draw_color = None  
brush_thickness = 5     # Çizimde kullanılan ASIL Genel Kalınlık
current_brightness = 50

# Ele özel (idx bazlı) takip sözlükleri
temp_thickness = {}          # {idx: değer}
is_adjusting_thickness = {}  # {idx: bool}

canvas = None

mode = "RENK SECILMEDI"
is_black_screen = False

black_screen_start_time = None
screenshot_start_time = None
show_ss_message_until = 0

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

hand_points = {}

# --- SLIDER (KAYDIRMA ÇUBUĞU) GEOMETRİSİ ---
slider_y_top = 130 # toplam boy 200  sol üst 0,0 alta doğru artar
slider_y_bottom = 330
slider_thickness_x = 45 
slider_brightness_x = 1235

def get_distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def get_finger_states(hand_landmarks):
    tips = [8, 12, 16, 20]
    mcp_joints = [6, 10, 14, 18]
    
    states = []
    thumb_tip = hand_landmarks.landmark[4]
    thumb_mcp = hand_landmarks.landmark[2]
    states.append(thumb_tip.y < thumb_mcp.y)
        
    for tip, mcp in zip(tips, mcp_joints):
        states.append(hand_landmarks.landmark[tip].y < hand_landmarks.landmark[mcp].y)
        
    return states

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    if canvas is None:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    btn_kirmizi = ((30, 10), (160, 65))
    btn_yesil   = ((190, 10), (320, 65))
    btn_mavi    = ((350, 10), (480, 65))
    btn_silgi   = ((510, 10), (640, 65))

    if not is_black_screen:
        cv2.rectangle(frame, btn_kirmizi[0], btn_kirmizi[1], (0, 0, 255), -1)
        cv2.putText(frame, "KIRMIZI", (50, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.rectangle(frame, btn_yesil[0], btn_yesil[1], (0, 255, 0), -1)
        cv2.putText(frame, "YESIL", (225, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        cv2.rectangle(frame, btn_mavi[0], btn_mavi[1], (255, 0, 0), -1)
        cv2.putText(frame, "MAVI", (385, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.rectangle(frame, btn_silgi[0], btn_silgi[1], (200, 200, 200), -1)
        cv2.putText(frame, "SILGI", (545, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # --- SLIDER 1: KALINLIK SCROLLBAR (SOL) ---
        cv2.line(frame, (slider_thickness_x, slider_y_top), (slider_thickness_x, slider_y_bottom), (70, 70, 70), 8)
        handle_thick_y = int(np.interp(brush_thickness, [1, 25], [slider_y_bottom, slider_y_top]))
        cv2.circle(frame, (slider_thickness_x, handle_thick_y), 13, (0, 255, 255), -1)
        cv2.circle(frame, (slider_thickness_x, handle_thick_y), 13, (255, 255, 255), 2)
        cv2.putText(frame, "KALINLIK", (slider_thickness_x - 35, slider_y_top - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        # --- SLIDER 2: PARLAKLIK SCROLLBAR (SAĞ) ---
        cv2.line(frame, (slider_brightness_x, slider_y_top), (slider_brightness_x, slider_y_bottom), (70, 70, 70), 8)
        try:
            b_list = sbc.get_brightness()
            current_brightness = b_list[0] if isinstance(b_list, list) else b_list
        except Exception:
            pass
        handle_bright_y = int(np.interp(current_brightness, [0, 100], [slider_y_bottom, slider_y_top]))
        cv2.circle(frame, (slider_brightness_x, handle_bright_y), 13, (255, 255, 0), -1)
        cv2.circle(frame, (slider_brightness_x, handle_bright_y), 13, (255, 255, 255), 2)
        cv2.putText(frame, "PARLAKLIK", (slider_brightness_x - 45, slider_y_top - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

    has_two_finger_hand = False
    has_three_finger_hand = False
    has_five_finger_hand = False

    current_frame_hand_ids = []

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            current_frame_hand_ids.append(idx)
            
            lm_list = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]
            
            thumb_tip = lm_list[4]
            index_tip = lm_list[8]
            
            finger_states = get_finger_states(hand_landmarks)
            open_count = sum(finger_states)

            is_two = (finger_states[1] and finger_states[2] and not finger_states[3] and not finger_states[4])
            is_three = (finger_states[1] and finger_states[2] and finger_states[3] and not finger_states[4])
            if is_two:
                has_two_finger_hand = True
            if is_three:
                has_three_finger_hand = True
            if open_count == 5:
                has_five_finger_hand = True
            # ----------------------------------------------------
            # PARLAKLIK VE KALINLIK AYARI (ELE ÖZEL KİLİTLEME)
            # ----------------------------------------------------
            hand_center_x = lm_list[9][0]
            dist_thumb_index = get_distance(thumb_tip, index_tip)
            # Cımbız Şartı
            is_strict_pinch = (finger_states[0] and finger_states[1] and 
                               not finger_states[2] and not finger_states[3] and not finger_states[4] and 
                               dist_thumb_index < 110)
            if is_strict_pinch and not is_black_screen:
                # EKRANIN SAĞI -> PARLAKLIK
                if hand_center_x > w // 2:
                    brightness_val = int(np.interp(dist_thumb_index, [22, 110], [0, 100]))
                    try:
                        sbc.set_brightness(brightness_val)
                    except Exception:
                        pass
                    cv2.line(frame, thumb_tip, index_tip, (255, 255, 0), 2)
                    cv2.putText(frame, f"Parlaklik: %{brightness_val}", (w - 220, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                # EKRANIN SOLU -> KALEM KALINLIĞI
                else:
                    is_adjusting_thickness[idx] = True
                    temp_thickness[idx] = int(np.interp(dist_thumb_index, [15, 110], [1, 25]))
                    
                    cv2.line(frame, thumb_tip, index_tip, (0, 255, 255), 2)
                    cv2.putText(frame, f"Ayarlaniyor: {temp_thickness[idx]}px", (20, h - 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            else:
                # SADECE BU EL (idx) daha önce ayar yapıyorsa ve şimdi bıraktıysa kilitler!
                if is_adjusting_thickness.get(idx, False):
                    brush_thickness = temp_thickness.get(idx, brush_thickness)
                    is_adjusting_thickness[idx] = False
            # ----------------------------------------------------
            # İŞARET PARMAĞI İLE SEÇİM, ÇİZİM / SİLME VE SLIDER
            # ----------------------------------------------------
            is_drawing_gesture = (finger_states[1] and not finger_states[2] and not finger_states[3] and not finger_states[4])
            if is_drawing_gesture and not is_black_screen:
                ix, iy = index_tip
                # A) RENK SEÇİMİ
                if iy < 70:
                    hand_points[idx] = (0, 0)
                    if btn_kirmizi[0][0] < ix < btn_kirmizi[1][0]:
                        draw_color = (0, 0, 255)
                        mode = "KIRMIZI"
                    elif btn_yesil[0][0] < ix < btn_yesil[1][0]:
                        draw_color = (0, 255, 0)
                        mode = "YESIL"
                    elif btn_mavi[0][0] < ix < btn_mavi[1][0]:
                        draw_color = (255, 0, 0)
                        mode = "MAVI"
                    elif btn_silgi[0][0] < ix < btn_silgi[1][0]:
                        draw_color = (0, 0, 0)
                        mode = "SILGI"

                # B) SOL SLIDER: KALINLIK SCROLLBAR TUTMA
                elif abs(ix - slider_thickness_x) < 30 and (slider_y_top - 15 <= iy <= slider_y_bottom + 15): # isaret parmagi ucunun (ix,iy) çubuk içinde mi ? 
# parmak yatayda en fazla 30 piksel yakınlıkta olmasını kontrol et.
                    hand_points[idx] = (0, 0)  # Çizimi engelle 
                    clamped_y = max(slider_y_top, min(slider_y_bottom, iy))
                    brush_thickness = int(np.interp(clamped_y, [slider_y_top, slider_y_bottom], [25, 1]))

                # C) SAĞ SLIDER: PARLAKLIK SCROLLBAR TUTMA
                elif abs(ix - slider_brightness_x) < 30 and (slider_y_top - 15 <= iy <= slider_y_bottom + 15):
                    hand_points[idx] = (0, 0)  # Çizimi engelle
                    clamped_y = max(slider_y_top, min(slider_y_bottom, iy))
                    brightness_val = int(np.interp(clamped_y, [slider_y_top, slider_y_bottom], [100, 0]))
                    try:
                        sbc.set_brightness(brightness_val)
                    except Exception:
                        pass

                # D) ÇİZİM / SİLME
                else:
                    if draw_color is not None:
                        px, py = hand_points.get(idx, (0, 0))
                        
                        if px == 0 and py == 0:
                            px, py = ix, iy

                        if mode == "SILGI":
                            current_eraser_radius = int(brush_thickness * 1.2) + 6
                            cv2.circle(canvas, (ix, iy), current_eraser_radius, (0, 0, 0), -1)
                            cv2.circle(frame, (ix, iy), current_eraser_radius, (200, 200, 200), 2)
                        else:
                            cv2.line(canvas, (px, py), (ix, iy), draw_color, brush_thickness)
                            cv2.circle(frame, (ix, iy), max(1, brush_thickness // 2), draw_color, -1)

                        hand_points[idx] = (ix, iy)
            else:
                hand_points[idx] = (0, 0)

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if has_two_finger_hand:
            if black_screen_start_time is None:
                black_screen_start_time = time.time()
            elif time.time() - black_screen_start_time > 1.0:
                is_black_screen = True
        else:
            black_screen_start_time = None

        if has_three_finger_hand and not has_two_finger_hand:
            is_black_screen = False

        if has_five_finger_hand and not is_black_screen:
            if screenshot_start_time is None:
                screenshot_start_time = time.time()
            elif time.time() - screenshot_start_time > 1.8:
                combined = cv2.addWeighted(frame, 1, canvas, 0.8, 0)
                filename = f"ekran_goruntusu_{int(time.time())}.png"
                cv2.imwrite(filename, combined)
                
                show_ss_message_until = time.time() + 2.0
                screenshot_start_time = None
        else:
            screenshot_start_time = None

    else:
        hand_points.clear()
        is_adjusting_thickness.clear()
        temp_thickness.clear()
        black_screen_start_time = None
        screenshot_start_time = None

    # Ekrandan çıkan ellerin durumlarını temizle
    for h_id in list(hand_points.keys()):
        if h_id not in current_frame_hand_ids:
            del hand_points[h_id]
            if h_id in is_adjusting_thickness:
                del is_adjusting_thickness[h_id]
            if h_id in temp_thickness:
                del temp_thickness[h_id]

    if is_black_screen:
        frame = np.zeros_like(frame)
        cv2.putText(frame, "SIYAH EKRAN MODU", (w // 2 - 180, h // 2 - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, "Cikmak icin 3 parmak kaldirin", (w // 2 - 210, h // 2 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2)
    else:
        canvas_gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, inv_canvas = cv2.threshold(canvas_gray, 20, 255, cv2.THRESH_BINARY_INV)
        inv_canvas = cv2.cvtColor(inv_canvas, cv2.COLOR_GRAY2BGR)
        frame = cv2.bitwise_and(frame, inv_canvas)
        frame = cv2.bitwise_or(frame, canvas)

        status_text = f"Mod: {mode} | Kalinlik: {brush_thickness}px"
        cv2.putText(frame, status_text, (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    if time.time() < show_ss_message_until:
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 255, 0), 10)
        cv2.rectangle(frame, (w // 2 - 250, h - 100), (w // 2 + 250, h - 40), (0, 0, 0), -1)
        cv2.rectangle(frame, (w // 2 - 250, h - 100), (w // 2 + 250, h - 40), (0, 255, 0), 2)
        cv2.putText(frame, "EKRAN GORUNTUSU KAYDEDILDI!", (w // 2 - 220, h - 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Sanal Tahta ve El Kontrolu", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()