import flet as ft
import pyrebase
import requests
import threading
import time
import asyncio
import os
import random
import string
from flet.fastapi import app as flet_app
import uvicorn

firebaseConfig = {
    "apiKey": "AIzaSyCBUqsxdgeASWmbN3SQEJKpMOAEIqZp2p8",
    "authDomain": "electronicsdoor-501.firebaseapp.com",
    "databaseURL": "https://electronicsdoor-501-default-rtdb.firebaseio.com",
    "projectId": "electronicsdoor-501",
    "storageBucket": "electronicsdoor-501.appspot.com",
    "messagingSenderId": "118920840447",
    "appId": "1:118920840447:web:facb0945d58b4f6bde38ca"
}

# Initialize Firebase with error handling
try:
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()
    db = firebase.database()
    storage = firebase.storage()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    auth = None
    db = None


def generate_random_ping():
    """สร้างตัวอักษรสุ่มสำหรับ ping"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


def update_display_name(id_token, new_display_name):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={firebaseConfig['apiKey']}"
        payload = {
            "idToken": id_token,
            "displayName": new_display_name,
            "returnSecureToken": True
        }
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Update display name error: {e}")
        raise e

def update_password(id_token, new_password):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={firebaseConfig['apiKey']}"
        payload = {
            "idToken": id_token,
            "password": new_password,
            "returnSecureToken": True
        }
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Update password error: {e}")
        raise e

def main(page: ft.Page):
    page.title = "ระบบควบคุมประตูหน้าแผนกวิชาช่างอิเล็กทรอนิกส์"
    page.window_width = 420
    page.window_height = 900
    page.window_maximizable = False

    def check_internet():
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False

    def show_home(user_info):
        page.clean()
        status_text = ft.Text("⏳ Checking controller...", color=ft.Colors.GREY_600)
        
        # สร้างตัวแปรสำหรับควบคุมการแสดงผลปุ่ม
        controller_online = False

        def check_controller_status():
            nonlocal controller_online
            def run_check():
                nonlocal controller_online
                try:
                    # สร้างตัวอักษรสุ่มสำหรับ ping
                    ping_value = generate_random_ping()
                    token = page.client_storage.get("saved_token")
                    
                    # ส่ง ping เป็นตัวอักษรสุ่ม
                    db.child("smart-home").child("Door").update({"ping": ping_value}, token)
                    print(f"[Ping] Sent: {ping_value}")
                    
                except Exception as e:
                    status_text.value = "❌ Failed to send ping"
                    status_text.color = ft.Colors.RED
                    controller_online = False
                    update_switch_visibility()
                    page.update()
                    return

                # รอการตอบกลับจาก pong
                max_wait = 5
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    try:
                        # อ่าน pong จาก smart-home/pong
                        pong = db.child("smart-home").child("pong").get(token).val()
                        print(f"[Pong] Received: {pong}")
                        
                        if pong is not None:
                            # ตรวจสอบว่า pong ตรงกับ ping หรือไม่
                            if str(pong).strip() == ping_value:
                                status_text.value = "✅ Controller is ONLINE"
                                status_text.color = ft.Colors.GREEN
                                controller_online = True
                                update_switch_visibility()
                                page.update()
                                return
                            else:
                                print(f"Ping/Pong mismatch: sent '{ping_value}', received '{pong}'")
                                
                    except Exception as e:
                        print(f"Error reading pong: {e}")
                        
                    time.sleep(0.5)

                status_text.value = "❌ Controller is OFFLINE"
                status_text.color = ft.Colors.RED
                controller_online = False
                update_switch_visibility()
                page.update()
            
            # Run in a separate thread to avoid blocking the UI
            threading.Thread(target=run_check, daemon=True).start()

        # Start the controller check
        def start_controller_check():
            check_controller_status()

        user_id = user_info['localId']
        display_name = user_info.get('displayName', user_info.get('email'))
        id_token = page.client_storage.get("saved_token")

        try:
            db.child("UsersActive").child(user_id).update({
                "displayName": display_name,
                "lastLogin": time.strftime("%Y-%m-%d %H:%M:%S")
            }, id_token)
        except Exception as e:
            print(f"Error updating user active status: {e}")

        # Switch buttons
        sw_men = ft.IconButton(
            icon=ft.Icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.Icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )
        
        sw_men_pause = ft.IconButton(
            icon=ft.Icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.Icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )
        
        sw_women = ft.IconButton(
            icon=ft.Icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.Icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )
        
        sw_women_pause = ft.IconButton(
            icon=ft.Icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.Icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )

        # Switch containers - จะถูกซ่อน/แสดงตามสถานะ controller
        switch_row_men = ft.Row([
            ft.Text("ชาย"), sw_men,
            ft.Text("หยุด"), sw_men_pause
        ], alignment=ft.MainAxisAlignment.CENTER, visible=False)
        
        switch_row_women = ft.Row([
            ft.Text("หญิง"), sw_women,
            ft.Text("หยุด"), sw_women_pause
        ], alignment=ft.MainAxisAlignment.CENTER, visible=False)

        # ข้อความแสดงเมื่อ controller offline
        offline_message = ft.Container(
            content=ft.Column([
                ft.Text("🔒 Controller is not available", 
                       size=18, 
                       color=ft.Colors.RED, 
                       text_align=ft.TextAlign.CENTER),
                ft.Text("Switch controls are disabled", 
                       size=14, 
                       color=ft.Colors.GREY, 
                       text_align=ft.TextAlign.CENTER),
                ft.ElevatedButton(
                    "Refresh Status",
                    on_click=lambda e: start_controller_check(),
                    icon=ft.Icons.REFRESH
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            visible=True
        )

        def update_switch_visibility():
            """อัพเดทการแสดงผลของปุ่มสวิทช์ตามสถานะ controller"""
            switch_row_men.visible = controller_online
            switch_row_women.visible = controller_online
            offline_message.visible = not controller_online
            
            if controller_online:
                update_switch_status()

        def update_switch_status():
            try:
                id_token = page.client_storage.get("saved_token")
                data = db.child("smart-home").child("Door").get(id_token).val()
                print("Door status:", data)
                if data:
                    sw_men.selected = data.get("Sw1") == "on"
                    sw_men_pause.selected = data.get("pause1") == "on"
                    sw_women.selected = data.get("Sw2") == "on"
                    sw_women_pause.selected = data.get("pause2") == "on"
                page.update()
            except Exception as e:
                print(f"Error updating switch status: {e}")

        def logout(e):
            try:
                page.client_storage.remove("saved_token")
            except:
                pass
            show_login()
            
        def on_nav_change(e):
            selected_index = e.control.selected_index
            if selected_index == 0:
                go_to_profile(e)
            elif selected_index == 1:
                logout(e)        
            elif selected_index == 2:
                go_to_history(e)     

        def go_to_profile(e):
            show_edit_profile(user_info)

        def go_to_history(e):
            show_history(user_info)

        def toggle_switch(switch_name):
            # ตรวจสอบว่า controller online หรือไม่ก่อนทำงาน
            if not controller_online:
                return
                
            try:
                id_token = page.client_storage.get("saved_token")
                current_value = db.child("smart-home").child("Door").child(switch_name).get(id_token).val() or "off"
                new_value = "off" if current_value == "on" else "on"
                db.child("smart-home").child("Door").update({switch_name: new_value}, id_token)
                update_switch_status()

                db.child("ButtonHistory").push({
                    "name": display_name,
                    "action": switch_name,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }, id_token)
            except Exception as e:
                print(f"Error toggling switch {switch_name}: {e}")

        sw_men.on_click = lambda e: toggle_switch("Sw1")
        sw_men_pause.on_click = lambda e: toggle_switch("pause1")
        sw_women.on_click = lambda e: toggle_switch("Sw2")
        sw_women_pause.on_click = lambda e: toggle_switch("pause2")            

        user_text = ft.Text(f"🔵 สวัสดีครับคุณ: {display_name}", size=18, color=ft.Colors.BLUE)

        MenuTemplat = ft.NavigationBar(
            on_change=on_nav_change,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.EDIT, label="Edit Profile"),
                ft.NavigationBarDestination(icon=ft.Icons.LOGOUT, label="Logout"),                
                ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="View History"),
            ]
        )        

        page.add(
            ft.Container(
                content=ft.Card(
                    content=ft.Container(
                        padding=20,
                        content=ft.Column(
                            [
                                ft.Row([user_text, status_text], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Text("ระบบควบคุมประตูแผนกวิชาช่างอิเล็กทรอนิกส์", size=22, weight=ft.FontWeight.BOLD, color="blue", text_align=ft.TextAlign.CENTER),
                                ft.Icon(ft.Icons.HOME, size=100, color="blue"),
                                
                                # แสดง switch controls เมื่อ controller online
                                switch_row_men,
                                switch_row_women,
                                
                                # แสดงข้อความเมื่อ controller offline
                                offline_message,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20,
                        )
                    )
                ),
                alignment=ft.alignment.center,
                expand=True
            ), MenuTemplat
        )

        # Start controller check after UI is set up
        start_controller_check()

    def show_edit_profile(user_info):
        page.clean()
        user_id = user_info['localId']
        current_display_name = user_info.get('displayName', user_info.get('email'))
        email = user_info.get('email')
        id_token = page.client_storage.get("saved_token")

        new_display_name_field = ft.TextField(label="New Display Name", value=current_display_name, width=300)
        new_password_field = ft.TextField(label="New Password", password=True, can_reveal_password=True, width=300)
        message = ft.Text("", color="green")

        def save_profile(e):
            new_display_name = new_display_name_field.value.strip()
            new_password = new_password_field.value.strip()

            try:
                id_token = page.client_storage.get("saved_token")
                
                db.child("Users").child(user_id).update({"name": new_display_name}, id_token)
                db.child("UsersActive").child(user_id).update({"displayName": new_display_name}, id_token)

                update_display_name(id_token, new_display_name)

                if new_password:
                    update_password(id_token, new_password)
                    message.value = "Profile updated. Please logout and login again."
                else:
                    message.value = "Profile updated successfully."

                message.color = "green"
                page.update()

            except Exception as ex:
                message.value = "เกิดข้อผิดพลาดในการอัพเดทข้อมูล"
                message.color = "red"
                page.update()
                print(f"Profile update error: {ex}")

        def back_to_home(e):
            show_home(user_info)

        def NavProfile(e):
            selected_index = e.control.selected_index
            if selected_index == 0:
                save_profile(e)
            elif selected_index == 1:
                back_to_home(e)         

        page.add(
            ft.Container(
                content=ft.Card(
                    content=ft.Container(
                        padding=20,
                        content=ft.Column(
                            [
                                ft.Text("Edit Profile", size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                ft.Text(f"Email: {email}", color=ft.Colors.GREY),
                                new_display_name_field,
                                new_password_field,
                                message
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15
                        )
                    )
                ),
                alignment=ft.alignment.center,
                expand=True
            ),
            ft.NavigationBar(
                on_change=NavProfile,
                destinations=[
                    ft.NavigationBarDestination(icon=ft.Icons.SAVE, label="Save"),   
                    ft.NavigationBarDestination(icon=ft.Icons.ARROW_BACK, label="Back"),                  
                ]
            )
        )

    def show_history(user_info):
        page.controls.clear()

        try:
            id_token = page.client_storage.get("saved_token")
            button_history_list = db.child("ButtonHistory").get(id_token).each() or []
            login_history_list = db.child("LoginHistory").get(id_token).each() or []
        except Exception as e:
            print(f"Error fetching history: {e}")
            button_history_list = []
            login_history_list = []

        button_history_view = ft.Column(
            controls=[
                ft.Text(f"🔵 {item.val()['name']} → {item.val()['action']}→ {item.val()['timestamp']}", size=16)
                for item in button_history_list if item.val()
            ],
            spacing=5
        )

        login_history_view = ft.Column(
            controls=[
                ft.Text(f"🟢 {item.val()['name']} → {item.val()['login_time']}", size=16)
                for item in login_history_list if item.val()
            ],
            spacing=5
        )

        def back_to_home(e):
            show_home(user_info)

        page.add(
            ft.Container(
                content=ft.Card(
                    content=ft.Container(
                        padding=20,
                        content=ft.Column(
                            [
                                ft.Text("🗂 HISTORY", size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                ft.Text("🛎 Button History", size=20, weight=ft.FontWeight.BOLD, color="blue"),
                                ft.Container(
                                    content=ft.Column(
                                        controls=button_history_view.controls,
                                        scroll=ft.ScrollMode.AUTO
                                    ),
                                    height=200,
                                    bgcolor=ft.Colors.GREY_100,
                                    padding=10,
                                    border_radius=8
                                ),
                                ft.Text("🔐 Login History", size=20, weight=ft.FontWeight.BOLD, color="green"),
                                ft.Container(
                                    content=ft.Column(
                                        controls=login_history_view.controls,
                                        scroll=ft.ScrollMode.AUTO
                                    ),
                                    height=200,
                                    bgcolor=ft.Colors.GREY_100,
                                    padding=10,
                                    border_radius=8
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15
                        )
                    )
                ),
                alignment=ft.alignment.center,
                expand=True
            ),
            ft.NavigationBar(
                on_change=back_to_home,
                destinations=[
                    ft.NavigationBarDestination(icon=ft.Icons.ARROW_BACK, label="Back"),                    
                ]
            )  
        )

        page.update()

    def show_login():
        page.clean()

        # Check for saved token first
        saved_token = page.client_storage.get("saved_token")
        if saved_token:
            try:
                print("Checking saved token...")
                user_info = auth.get_account_info(saved_token)
                if user_info and 'users' in user_info and user_info['users']:
                    user_data = user_info['users'][0]
                    print("Auto-login successful")
                    show_home(user_data)
                    return
            except Exception as e:
                print(f"Saved token invalid: {e}")
                try:
                    page.client_storage.remove("saved_token")
                except:
                    pass

        # ดึงข้อมูลที่จำไว้
        saved_username = page.client_storage.get("saved_username") or ""
        saved_password = page.client_storage.get("saved_password") or ""
        remember_me_checked = page.client_storage.get("remember_me") == "true"

        username = ft.TextField(
            label="Username", 
            width=300,
            value=saved_username,
            hint_text="กรอกเฉพาะชื่อผู้ใช้ (จะเติม @kpt.com ให้)",
            keyboard_type=ft.KeyboardType.TEXT
        )
        password = ft.TextField(
            label="Password", 
            password=True, 
            can_reveal_password=True, 
            width=300,
            value=saved_password
        )
        
        # Checkbox สำหรับจำรหัสผ่าน
        remember_me = ft.Checkbox(
            label="Remember Username & Password",
            value=remember_me_checked,
            check_color=ft.Colors.BLUE,
            fill_color=ft.Colors.BLUE_100,
        )
        
        # แสดงอีเมลที่จะใช้
        email_preview = ft.Text(
            f"Email: {saved_username}@kpt.com" if saved_username else "Email: @kpt.com",
            size=12,
            color=ft.Colors.GREY,
            italic=True
        )
        
        def update_email_preview(e):
            current_username = username.value.strip()
            if current_username:
                email_preview.value = f"Email: {current_username}@kpt.com"
            else:
                email_preview.value = "Email: @kpt.com"
            page.update()
            
        username.on_change = update_email_preview
        
        message = ft.Text("", color="red")
        internet_status = ft.Text("Checking Internet...", color=ft.Colors.ORANGE)

        def update_internet_status():
            def run():
                while True:
                    if check_internet():
                        internet_status.value = "Status: Ready..."
                        internet_status.color = ft.Colors.GREEN
                    else:
                        internet_status.value = "Status: Disconnected"
                        internet_status.color = ft.Colors.RED
                    try:
                        page.update()
                    except:
                        break
                    time.sleep(5)
            threading.Thread(target=run, daemon=True).start()

        def login(e):
            user_name = username.value.strip()
            pwd = password.value.strip()
            
            # สร้าง email โดยเติม @kpt.com
            email = f"{user_name}@kpt.com" if user_name else ""
            
            # Input validation
            if not user_name or not pwd:
                message.value = "กรุณากรอก Username และ Password"
                message.color = "red"
                page.update()
                return
                
            if not check_internet():
                message.value = "ไม่มีการเชื่อมต่ออินเทอร์เน็ต"
                message.color = "red"
                page.update()
                return
                
            if not auth or not db:
                message.value = "ไม่สามารถเชื่อมต่อ Firebase ได้"
                message.color = "red"
                page.update()
                return

            try:
                print(f"Attempting login with email: {email}")
                message.value = "กำลังตรวจสอบ..."
                message.color = "blue"
                page.update()
                
                # Sign in with Firebase
                user_auth = auth.sign_in_with_email_and_password(email, pwd)
                print("Firebase authentication successful")
                
                # บันทึกข้อมูลถ้าผู้ใช้เลือก Remember Me
                if remember_me.value:
                    page.client_storage.set("saved_username", user_name)
                    page.client_storage.set("saved_password", pwd)
                    page.client_storage.set("remember_me", "true")
                else:
                    # ลบข้อมูลที่จำไว้ถ้าผู้ใช้ไม่เลือก Remember Me
                    try:
                        page.client_storage.remove("saved_username")
                        page.client_storage.remove("saved_password")
                        page.client_storage.remove("remember_me")
                    except:
                        pass
                
                id_token = user_auth['idToken']
                page.client_storage.set("saved_token", id_token)
                
                # Get user info
                user_info = auth.get_account_info(id_token)
                user_data = user_info['users'][0]
                print(f"User data retrieved: {user_data.get('email')}")

                # Log login history
                try:
                    login_info = {
                        "name": user_data.get('displayName', email),
                        "email": email,
                        "login_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    db.child("LoginHistory").push(login_info, id_token)

                    # Update user info
                    db.child("Users").child(user_data['localId']).update({
                        "name": user_data.get('displayName', email),
                        "email": email
                    }, id_token)
                except Exception as db_error:
                    print(f"Database update error: {db_error}")
                    # Continue with login even if database update fails

                print("Login successful, showing home")
                show_home(user_data)

            except Exception as ex:
                error_str = str(ex).lower()
                print(f"Login error: {ex}")
                
                if "invalid_email" in error_str:
                    message.value = "รูปแบบ Username ไม่ถูกต้อง"
                elif "user_not_found" in error_str:
                    message.value = "ไม่พบผู้ใช้นี้ในระบบ"
                elif "wrong_password" in error_str or "invalid_password" in error_str:
                    message.value = "รหัสผ่านไม่ถูกต้อง"
                elif "too_many_requests" in error_str:
                    message.value = "มีการพยายามเข้าสู่ระบบมากเกินไป กรุณารอสักครู่"
                elif "network" in error_str or "connection" in error_str:
                    message.value = "ปัญหาการเชื่อมต่อ กรุณาตรวจสอบอินเทอร์เน็ต"
                else:
                    message.value = "เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
                
                message.color = "red"
                page.update()

        # Handle Enter key press
        def on_key_press(e):
            if e.key == "Enter":
                login(e)
                
        username.on_submit = login
        password.on_submit = login

        page.add(
            ft.Container(
                content=ft.Card(
                    content=ft.Container(
                        width=min(page.window_width * 0.9, 400),
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        content=ft.Column(
                            [
                                ft.Text("เข้าสู่ระบบ", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                internet_status,
                                username,
                                # email_preview,
                                password,
                                remember_me,
                                message,
                                ft.CupertinoFilledButton(
                                    content=ft.Text("LOGIN"),
                                    opacity_on_click=0.3,
                                    on_click=login,
                                    width=250,
                                    height=50,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20
                        )
                    )
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        )

        update_internet_status()

    # Start with login screen
    show_login()

if __name__ == "__main__":
    # ft.app(target=main, port=8080, view=ft.WEB_BROWSER)
     uvicorn.run(flet_app(main), host="0.0.0.0", port=int(os.environ.get("PORT", 8550)))