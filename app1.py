import flet as ft
import pyrebase
import requests
import threading
import time
import os
from flet.fastapi import app as flet_app
import uvicorn

# Firebase config
firebaseConfig = {
    "apiKey": "AIzaSyCBUqsxdgeASWmbN3SQEJKpMOAEIqZp2p8",
    "authDomain": "electronicsdoor-501.firebaseapp.com",
    "databaseURL": "https://electronicsdoor-501-default-rtdb.firebaseio.com/",
    "projectId": "electronicsdoor-501",
    "storageBucket": "electronicsdoor-501.appspot.com",
    "messagingSenderId": "331451462196",
    "appId": "1:331451462196:web:b5c6145b7db7c60ff86b0f",
    "measurementId": "G-YFMER0R1ME"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

def main(page: ft.Page):
    page.title = "ควบคุม เปิด-ปิด ประตู"
    page.window_width = 390
    page.window_height = 844
    page.window_maximizable = False

    def check_internet():
        try:
            requests.get("https://www.google.com", timeout=2)
            return True
        except:
            return False

    def show_home(user_info):
        page.clean()

        # ตัวอย่างปุ่มเปิดปิดประตู
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
            data = db.child("smart-home").child("Door").get().val()
            print("Door status:", data)

            sw_men.selected = True if data and data.get("Sw1") == "on" else False
            sw_men_pause.selected = True if data and data.get("pause1") == "on" else False
            sw_women.selected = True if data and data.get("Sw2") == "on" else False
            sw_women_pause.selected = True if data and data.get("pause2") == "on" else False

            page.update()

        def toggle_sw1(e):
            current_value = db.child("smart-home").child("Door").child("Sw1").get().val() or "off"
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"Sw1": new_value})
            update_switch_status()

        def toggle_pause1(e):
            current_value = db.child("smart-home").child("Door").child("pause1").get().val() or "off"
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"pause1": new_value})
            update_switch_status()

        def toggle_sw2(e):
            current_value = db.child("smart-home").child("Door").child("Sw2").get().val() or "off"
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"Sw2": new_value})
            update_switch_status()

        def toggle_pause2(e):
            current_value = db.child("smart-home").child("Door").child("pause2").get().val() or "off"
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"pause2": new_value})
            update_switch_status()

        def logout(e):
            page.client_storage.remove("saved_token")
            show_login()

        # กำหนด event handler
        sw_men.on_click = toggle_sw1
        sw_men_pause.on_click = toggle_pause1
        sw_women.on_click = toggle_sw2
        sw_women_pause.on_click = toggle_pause2

        update_switch_status()

        # แสดง user info ด้านบน (ตัวอย่าง)
        user_text = ft.Text(f"Logged in as: {user_info.get('displayName') or user_info.get('email')}", size=16, color=ft.Colors.BLUE)

        MenuTemplat = ft.NavigationBar(
            on_change=logout,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.LOGOUT, label="Logout"),
            ]
        )

        page.add(
            ft.Column([
                user_text,
                ft.Text("\nควบคุม ปิด-เปิด ประตูแผนกวิชาช่างอิเล็กทรอนิกส์", size=20, weight=ft.FontWeight.BOLD, color="blue", text_align=ft.TextAlign.CENTER),
                ft.Icon(ft.Icons.HOME, size=80, color="blue"),
                ft.Row([
                    ft.Text("ชาย"), sw_men,
                    ft.Text("หยุด"), sw_men_pause
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.Text("หญิง"), sw_women,
                    ft.Text("หยุด"), sw_women_pause
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            MenuTemplat
        )

    def show_login():
        page.clean()

        saved_token = page.client_storage.get("saved_token")

        # ถ้ามี token ให้ลองดึงข้อมูลและแสดงหน้า Home เลย
        if saved_token:
            try:
                user_info = auth.get_account_info(saved_token)
                # user_info เป็น dict ให้เราเอา uid และ displayName ออกมาด้วย
                user_data = user_info['users'][0]
                # บันทึก user data ลง DB (ถ้ายังไม่มี)
                user_id = user_data['localId']
                display_name = user_data.get('displayName', user_data.get('email'))

                # เก็บข้อมูล userId และ displayName ลงฐานข้อมูล Realtime Database
                db.child("UsersLoggedIn").child(user_id).push({
                    "displayName": display_name,
                    "lastLogin": int(time.time())
                })

                show_home(user_data)
                return
            except:
                page.client_storage.remove("saved_token")

        username = ft.TextField(label="Username", width=300)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
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
                    page.update()
                    time.sleep(3)
            threading.Thread(target=run, daemon=True).start()

        def login(e):
            users = db.child("Users").get()
            found = False
            for user in users.each():
                user_data = user.val()
                if user_data['name'] == username.value and str(user_data['password']) == password.value:
                    # Use email/password login to get token
                    try:
                        user_auth = auth.sign_in_with_email_and_password(user_data['email'], user_data['password'])
                        id_token = user_auth['idToken']
                        page.client_storage.set("saved_token", id_token)

                        # 🔥 บันทึกข้อมูล name, email ลง Firebase ใน node 'LoginHistory'
                        login_info = {
                            "name": user_data['name'],
                            "email": user_data['email'],
                            "login_time": time.strftime("%Y-%m-%d %H:%M:%S")  # timestamp login
                        }
                        db.child("LoginHistory").push(login_info)

                    except:
                        message.value = "เกิดข้อผิดพลาดในการรับ Token"
                        page.update()
                        return

                    show_home()
                    found = True
                    break
            if not found:
                message.value = "Username หรือ Password ไม่ถูกต้อง"
                page.update()

                message.value = "Username หรือ Password ไม่ถูกต้อง"
                page.update()

        # btn_login = ft.ElevatedButton(text="เข้าสู่ระบบ", on_click=login, width=300)

        # page.add(
        #     ft.Column([
        #         ft.Text("ระบบควบคุมประตู", size=24, weight=ft.FontWeight.BOLD, color="blue"),
        #         username,
        #         password,
        #         btn_login,
        #         message,
        #         internet_status
        #     ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        # )
        # Add login UI centered in Card and centered on the page
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Card(
                            elevation=5,
                            content=ft.Container(
                                width=min(page.window_width * 0.9, 400),
                                padding=20,
                                bgcolor=ft.Colors.WHITE,
                                border_radius=10,
                                content=ft.Column(
                                    [
                                        ft.Text("เข้าสู่ระบบ", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                        internet_status,
                                        username,
                                        password,
                                        message,
                                        # ft.ElevatedButton("Login", on_click=login),
                                        ft.CupertinoFilledButton(
                                        content=ft.Text("LOGIN"),
                                        opacity_on_click=0.3,
                                        # on_click=lambda e: print(f"LOGIN! {username.value},{password.value}"),
                                        on_click= login,
                                        width=250,
                                        height=50,
                                    ),
                                        message
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=20
                                )
                            )
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        )

        update_internet_status()

    # เริ่มต้นแสดง login page
    show_login()

if __name__ == "__main__":
    # รันด้วย Flet Server
    ft.app(target=main, port=8080, view=ft.WEB_BROWSER)
# if __name__ == "__main__":
    # uvicorn.run(flet_app(main), host="0.0.0.0", port=int(os.environ.get("PORT", 8550)))
