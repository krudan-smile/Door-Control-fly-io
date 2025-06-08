import flet as ft
import pyrebase
import requests
import threading
import time
from flet.fastapi import app as flet_app
import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

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

# Main Flet App
def main(page: ft.Page):
    page.title = "ควบคุม เปิด-ปิด ประตู"
    page.window_width = 390
    page.window_height = 844
    page.window_maximizable = False

    # รับ userId จาก LIFF (ถ้ามี)
    user_id_from_line = page.query_params.get("userId")
    print("LIFF UserID (query param):", user_id_from_line)

    def check_internet():
        try:
            requests.get("https://www.google.com", timeout=2)
            return True
        except:
            return False

    def show_home():
        page.clean()

        sw_men = ft.IconButton(
            icon=ft.icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )

        sw_men_pause = ft.IconButton(
            icon=ft.icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )

        sw_women = ft.IconButton(
            icon=ft.icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )

        sw_women_pause = ft.IconButton(
            icon=ft.icons.POWER_SETTINGS_NEW,
            icon_size=50,
            selected_icon=ft.icons.POWER_SETTINGS_NEW,
            selected=False,
            style=ft.ButtonStyle(color={"selected": ft.Colors.GREEN, "": ft.Colors.RED})
        )

        def update_switch_status():
            data = db.child("smart-home").child("Door").get().val()
            print("Door status:", data)

            sw_men.selected = True if data["Sw1"] == "on" else False
            sw_men_pause.selected = True if data["pause1"] == "on" else False
            sw_women.selected = True if data["Sw2"] == "on" else False
            sw_women_pause.selected = True if data["pause2"] == "on" else False

            page.update()

        def toggle_sw1(e):
            current_value = db.child("smart-home").child("Door").child("Sw1").get().val()
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"Sw1": new_value})
            update_switch_status()

        def toggle_pause1(e):
            current_value = db.child("smart-home").child("Door").child("pause1").get().val()
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"pause1": new_value})
            update_switch_status()

        def toggle_sw2(e):
            current_value = db.child("smart-home").child("Door").child("Sw2").get().val()
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"Sw2": new_value})
            update_switch_status()

        def toggle_pause2(e):
            current_value = db.child("smart-home").child("Door").child("pause2").get().val()
            new_value = "off" if current_value == "on" else "on"
            db.child("smart-home").child("Door").update({"pause2": new_value})
            update_switch_status()

        def logout(e):
            page.client_storage.remove("saved_token")
            show_login()

        sw_men.on_click = toggle_sw1
        sw_men_pause.on_click = toggle_pause1
        sw_women.on_click = toggle_sw2
        sw_women_pause.on_click = toggle_pause2

        update_switch_status()

        MenuTemplat = ft.NavigationBar(
            on_change=logout,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.LOGOUT, label="Logout"),
            ]
        )

        page.add(
            ft.Column([
                ft.Text("\nควบคุม ปิด-เปิด ประตูแผนกวิชาช่างอิเล็กทรอนิกส์", size=20, weight=ft.FontWeight.BOLD, color="blue", text_align=ft.TextAlign.CENTER),
                ft.Text(f"(LIFF UserID: {user_id_from_line})", size=12, color="green"),  # แสดง userId
                ft.Icon(ft.icons.HOME, size=80, color="blue"),
                ft.Row([ft.Text("ชาย"), sw_men, ft.Text("หยุด"), sw_men_pause], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([ft.Text("หญิง"), sw_women, ft.Text("หยุด"), sw_women_pause], alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            MenuTemplat
        )

    def show_login():
        page.clean()

        saved_token = page.client_storage.get("saved_token")

        if saved_token:
            try:
                auth.get_account_info(saved_token)
                show_home()
                return
            except:
                page.client_storage.remove("saved_token")

        username = ft.TextField(label="Username", width=300)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        message = ft.Text("", color="red")
        internet_status = ft.Text("Checking Internet...", color=ft.colors.ORANGE)

        def update_internet_status():
            def run():
                while True:
                    if check_internet():
                        internet_status.value = "Internet: Connected"
                        internet_status.color = ft.colors.GREEN
                    else:
                        internet_status.value = "Internet: Disconnected"
                        internet_status.color = ft.colors.RED
                    page.update()
                    time.sleep(3)

            threading.Thread(target=run, daemon=True).start()

        def login(e):
            users = db.child("Users").get()
            found = False
            for user in users.each():
                user_data = user.val()
                if user_data['name'] == username.value and str(user_data['password']) == password.value:
                    try:
                        user_auth = auth.sign_in_with_email_and_password(user_data['email'], user_data['password'])
                        id_token = user_auth['idToken']
                        page.client_storage.set("saved_token", id_token)
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

        update_internet_status()

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Card(
                            elevation=5,
                            content=ft.Container(
                                width=min(page.window_width * 0.9, 400),
                                padding=20,
                                bgcolor=ft.colors.WHITE,
                                border_radius=10,
                                content=ft.Column(
                                    [
                                        ft.Text("เข้าสู่ระบบ", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                        internet_status,
                                        username,
                                        password,
                                        ft.CupertinoFilledButton(
                                            content=ft.Text("LOGIN"),
                                            opacity_on_click=0.3,
                                            on_click=login,
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

    show_login()

# --- Setup FastAPI app ---
api_app = FastAPI()

# Serve static /liff/ → static/liff/
api_app.mount("/liff", StaticFiles(directory="static/liff", html=True), name="liff")

# API log_user → log userId จาก LIFF
@api_app.post("/api/log_user")
async def log_user(request: Request):
    data = await request.json()
    user_id = data.get("userId")
    print(f"[LOG_USER] LINE UserID: {user_id}")
    return {"status": "ok"}

# Mount Flet app ที่ /
api_app.mount("/", flet_app(main))

# Run Server
if __name__ == "__main__":
    uvicorn.run(api_app, host="0.0.0.0", port=int(os.environ.get("PORT", 8550)))
