# วิธีตั้งค่า Siri Shortcut สำหรับสั่ง Jarvis

คุณสามารถใช้ Siri บน Mac เพื่อรับเสียงแล้วส่งคำสั่งไปยัง Jarvis ได้โดยตรง วิธีนี้จะช่วยให้การรับเสียงแม่นยำขึ้นเพราะใช้ระบบของ Apple เอง

## ขั้นตอนการสร้าง Shortcut

1. เปิดแอป **Shortcuts** บน Mac
2. กดปุ่ม **+** เพื่อสร้าง Shortcut ใหม่ (ตั้งชื่อเช่น "สั่ง Jarvis" หรือ "Jarvis")
3. ค้นหาและลากคำสั่งต่างๆ มาวางดังนี้:

### 1. รับเสียงพูด
- ค้นหาคำสั่ง **Dictate Text** (บอกตามคำบอก)
- ลากมาวางเป็นขั้นตอนแรก
- ตั้งค่าภาษาเป็น **Thai** (หรือภาษาที่คุณถนัด)

### 2. ส่งคำสั่งไปที่ Jarvis
- ค้นหาคำสั่ง **Get Contents of URL** (รับเนื้อหาของ URL)
- ลากมาต่อจาก Dictate Text
- ตั้งค่าดังนี้:
  - **URL**: `http://localhost:8080/api/command`
  - **Method**: เปลี่ยนจาก GET เป็น **POST**
  - **Headers**: กดปุ่ม + แล้วเพิ่ม `Content-Type`: `application/json`
  - **Request Body**: เลือก **JSON**
  - กดเพิ่ม Field:
    - Key: `text`
    - Value: คลิกขวาเลือก **Select Variable** > เลือก **Dictated Text** (ข้อความที่บอก)

### 3. (ตัวเลือกเสริม) ให้ Siri พูดตอบกลับ
- ค้นหาคำสั่ง **Get Dictionary Value**
- ลากมาต่อ
- ตั้งค่า Key เป็น `response`
- ค้นหาคำสั่ง **Speak Text** (อ่านออกเสียง)
- ลากมาต่อ
- ให้มันอ่านค่าที่ได้จาก Dictionary Value

## วิธีใช้งาน
1. พูด "Hey Siri, Jarvis" (หรือชื่อ Shortcut ที่คุณตั้ง)
2. พูดคำสั่ง เช่น "เปิดเพลง Bodyslam", "หยุดเพลง", "ข้ามเพลง"
3. Jarvis จะทำงานทันที!

## หมายเหตุ
- ต้องรัน `python3 app.py` ทิ้งไว้
- ถ้าใช้ iPhone/iPad ต้องเปลี่ยน `localhost` เป็น IP ของเครื่อง Mac (เช่น `192.168.1.x`)
