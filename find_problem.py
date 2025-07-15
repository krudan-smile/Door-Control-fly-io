import os
import chardet

def find_problematic_files():
    problem_files = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # ลองอ่านไฟล์เป็น UTF-8
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read()
                print(f"✓ OK: {file_path}")
            except UnicodeDecodeError as e:
                print(f"✗ PROBLEM: {file_path} - {e}")
                problem_files.append(file_path)
            except Exception as e:
                print(f"? SKIP: {file_path} - {e}")
    
    return problem_files

if __name__ == "__main__":
    print("กำลังค้นหาไฟล์ที่มีปัญหา encoding...")
    problems = find_problematic_files()
    
    if problems:
        print(f"\nพบไฟล์ที่มีปัญหา {len(problems)} ไฟล์:")
        for file in problems:
            print(f"  - {file}")
    else:
        print("\nไม่พบไฟล์ที่มีปัญหา encoding")