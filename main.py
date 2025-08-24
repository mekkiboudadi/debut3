from flet import *
import sqlite3
import hashlib
# import smtplib
# from email.mime.text import MIMEText
# import random
# import string

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('debt.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # جدول الديون
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS debt(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               lname TEXT,
               ldate_send TEXT,
               lmoney TEXT,
               ltreason TEXT,
               ltime TEXT,
               ldate_up TEXT
               )''')
        
        # جدول المستخدمين
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT UNIQUE,
               email TEXT UNIQUE,
               password TEXT,
               reset_token TEXT,
               token_expiry TEXT
               )''')
        self.conn.commit()

    # عمليات الديون
    def add_item(self, lname, ldate_send, lmoney, ltreason, ltime, ldate_up):
        self.cursor.execute('''
            INSERT INTO debt(lname, ldate_send, lmoney, ltreason, ltime, ldate_up)
            VALUES(?, ?, ?, ?, ?, ?)''',
            (lname.value, ldate_send.value, lmoney.value, ltreason.value, ltime.value, ldate_up.value)
        )
        self.conn.commit()

    def get_all_items(self):
        self.cursor.execute('SELECT * FROM debt')
        return self.cursor.fetchall()

    def get_item(self, item_id):
        self.cursor.execute('SELECT * FROM debt WHERE id=?', (item_id,))
        return self.cursor.fetchone()

    def update_item(self, id, lname, ldate_send, lmoney, ltreason, ltime, ldate_up):
        self.cursor.execute('''
            UPDATE debt 
            SET lname=?, ldate_send=?, lmoney=?, ltreason=?, ltime=?, ldate_up=? 
            WHERE id=?''',
            (lname, ldate_send, lmoney, ltreason, ltime, ldate_up, id)
        )
        self.conn.commit()

    def delete_item(self,id):
        self.cursor.execute('DELETE FROM debt WHERE id=?', (id,))
        self.conn.commit()

    # عمليات المستخدمين
    def register_user(self, username, email, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute('''
                INSERT INTO users(username, email, password)
                VALUES(?, ?, ?)''',
                (username, email, hashed_password)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute('''
            SELECT id, username FROM users 
            WHERE username=? AND password=?''',
            (username, hashed_password)
        )
        return self.cursor.fetchone()

    def set_reset_token(self, email, token):
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        self.cursor.execute('''
            UPDATE users 
            SET reset_token=?, token_expiry=?
            WHERE email=?''',
            (token, expiry.strftime("%Y-%m-%d %H:%M:%S"), email)
        )
        self.conn.commit()

    def get_user_by_token(self, token):
        self.cursor.execute('''
            SELECT id, username, email FROM users 
            WHERE reset_token=? AND token_expiry > datetime('now')''',
            (token,)
        )
        return self.cursor.fetchone()

    def update_password(self, user_id, new_password):
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        self.cursor.execute('''
            UPDATE users 
            SET password=?, reset_token=NULL, token_expiry=NULL
            WHERE id=?''',
            (hashed_password, user_id)
        )
        self.conn.commit()

class EmailService:
    @staticmethod
    def send_reset_email(email, token):
        # هذا مثال بسيط، في التطبيق الحقيقي تحتاج إلى إعداد إعدادات البريد الإلكتروني
        msg = MIMEText(f"استخدم هذا الرابط لإعادة تعيين كلمة المرور: http://yourapp.com/reset?token={token}")
        msg['Subject'] = 'إعادة تعيين كلمة المرور'
        msg['From'] = 'noreply@yourapp.com'
        msg['To'] = email
        
        try:
            with smtplib.SMTP('smtp.example.com', 587) as server:
                server.login('your_email@example.com', 'your_password')
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

class CardWidget:
    def __init__(self, person,on_edit=None, on_delete=None):
        id, lname, ldate_send, lmoney, ltreason, ltime, ldate_up = person
        
        
        self.edit_btn = IconButton(
            icon=icons.EDIT,
            on_click=lambda e: on_edit(person) if on_edit else None,
            icon_color=colors.BLUE_700
        )
        
        self.delete_btn = IconButton(
            icon=icons.DELETE,
            on_click=lambda e: on_delete(id) if on_delete else None,
            icon_color=colors.RED_700
        )
        heade= Column([ Text(f" الرقم: {id}", weight=FontWeight.BOLD, size=20),
                Text(f"الاسم: {lname}", size=18),
                # Row([self.edit_btn, self.delete_btn], spacing=5),
                
        ]
        )
        self.card_content = Column(
              [   heade,
                # Text(f" الرقم: {id}", weight=FontWeight.BOLD, size=20),
                # Text(f"الاسم: {lname}", size=18),
                # Row([self.edit_btn, self.delete_btn], spacing=5),
                
                Divider(height=1),
                Text(f"تاريخ الاستدانة: {ldate_send}", size=16),
                Text(f"المبلغ: {lmoney} دج", size=16),
                Text(f"السبب: {ltreason}", size=16),
                Text(f"المدة المتوقعة: {ltime}", size=16),
                Text(f"تاريخ التأكيد: {ldate_up}", size=16),
                Row([self.edit_btn, self.delete_btn], spacing=5),
            ],
            spacing=8,
            alignment=MainAxisAlignment.START,
            expand=True
        )
        
        self.card = Card(
            elevation=8,
            content=Container(
                content=self.card_content,
                padding=15,
                border_radius=30,
                bgcolor='#ACFF7A',
                rtl=True,
                

            ),
            margin=margin.symmetric(horizontal=10, vertical=5),
            color=colors.with_opacity(0.05, colors.SURFACE_VARIANT),
            shadow_color=colors.with_opacity(0.1, colors.ON_SURFACE),
            
        )

class LoginPage:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        
        # ألوان متناسقة
        self.primary_color = "#00E6CF"
        self.secondary_color = "#1300E6"
        self.accent_color = "#FFE81A"
        self.error_color = "#FA0011"
        
        self.username = TextField(
            label="اسم المستخدم",
            border_color=self.primary_color,
            focused_border_color=self.secondary_color,
            text_size=16,
            width=300,
            icon=icons.PERSON,
            rtl=True
        )
        
        self.password = TextField(
            label="كلمة المرور",
            password=True,
            border_color=self.primary_color,
            focused_border_color=self.secondary_color,
            text_size=16,
            width=300,
            icon=icons.PASSWORD,
            rtl=True
        )
        
        self.error_text = Text("", color=self.error_color)
        
        self.view = View(
            "/",
            [
                Container(
                    content=Column(
                        [
                            Text("تسجيل الدخول", size=24, weight=FontWeight.BOLD),
                            self.username,
                            self.password,
                            ElevatedButton(
                                "تسجيل الدخول",
                                on_click=self.login_clicked,
                                bgcolor=self.primary_color,
                                color=colors.WHITE
                            ),
                            TextButton(
                                "إنشاء حساب جديد",
                                on_click=lambda e: page.go("/register"),
                                style=ButtonStyle(color=self.secondary_color)
                            ),
                            TextButton(
                                "نسيت كلمة المرور؟",
                                on_click=lambda e: page.go("/forgot-password"),
                                style=ButtonStyle(color=self.error_color)
                            ),
                            self.error_text,
                            Text('Develeper: Boudadi.Mekki.GST99',size=20)
                        ],
                        spacing=20,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    ),
                    padding=20,
                    alignment=alignment.center
                )
            ],
            bgcolor=colors.with_opacity(0.95, colors.GREY_50),
            vertical_alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER
        )

    def login_clicked(self, e):
        user = self.db.login_user(self.username.value, self.password.value)
        if user:
            self.page.session.set("user_id", user[0])
            self.page.session.set("username", user[1])
            self.page.go("/home")
        else:
            self.error_text.value = "اسم المستخدم أو كلمة المرور غير صحيحة"
            self.page.update()

class RegisterPage:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        
        self.primary_color = "#4a6fa5"
        self.secondary_color = "#166088"
        
        self.username = TextField(label="اسم المستخدم", width=300)
        self.email = TextField(label="البريد الإلكتروني", width=300)
        self.password = TextField(label="كلمة المرور", password=True, width=300)
        self.confirm_password = TextField(label="تأكيد كلمة المرور", password=True, width=300)
        self.error_text = Text("", color=colors.RED)
        
        self.view = View(
            "/register",
            [
                Container(
                    content=Column(
                        [
                            Text("إنشاء حساب جديد", size=24, weight=FontWeight.BOLD),
                            self.username,
                            self.email,
                            self.password,
                            self.confirm_password,
                            ElevatedButton(
                                "تسجيل",
                                on_click=self.register_clicked,
                                bgcolor=self.primary_color
                            ),
                            TextButton(
                                "لديك حساب؟ تسجيل الدخول",
                                on_click=lambda e: page.go("/")
                            ),
                            self.error_text
                        ],
                        spacing=20,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    ),
                    padding=20,
                    alignment=alignment.center
                )
            ],
            bgcolor=colors.with_opacity(0.95, colors.GREY_50)
        )

    def register_clicked(self, e):
        if self.password.value != self.confirm_password.value:
            self.error_text.value = "كلمات المرور غير متطابقة"
            self.page.update()
            return
            
        if len(self.password.value) < 6:
            self.error_text.value = "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
            self.page.update()
            return
            
        if self.db.register_user(self.username.value, self.email.value, self.password.value):
            self.page.go("/")
        else:
            self.error_text.value = "اسم المستخدم أو البريد الإلكتروني موجود بالفعل"
            self.page.update()

class ForgotPasswordPage:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        
        self.email = TextField(label="البريد الإلكتروني", width=300)
        self.error_text = Text("", color=colors.RED)
        self.success_text = Text("", color=colors.GREEN)
        
        self.view = View(
            "/forgot-password",
            [
                Container(
                    content=Column(
                        [
                            Text("استعادة كلمة المرور", size=24, weight=FontWeight.BOLD),
                            self.email,
                            ElevatedButton(
                                "إرسال رابط الاستعادة",
                                on_click=self.send_reset_link,
                                bgcolor="#4a6fa5"
                            ),
                            TextButton(
                                "العودة لتسجيل الدخول",
                                on_click=lambda e: page.go("/")
                            ),
                            self.error_text,
                            self.success_text
                        ],
                        spacing=20,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    ),
                    padding=20,
                    alignment=alignment.center
                )
            ],
            bgcolor=colors.with_opacity(0.95, colors.GREY_50)
        )

    def send_reset_link(self, e):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        self.db.set_reset_token(self.email.value, token)
        
        if EmailService.send_reset_email(self.email.value, token):
            self.success_text.value = "تم إرسال رابط إعادة التعيين إلى بريدك الإلكتروني"
            self.error_text.value = ""
        else:
            self.error_text.value = "حدث خطأ أثناء إرسال البريد الإلكتروني"
        
        self.page.update()

class ResetPasswordPage:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        
        self.token = page.route.split("=")[1] if "=" in page.route else ""
        self.user = self.db.get_user_by_token(self.token) if self.token else None
        
        self.new_password = TextField(label="كلمة المرور الجديدة", password=True, width=300)
        self.confirm_password = TextField(label="تأكيد كلمة المرور", password=True, width=300)
        self.error_text = Text("", color=colors.RED)
        
        self.view = View(
            "/reset-password",
            [
                Container(
                    content=Column(
                        [
                            Text("إعادة تعيين كلمة المرور", size=24, weight=FontWeight.BOLD),
                            self.new_password,
                            self.confirm_password,
                            ElevatedButton(
                                "تغيير كلمة المرور",
                                on_click=self.reset_password,
                                bgcolor="#4a6fa5"
                            ),
                            self.error_text
                        ],
                        spacing=20,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    ),
                    padding=20,
                    alignment=alignment.center
                )
            ],
            bgcolor=colors.with_opacity(0.95, colors.GREY_50)
        ) if self.user else View(
            "/reset-password",
            [
                Container(
                    content=Column(
                        [
                            Text("رابط غير صالح", size=24, weight=FontWeight.BOLD, color=colors.RED),
                            Text("رابط إعادة التعيين غير صالح أو منتهي الصلاحية", size=16),
                            TextButton(
                                "العودة لتسجيل الدخول",
                                on_click=lambda e: page.go("/")
                            )
                        ],
                        spacing=20,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    ),
                    padding=20,
                    alignment=alignment.center
                )
            ],
            bgcolor=colors.with_opacity(0.95, colors.GREY_50)
        )

    def reset_password(self, e):
        if self.new_password.value != self.confirm_password.value:
            self.error_text.value = "كلمات المرور غير متطابقة"
            self.page.update()
            return
            
        if len(self.new_password.value) < 6:
            self.error_text.value = "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
            self.page.update()
            return
            
        self.db.update_password(self.user[0], self.new_password.value)
        self.page.go("/")

class HomePage:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        
        # ألوان متناسقة
        self.primary_color = "#05BBE0"
        self.secondary_color = "#05BBE0"
        self.background_color = "#5DFA05"
        
        # حقول الإدخال
        self.lname = TextField(label="الاسم و اللقب", width=300, border_color=self.primary_color,rtl=True,bgcolor=colors.WHITE)
        self.ldate_send = TextField(label="تاريخ الادانة", width=300, border_color=self.primary_color,rtl=True,bgcolor=colors.WHITE)
        self.lmoney = TextField(label="القيمة بالدينار", width=300, border_color=self.primary_color,rtl=True,bgcolor=colors.WHITE)
        self.ltreason = TextField(label="سبب التدين", width=300, border_color=self.primary_color,rtl=True,bgcolor=colors.WHITE)
        self.ltime = TextField(label="مدة الارجاع", width=300, border_color=self.primary_color,rtl=True,bgcolor=colors.WHITE)
        self.ldate_up = TextField(label="تاريخ الارجاع", width=300, border_color=self.primary_color,rtl=True,bgcolor=colors.WHITE)
        
        # الأزرار
        self.new_add = ElevatedButton(
            'اضافة شخص جديد',
            on_click=self.add_new,
            bgcolor=self.primary_color,
            color=colors.WHITE
        )
        
        self.show_add = ElevatedButton(
            'صفحة العرض',
            on_click=lambda _: page.go('/cards'),
            bgcolor=self.secondary_color,
            color=colors.WHITE
        )
        
        self.clear_fields = ElevatedButton(
            'افراغ الحقول',
            on_click=self.clear_empty,
            bgcolor=colors.GREY_400
        )
        
        self.logout_btn = IconButton(
            icon=icons.LOGOUT,
            on_click=lambda e: self.logout(),
            icon_color=colors.RED_700
        )
        
        self.view = View(
            "/home",
            [
                AppBar(
                    title=Text("إدارة الديون", color=colors.WHITE,rtl=True),
                    bgcolor=self.primary_color,
                    actions=[self.logout_btn]
                ),
                Container(
                    content=Column(
                        [
                            Text("إضافة مدين جديد", size=20, weight=FontWeight.BOLD),
                            self.lname,
                            self.ldate_send,
                            self.lmoney,
                            self.ltreason,
                            self.ltime,
                            self.ldate_up,
                            Row([self.new_add, self.show_add], spacing=20),
                            self.clear_fields
                        ],
                        spacing=15,
                        scroll=ScrollMode.AUTO,
                        expand=True
                    ),
                    padding=20,
                    bgcolor=self.background_color,
                    expand=True,
                    rtl=True
                    
                )
            ]
        )

    def add_new(self, e):
        try:
            self.db.add_item(
                self.lname, self.ldate_send, self.lmoney, 
                self.ltreason, self.ltime, self.ldate_up
            )
            self.clear_empty(e)
            self.page.snack_bar = SnackBar(Text("تمت إضافة المدين بنجاح!"))
            self.page.snack_bar.open = True
        except Exception as ex:
            self.page.snack_bar = SnackBar(Text(f"حدث خطأ: {str(ex)}"))
            self.page.snack_bar.open = True
        self.page.update()

    def clear_empty(self, e):
        self.lname.value = ""
        self.ldate_send.value = ""
        self.lmoney.value = ""
        self.ltreason.value = ""
        self.ltime.value = ""
        self.ldate_up.value = ""
        self.page.update()
    
    def logout(self):
        self.page.session.clear()
        self.page.go("/")

class CardsPage:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        self.editing_id = None
        
        # ألوان متناسقة
        self.primary_color = "#1AF7FF"
        self.secondary_color = "#1AF7FF"
        self.background_color = "#121212"
        
        # حقول التعديل
        self.edit_lname = TextField(label="الاسم و اللقب", width=300,bgcolor=colors.WHITE,rtl=True ,visible=False)
        self.edit_ldate_send = TextField(label="تاريخ الادانة", width=300,bgcolor=colors.WHITE,rtl=True, visible=False)
        self.edit_lmoney = TextField(label="القيمة بالدينار", width=300,bgcolor=colors.WHITE,rtl=True, visible=False)
        self.edit_ltreason = TextField(label="سبب التدين", width=300,bgcolor=colors.WHITE,rtl=True, visible=False)
        self.edit_ltime = TextField(label="مدة الارجاع", width=300,bgcolor=colors.WHITE,rtl=True, visible=False)
        self.edit_ldate_up = TextField(label="تاريخ الارجاع", width=300,bgcolor=colors.WHITE,rtl=True, visible=False)
        
        self.save_edit_btn = ElevatedButton(
            "حفظ التعديلات",
            on_click=self.save_edit,
            bgcolor=self.primary_color,
            color=colors.WHITE,
            visible=False
        )
        
        self.cancel_edit_btn = ElevatedButton(
            "إلغاء",
            on_click=self.cancel_edit,
            bgcolor=colors.GREY_400,
            visible=False
        )
        
        self.back_btn = ElevatedButton(
            "العودة للصفحة الرئيسية",
            on_click=lambda _: page.go("/home"),
            bgcolor=self.secondary_color,
            color=colors.WHITE
        )
        
        self.search_field = TextField(
            label="ابحث بالاسم",
            bgcolor=colors.WHITE,
            on_change=self.filter_cards,
            width=300,
            rtl=True,
            border_color=self.primary_color,
            suffix_icon=icons.SEARCH
        )
        
        self.cards_column = Column(scroll=ScrollMode.AUTO, expand=True)
        self.refresh_cards()
        
        self.view = View(
            "/cards",
            [
                AppBar(
                    title=Text("قائمة المدينين", color='#FA0011'),
                    bgcolor=self.primary_color,
                    rtl=True
                ),
                Container(
                    content=Column(
                        [
                            self.search_field,
                            Row(
                                [
                                    self.edit_lname,
                                    self.edit_ldate_send,
                                    self.edit_lmoney
                                ],
                                wrap=True
                            ),
                            Row(
                                [
                                    self.edit_ltreason,
                                    self.edit_ltime,
                                    self.edit_ldate_up
                                ],
                                wrap=True
                            ),
                            Row(
                                [
                                    self.save_edit_btn,
                                    self.cancel_edit_btn
                                ],
                                spacing=20
                            ),
                            self.cards_column,
                            self.back_btn
                        ],
                        spacing=20,
                        expand=True
                    ),
                    padding=20,
                    bgcolor=self.background_color,
                    expand=True
                )
            ]
        )

    def refresh_cards(self, filter_text=None):
        self.cards_column.controls.clear()
        data = self.db.get_all_items()
        
        for person in data:
            if filter_text and filter_text.lower() not in person[1].lower():
                continue
                
            card = CardWidget(
                person,
                on_edit=self.start_edit,
                on_delete=self.delete_card
            )
            self.cards_column.controls.append(card.card)
        
        self.page.update()

    def filter_cards(self, e):
        self.refresh_cards(self.search_field.value)

    def start_edit(self, person):
        self.editing_id = person[0]
        self.edit_lname.value = person[1]
        self.edit_ldate_send.value = person[2]
        self.edit_lmoney.value = person[3]
        self.edit_ltreason.value = person[4]
        self.edit_ltime.value = person[5]
        self.edit_ldate_up.value = person[6]
        
        self.edit_lname.visible = True
        self.edit_ldate_send.visible = True
        self.edit_lmoney.visible = True
        self.edit_ltreason.visible = True
        self.edit_ltime.visible = True
        self.edit_ldate_up.visible = True
        self.save_edit_btn.visible = True
        self.cancel_edit_btn.visible = True
        
        self.page.update()

    def save_edit(self, e):
        self.db.update_item(
            self.editing_id,
            self.edit_lname.value,
            self.edit_ldate_send.value,
            self.edit_lmoney.value,
            self.edit_ltreason.value,
            self.edit_ltime.value,
            self.edit_ldate_up.value
        )
        
        self.cancel_edit(e)
        self.refresh_cards()
        self.page.snack_bar = SnackBar(Text("تم تحديث البيانات بنجاح!"))
        self.page.snack_bar.open = True
        self.page.update()

    def cancel_edit(self, e):
        self.editing_id = None
        self.edit_lname.visible = False
        self.edit_ldate_send.visible = False
        self.edit_lmoney.visible = False
        self.edit_ltreason.visible = False
        self.edit_ltime.visible = False
        self.edit_ldate_up.visible = False
        self.save_edit_btn.visible = False
        self.cancel_edit_btn.visible = False
        
        self.edit_lname.value = ""
        self.edit_ldate_send.value = ""
        self.edit_lmoney.value = ""
        self.edit_ltreason.value = ""
        self.edit_ltime.value = ""
        self.edit_ldate_up.value = ""
        
        self.page.update()
#*************************************************************مسح العنصر عن طريق ايدي *********************************
    def delete_card(self,card_id):
        def confirm_delete():
            self.db.delete_item(card_id)
            self.refresh_cards()
            self.page.snack_bar = SnackBar(Text("تم حذف المدين بنجاح!"))
            self.page.snack_bar.open = True
            self.page.update()
            #self.page.dialog.open = False
            self.page.update()
        confirm_delete()
        
        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()
        
        # self.page.dialog= AlertDialog(
        #     title=Text("تأكيد الحذف"),
        #     content=Text("هل أنت متأكد من حذف هذا المدين؟"),
        #     actions=[
        #         TextButton("حذف", on_click=confirm_delete),
        #         TextButton("إلغاء", on_click=cancel_delete)
        #     ]
        # )
        # self.page.dialog.open = True
        self.page.update()

def main(page: Page):
    # إعدادات الصفحة
    page.title = "تطبيق إدارة الديون"
    page.window.width = 600
    page.window.height = 900
    page.window.min_width = 600
    page.window.min_height = 400
    page.theme_mode = ThemeMode.LIGHT
    page.fonts = {
        "CustomFont": "fonts/NotoNaskhArabic-Regular.ttf"
    }
    page.theme = Theme(font_family="CustomFont")
    
    db = Database()

    def route_change(e):
        page.views.clear()
        
        if page.route == "/" or page.route == "/login":
            login_page = LoginPage(page, db)
            page.views.append(login_page.view)
            
        elif page.route == "/register":
            register_page = RegisterPage(page, db)
            page.views.append(register_page.view)
            
        elif page.route == "/forgot-password":
            forgot_page = ForgotPasswordPage(page, db)
            page.views.append(forgot_page.view)
            
        elif page.route.startswith("/reset-password"):
            reset_page = ResetPasswordPage(page, db)
            page.views.append(reset_page.view)
            
        elif page.route == "/home":
            if not page.session.get("user_id"):
                page.go("/")
                return
            home_page = HomePage(page, db)
            page.views.append(home_page.view)
            
        elif page.route == "/cards":
            if not page.session.get("user_id"):
                page.go("/")
                return
            cards_page = CardsPage(page, db)
            page.views.append(cards_page.view)
        
        page.update()

    page.on_route_change = route_change
    page.go("/login")

app(target=main)
