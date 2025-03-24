import os
import pandas as pd
from django.core.management.base import BaseCommand
from store.models import Shoe

class Command(BaseCommand):
    help = 'Import shoes data from Excel to database'

    def handle(self, *args, **kwargs):
        # กำหนด path ของไฟล์ Excel
        file_path = 'C:/Users/Pan_Pan/PycharmProjects/FLP0/shoe_store/media/Shoe_prices0.xlsx'  # แก้ไขเป็น path ของไฟล์คุณ

        # อ่านข้อมูลจาก Excel
        df = pd.read_excel(file_path)

        # แปลงราคาจาก string เป็นตัวเลข
        df["Price (USD)"] = df["Price (USD)"].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df['Price (USD)'] = pd.to_numeric(df['Price (USD)'], errors='coerce')
        df['Price (USD)'] = df['Price (USD)'].fillna(0)

        # เพิ่มข้อมูลจาก DataFrame ลงในฐานข้อมูล
        for index, row in df.iterrows():
            shoe = Shoe(
                brand=row['Brand'],
                model=row['Model'],
                shoe_type=row['Type'],
                gender=row['Gender'],
                size=row['Size'],
                color=row['Color'],
                material=row['Material'],
                price=row['Price (USD)'],
                image=row['Image_URL']
            )
            shoe.save()
            self.stdout.write(self.style.SUCCESS(f"Inserted: {shoe}"))
