import pandas as pd
from django.core.management.base import BaseCommand
from store.models import Shoe

class Command(BaseCommand):
    help = 'Load shoe data from Excel file into the database'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='The path to the Excel file to be loaded')

    def handle(self, *args, **kwargs):
        excel_file = kwargs['excel_file']

        try:
            # ใช้ pandas ในการอ่านไฟล์ Excel
            data = pd.read_excel(excel_file, engine='openpyxl')

            # ตรวจสอบข้อมูลใน Excel และนำเข้าข้อมูลทีละแถว
            for index, row in data.iterrows():
                # ลบเครื่องหมาย $ และช่องว่างออกจากฟิลด์ราคา และแปลงเป็น float
                cleaned_price = row['Price (USD)'].replace('$', '').replace(',', '').strip()
                Shoe.objects.create(
                    brand=row['Brand'],
                    model=row['Model'],
                    shoe_type=row['Type'],
                    gender=row['Gender'],
                    size=row['Size'],
                    color=row['Color'],
                    material=row['Material'],
                    price=float(cleaned_price)  # แปลงเป็น float หลังจากล้างข้อมูล
                )
            self.stdout.write(self.style.SUCCESS('Data imported successfully from Excel'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File '{excel_file}' not found"))

        except KeyError as e:
            self.stdout.write(self.style.ERROR(f"KeyError: The key {e} was not found in the Excel file"))

        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"ValueError: {e}"))