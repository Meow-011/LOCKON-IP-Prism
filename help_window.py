import customtkinter as ctk

class HelpWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("วิธีใช้งาน / About LOCKON IP Prism")
        self.geometry("800x750") # ขยายความสูงเพื่อรองรับเนื้อหาใหม่
        self.transient(master)
        self.grab_set()

        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="คู่มือการใช้งาน LOCKON IP Prism")
        self.scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # ใช้ f-string และ triple quotes เพื่อสร้างข้อความหลายบรรทัด
        help_text = f"""
        LOCKON IP Prism คือโปรแกรมสำหรับวิเคราะห์และจัดการ IP Address ที่น่าสงสัย 
        โดยเชื่อมต่อกับฐานข้อมูล Threat Intelligence ภายนอก (IPQualityScore, AlienVault OTX) 
        เพื่อตรวจสอบชื่อเสียง (Reputation) และจัดเก็บผลลัพธ์เพื่อใช้ในการวิเคราะห์ข้อมูล
        ย้อนหลังและการทำรายงานเชิงลึก

        {"-"*90}

        เริ่มต้นใช้งาน (Quick Start)

        1. ตั้งค่า API Key (สำคัญมาก!):
           • สำหรับการใช้งานครั้งแรก ให้ไปที่เมนู [Settings] ที่มุมบนขวา
           • ใส่ Private API Key ของคุณที่ได้จากเว็บ:
             - IPQualityScore.com (จำเป็นต้องมี)
             - otx.alienvault.com (ไม่มีก็ได้ แต่แนะนำเพื่อข้อมูลเชิงลึก)
           • ตั้งค่า Cache Duration (จำนวนชั่วโมงที่โปรแกรมจะจำผลลัพธ์ไว้)

        2. เลือกไฟล์:
           • คลิกที่ปุ่ม [Select IP File (.txt, .log)] เพื่อเลือกไฟล์ที่ต้องการ
           • ไฟล์ .txt: ควรมี IP บรรทัดละหนึ่งอัน
           • ไฟล์ .log: โปรแกรมจะค้นหาและดึง IP ทั้งหมดจากในไฟล์ให้โดยอัตโนมัติ

        3. เพิ่มคำอธิบาย (แนะนำอย่างยิ่ง):
           • ใส่คำอธิบายสั้นๆ สำหรับไฟล์แต่ละชุด (เช่น "Week 32 Blocklist") เพื่อให้คุณ
             จำแนกข้อมูลในภายหลังได้ง่ายขึ้น

        4. เริ่มการวิเคราะห์:
           • คลิกที่ปุ่มใหญ่ [Start Analysis] โปรแกรมจะเริ่มประมวลผลและแสดงความคืบหน้า

        {"-"*90}

        การอ่านและตีความข้อมูล (Understanding the Data)

        Fraud Score (คะแนนความเสี่ยง):
        • มาจาก IPQualityScore เป็นคะแนน 0-100 ที่บ่งบอกระดับความเสี่ยงของ IP
        • 85 - 100: ความเสี่ยงสูงมาก (High Risk), มีแนวโน้มสูงที่จะเป็นอันตราย
        • 75 - 84: ความเสี่ยงปานกลาง (Medium Risk), น่าสงสัย, ควรจับตามอง
        • < 75: ความเสี่ยงต่ำ (Low Risk)
        • Max Fraud Score (ในรายงานเปรียบเทียบ): คือคะแนนความเสี่ยง "สูงสุด" ที่ IP นั้นเคยทำได้

        ISP (ผู้ให้บริการอินเทอร์เน็ต):
        • ชื่อของผู้ให้บริการอินเทอร์เน็ตของ IP นั้นๆ เช่น 'Digital Ocean', 'Google Cloud'
        • ช่วยให้ทราบว่า IP มาจาก Data Center หรือผู้ให้บริการตามบ้านทั่วไป

        Organization (องค์กร):
        • ชื่อขององค์กรที่เป็นเจ้าของ IP Address นั้นๆ

        OTX Pulses (ข้อมูลจาก AlienVault OTX):
        • "Pulse" คือ "รายงาน" เกี่ยวกับภัยคุกคามที่ถูกสร้างโดยชุมชนนักวิเคราะห์ทั่วโลก
        • ตัวเลขนี้คือ จำนวนรายงาน (Pulses) ทั้งหมดที่เคยมีการกล่าวถึง IP นี้
        • ยิ่งตัวเลขสูง ยิ่งหมายความว่า IP นี้เคยมีประวัติไม่ดี และถูกจับตามองโดยชุมชน
        • Max OTX Pulses (ในรายงานเปรียบเทียบ): คือจำนวน Pulses "สูงสุด" ที่ IP นั้นเคยมี

        Tags (แท็ก):
        • "ป้ายกำกับ" ที่คุณสามารถกำหนดเองได้ (โดยการคลิกขวาที่ IP -> Edit Details) 
          เพื่อจัดกลุ่มหรือบันทึกข้อมูลสำคัญ เช่น `APT28`, `Phishing`, `C2-Server`

        Notes (โน้ต):
        • พื้นที่สำหรับบันทึกข้อความหรือรายละเอียดเพิ่มเติมเกี่ยวกับ IP นั้นๆ

        {"-"*90}

        ความสามารถหลัก (Features)

        Dashboard: แสดงข้อมูลสรุปภาพรวมของฐานข้อมูลทั้งหมด
        • Color Coding: IP ที่มีความเสี่ยงสูง (Score > 85) จะเป็น สีแดง และที่น่าสงสัย (Score >= 75) จะเป็น สีเหลือง เพื่อให้สังเกตได้ง่าย
        • Recurrence Report: สร้างรายงานเปรียบเทียบ IP จาก "ไฟล์ล่าสุด" กับ "ไฟล์ก่อนหน้าทั้งหมด" เพื่อค้นหา "ผู้กระทำผิดซ้ำซาก"
        • Multi-Batch Compare: สร้างรายงานเปรียบเทียบ IP ระหว่างไฟล์ชุดใดๆ ที่คุณเลือก
        • Generate PDF / Export to CSV: สร้างรายงานสรุปในรูปแบบ PDF หรือไฟล์ตาราง CSV
        • Delete Batch: ลบข้อมูลของไฟล์ (Batch) ที่คุณเลือกใน Filter ทิ้งอย่างถาวร
        """

        self.label = ctk.CTkLabel(self.scrollable_frame, text=help_text, justify="left", anchor="nw", font=ctk.CTkFont(family="Tahoma", size=14))
        self.label.pack(padx=10, pady=10)

