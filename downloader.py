import os
import subprocess

def setup_all():
    if not os.path.exists("Wav2Lip"):
        print("[Setup] Đang tải mã nguồn Wav2Lip...")
        subprocess.run(["git", "clone", "https://github.com/Rudrabha/Wav2Lip.git"], check=True)
        
        os.makedirs("Wav2Lip/face_detection/detection", exist_ok=True)
        os.makedirs("Wav2Lip/checkpoints", exist_ok=True)
        
        print("[Setup] Đang tải Model nhận diện khuôn mặt (S3FD)...")
        subprocess.run(["wget", "-O", "Wav2Lip/face_detection/detection/sfd_face.pth", 
                        "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"], check=True)
        
        print("[Setup] Đang tải Model Wav2Lip GAN...")
        # Sử dụng gdown để tải từ Google Drive (Link gốc của tác giả)
        subprocess.run(["pip", "install", "gdown"], check=True)
        subprocess.run(["gdown", "--id", "17zHNQ3KJYDPKpHStcrpdD_T8B_6v_B9X", "-O", "Wav2Lip/checkpoints/wav2lip_gan.pth"])
        
        print("[Setup] Cập nhật Wav2Lip requirements (Bỏ khoá version cũ)...")
        import re
        with open("Wav2Lip/requirements.txt", "r") as f:
            reqs = f.read()
        reqs = re.sub(r'==.*', '', reqs)
        with open("Wav2Lip/requirements.txt", "w") as f:
            f.write(reqs)
            
        print("[Setup] Cài đặt dependencies phụ...")
        subprocess.run(["pip", "install", "-r", "Wav2Lip/requirements.txt"], check=True)
        print("[Setup] Hoàn tất tải module!")
    else:
        print("[Setup] Module Wav2Lip đã tồn tại. Bỏ qua tải.")

if __name__ == "__main__":
    setup_all()
