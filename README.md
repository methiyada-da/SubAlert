# SubAlert

> **สถานะโปรเจกต์: อยู่ระหว่างการพัฒนา (Work in Progress / In Development)**

## สถานะโปรเจกต์

SubAlert ยังอยู่ระหว่างการพัฒนา ฟีเจอร์บางส่วนยังไม่สมบูรณ์ และยังไม่ใช่ระบบที่พร้อมใช้งานในระดับ Production

## เกี่ยวกับโปรเจกต์

SubAlert เป็นเว็บแอปพลิเคชันที่พัฒนาด้วย Django สำหรับรวบรวมและจัดการข้อมูล Subscription และ Free Trial ไว้ในที่เดียว ช่วยให้ผู้ใช้ที่เข้าสู่ระบบแล้วสามารถตรวจสอบบริการที่กำลังใช้งาน วันตัดรอบครั้งถัดไป และวันสิ้นสุดช่วงทดลองใช้ฟรี พร้อมส่วนแสดงการแจ้งเตือนที่ยังอยู่ในระยะเริ่มต้นและการเชื่อมต่อบัญชี LINE

## ฟีเจอร์ที่ใช้งานได้ในปัจจุบัน

- สมัครสมาชิก เข้าสู่ระบบ และออกจากระบบ
- แก้ไขโปรไฟล์และเปลี่ยนรหัสผ่าน
- จัดการ Subscription แบบชำระเงินและ Free Trial
- คำนวณวันตัดรอบโดยคำนึงถึงจำนวนวันจริงในแต่ละเดือนและปีอธิกสุรทิน
- Dashboard แยกตามผู้ใช้ พร้อมการค้นหาและกรองรายการ Subscription
- ตรวจสอบความเป็นเจ้าของข้อมูลก่อนดูรายละเอียด แก้ไข ปิดการติดตาม เปลี่ยนจาก Free Trial เป็นแบบชำระเงิน และลบ Subscription
- เชื่อมบัญชี LINE เข้ากับบัญชี SubAlert ที่ผ่านการเข้าสู่ระบบแล้ว
- รองรับ LINE webhook ที่ตรวจสอบลายเซ็นสำหรับเหตุการณ์ follow และ unfollow
- ส่งข้อความทดสอบผ่าน LINE ไปยังบัญชีที่เชื่อมต่อแล้ว
- แสดงรายการแจ้งเตือนภายในเว็บและทำเครื่องหมายรายการที่มีอยู่ทั้งหมดว่าอ่านแล้ว

## ฟีเจอร์ที่กำลังพัฒนา

- การตั้งเวลาสร้างการแจ้งเตือนอัตโนมัติ
- Workflow แบบครบวงจรสำหรับสร้างและส่งการแจ้งเตือนวันตัดรอบและวันสิ้นสุด Free Trial
- การส่งซ้ำเมื่อเกิดข้อผิดพลาดและการติดตามสถานะการทำงานของระบบแจ้งเตือน

Workflow เหล่านี้ยังพัฒนาไม่เสร็จใน source ปัจจุบัน และยังไม่ถือเป็นฟีเจอร์ที่สมบูรณ์

## Tech Stack

- Python 3.13
- Django 6.1
- SQLite สำหรับการพัฒนาในเครื่อง
- HTML, CSS และ Vanilla JavaScript
- LINE Login and LINE Messaging APIs
- `python-dotenv` สำหรับจัดการ Environment Variables ในเครื่อง

## โครงสร้างโปรเจกต์

```text
accounts/       Authentication, โปรไฟล์, การจัดการรหัสผ่าน และการเชื่อมบัญชี LINE
config/         การตั้งค่าโปรเจกต์ Django และ การกำหนด URL หลักของโปรเจก
dashboard/      Dashboard แยกตามผู้ใช้
notifications/  Notification model, การแสดงผลบน top bar และสถานะการอ่าน
subscriptions/  Models, forms, views, date logic และ URLs สำหรับ Subscription
static/         ไฟล์ CSS และ JavaScript
templates/      Django templates ส่วนกลางและแยกตามแอป
```

## การติดตั้ง

1. Clone repository และเข้าไปที่ไดเรกทอรีของโปรเจกต์
2. สร้างและเปิดใช้งาน Python virtual environment
3. ติดตั้ง dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. คัดลอก `.env.example` เป็น `.env` และแทนที่ safe placeholders ด้วยค่าที่ใช้ในเครื่อง
5. ใช้งาน migrations:

   ```bash
   python manage.py migrate
   ```

6. เริ่ม local development server:

   ```bash
   python manage.py runserver
   ```

การตั้งค่าตัวอย่างเริ่มต้นรองรับการพัฒนาผ่าน HTTP ในเครื่องที่ `127.0.0.1` และ `localhost`

## Environment Variables

แอปรองรับ Environment Variables ต่อไปนี้ ค่า secret ต้องจัดเก็บไว้เฉพาะใน environment ของเครื่องหรือระบบ deployment และห้าม commit ลง Git

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE
SECURE_SSL_REDIRECT
SECURE_HSTS_SECONDS
SECURE_HSTS_INCLUDE_SUBDOMAINS
SECURE_HSTS_PRELOAD
EMAIL_BACKEND
LINE_LOGIN_CHANNEL_ID
LINE_LOGIN_CHANNEL_SECRET
LINE_CALLBACK_URL
LINE_MESSAGING_CHANNEL_SECRET
LINE_MESSAGING_CHANNEL_ACCESS_TOKEN
```

`ALLOWED_HOSTS` และ `CSRF_TRUSTED_ORIGINS` เป็นรายการที่คั่นด้วยเครื่องหมาย comma ส่วนค่า Boolean รองรับ `1`, `true`, `yes` หรือ `on` สำหรับค่า true โดย local development ใช้ console email backend เป็นค่าเริ่มต้น และ environment ที่ deploy ต้องกำหนด production backend ที่เหมาะสม

## LINE Integration

LINE flow ปัจจุบันใช้สำหรับเชื่อมบัญชี LINE เข้ากับผู้ใช้ SubAlert ที่ login อยู่แล้ว โดย **ไม่ใช่การ Login เข้า SubAlert ด้วย LINE**

ผู้พัฒนาต้องสร้าง channel ที่เกี่ยวข้องใน LINE Developers Console กำหนด channel credentials ผ่าน Environment Variables และตั้งค่า `LINE_CALLBACK_URL` ให้ตรงกับ callback ที่ลงทะเบียนไว้ทุกตัวอักษร สำหรับ Production ต้องใช้ stable HTTPS callback URL ส่วน temporary tunnel ควรใช้เฉพาะระหว่างการพัฒนา

Webhook endpoint จะตรวจสอบ LINE signature ก่อนอัปเดตสถานะ follow ของบัญชีที่เชื่อมต่อ และห้าม commit LINE access token หรือ channel secret ลง repository

## การทดสอบ

ปัจจุบันโปรเจกต์มี automated Django tests จำนวน 88 tests ครอบคลุม Authentication, การจัดการโปรไฟล์, LINE Integration, Subscription, การแยกข้อมูลบน Dashboard ตามผู้ใช้ และพฤติกรรมของระบบแจ้งเตือนที่มีอยู่ในปัจจุบัน

รันการตรวจสอบด้วยคำสั่ง:

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## ข้อจำกัดปัจจุบัน

- Notification scheduling และการส่งข้อความแจ้งเตือนอัตโนมัติยังไม่ถูกพัฒนาให้ทำงานครบวงจร
- ฐานข้อมูลเริ่มต้นออกแบบมาสำหรับ local development ไม่ใช่ production deployment
- Environment ที่ใช้ deploy ต้องจัดเตรียม Production hosting, email delivery, HTTPS และ public host configuration
- Automated tests ยังไม่ครอบคลุมพฤติกรรมของ JavaScript ในระดับ browser
- UI และ styles ยังอาจมีการเปลี่ยนแปลงระหว่างการพัฒนา

## Security / Privacy

- `.env`, ฐานข้อมูล SQLite ในเครื่อง, virtual environments, caches, logs, uploads และ generated static output ถูกแยกออกจาก version control
- ตัวอย่างใน repository มีเฉพาะชื่อ variables และ safe placeholders
- Production deployment ต้องใช้ `DJANGO_SECRET_KEY` ใหม่ที่มีความปลอดภัยสูง, cookies ที่ส่งผ่าน HTTPS เท่านั้น, HTTPS redirect, HSTS, host name ที่เสถียร และ production email backend
- ห้ามเผยแพร่ฐานข้อมูลในเครื่อง เพราะอาจมีข้อมูลบัญชี อีเมล LINE user ID, session และข้อมูล Subscription

## ผู้พัฒนา / ความรับผิดชอบ

**ผู้พัฒนา:** Methiyada

SubAlert เป็น Mini Project งานเดี่ยว โดยรับผิดชอบงานดังต่อไปนี้:

- วิเคราะห์ความต้องการและออกแบบข้อมูล
- พัฒนา Django backend
- พัฒนา Authentication / Authorization
- ออกแบบและพัฒนา Subscription workflows
- พัฒนา LINE Integration
- พัฒนา UI
- เขียน Automated tests
- จัดทำ Documentation
