import pydicom
import os
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DICOM_DIR = Path("PPMI/100878/3D_T1-weighted/2023-05-09_09_37_59.0/I1704600")
OUTPUT_DIR = DICOM_DIR / "out_put_I1704600"
TEMPLATE_PATH = Path("/home/vi0let/Рабочий стол/PD/mni_icbm152_nlin_sym_09a/mni_icbm152_gm_tal_nlin_sym_09a.nii")


# =============================================
# 1. Конвертация DICOM в NIfTI
# =============================================
def convert_dicom_to_nifti(dicom_dir, output_dir):
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run([
            "dcm2niix",
            "-o", str(output_dir),
            "-z", "y",
            str(dicom_dir)
        ], capture_output=True, text=True, check=True)

        logging.info("Конвертация DICOM в NIfTI завершена.")
        nifti_files = list(output_dir.glob("*.nii.gz"))
        if not nifti_files:
            raise FileNotFoundError("NIfTI-файл не найден после конвертации.")

        return nifti_files[0]  
    except Exception as e:
        logging.error(f"Ошибка конвертации: {e}")
        exit(1)


# =============================================
# 2. Предобработка (обрезка черепа)
# =============================================
def preprocess_nifti(input_path, output_dir):
    try:
        output_path = output_dir / "preprocessed.nii.gz"
        
        subprocess.run([
            "bet", str(input_path), str(output_path),
            "-R",
        ], check=True)
        
        logging.info("Предобработка завершена.")
        return output_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка предобработки: {e}")
        exit(1)


# =============================================
# 3. Регистрация в MNI пространство (через FSL)
# =============================================
def register_to_mni(input_path, template_path, output_dir):
    try:
        affine_mat = output_dir / "affine.mat"
        affine_reg = output_dir / "affine_reg.nii.gz"
        
        subprocess.run([
            "flirt",
            "-in", str(input_path),
            "-ref", str(template_path),
            "-omat", str(affine_mat),
            "-out", str(affine_reg)
        ], check=True)
        
        nonlinear_reg = output_dir / "nonlinear_reg.nii.gz"
        subprocess.run([
            "fnirt",
            "--in=" + str(input_path),
            "--ref=" + str(template_path),
            "--aff=" + str(affine_mat),
            "--iout=" + str(nonlinear_reg)
        ], check=True)
        
        logging.info("Регистрация в MNI завершена.")
        return nonlinear_reg
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка регистрации: {e}")
        exit(1)


# === Основной процесс ===
nifti_path = convert_dicom_to_nifti(DICOM_DIR, OUTPUT_DIR)
preprocessed_path = preprocess_nifti(nifti_path, OUTPUT_DIR)
registered_path = register_to_mni(preprocessed_path, TEMPLATE_PATH, OUTPUT_DIR)
