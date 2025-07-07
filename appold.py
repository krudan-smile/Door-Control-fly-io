import flet as ft
import pyrebase
import requests
import threading
import time
import os
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
                
        user_id = user_info['localId']
        display_name = user_info.get('displayName', user_info.get('email'))

        try:
            db.child("UsersActive").child(user_id).update({
                "displayName": display_name,
                "lastLogin": time.strftime("%Y-%m-%d %H:%M:%S")
            })
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

        def update_switch_status():
            try:
                data = db.child("smart-home").child("Door").get().val()
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
            try:
                current_value = db.child("smart-home").child("Door").child(switch_name).get().val() or "off"
                new_value = "off" if current_value == "on" else "on"
                db.child("smart-home").child("Door").update({switch_name: new_value})
                update_switch_status()

                db.child("ButtonHistory").push({
                    "name": display_name,
                    "action": switch_name,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                print(f"Error toggling switch {switch_name}: {e}")

        sw_men.on_click = lambda e: toggle_switch("Sw1")
        sw_men_pause.on_click = lambda e: toggle_switch("pause1")
        sw_women.on_click = lambda e: toggle_switch("Sw2")
        sw_women_pause.on_click = lambda e: toggle_switch("pause2")            

        update_switch_status()

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
                                user_text,
                                ft.Text("ระบบควบคุมประตูแผนกวิชาช่างอิเล็กทรอนิกส์", size=22, weight=ft.FontWeight.BOLD, color="blue", text_align=ft.TextAlign.CENTER),
                                ft.Icon(ft.Icons.HOME, size=100, color="blue"),
                                ft.Row([
                                    ft.Text("ชาย"), sw_men,
                                    ft.Text("หยุด"), sw_men_pause
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    ft.Text("หญิง"), sw_women,
                                    ft.Text("หยุด"), sw_women_pause
                                ], alignment=ft.MainAxisAlignment.CENTER),
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
                db.child("Users").child(user_id).update({"name": new_display_name})
                db.child("UsersActive").child(user_id).update({"displayName": new_display_name})

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
            button_history_list = db.child("ButtonHistory").get().each() or []
            login_history_list = db.child("LoginHistory").get().each() or []
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

        username = ft.TextField(
            label="Email", 
            width=300,
            value="",  # Default empty
            keyboard_type=ft.KeyboardType.EMAIL
        )
        password = ft.TextField(
            label="Password", 
            password=True, 
            can_reveal_password=True, 
            width=300,
            value=""  # Default empty
        )
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
            email = username.value.strip()
            pwd = password.value.strip()
            
            # Input validation
            if not email or not pwd:
                message.value = "กรุณากรอก Email และ Password"
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
                    db.child("LoginHistory").push(login_info)

                    # Update user info
                    db.child("Users").child(user_data['localId']).update({
                        "name": user_data.get('displayName', email),
                        "email": email
                    })
                except Exception as db_error:
                    print(f"Database update error: {db_error}")
                    # Continue with login even if database update fails

                print("Login successful, showing home")
                show_home(user_data)

            except Exception as ex:
                error_str = str(ex).lower()
                print(f"Login error: {ex}")
                
                if "invalid_email" in error_str:
                    message.value = "รูปแบบ Email ไม่ถูกต้อง"
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
                                password,
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
    ft.app(target=main, port=8080, view=ft.WEB_BROWSER, assets_dir="assets")