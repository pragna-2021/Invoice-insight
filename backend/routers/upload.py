from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import time
from .. import database, models, security
from ..services import pdf_handler, ocr_engine, structurer

router = APIRouter()

@router.post("/")
async def upload_invoice(
    file: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    start_time = time.time()
    
    # 1. Validation
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, JPG, and PNG are supported.")
    
    content = await file.read()
    
    # Create DB entry
    db_invoice = models.Invoice(
        user_id=current_user.id,
        filename=file.filename,
        status="processing"
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    try:
        # 2. Extract Images (PDF pages or single image)
        images = []
        if file.filename.lower().endswith('.pdf'):
            images = pdf_handler.pdf_to_images(content)
        else:
            images = [content]
        
        # 3. Process & OCR
        raw_text_parts = []
        translated_text_parts = []
        ocr_accuracies = []
        translation_accuracies = []
        detected_languages = []
        
        for img_bytes in images:
            # Process page
            raw, trans, ocr_acc, lang, trans_acc = ocr_engine.extract_and_translate(img_bytes)
            raw_text_parts.append(raw)
            translated_text_parts.append(trans)
            ocr_accuracies.append(ocr_acc)
            translation_accuracies.append(trans_acc)
            detected_languages.append(lang)
                 
        full_raw_text = "\n\n--- Page Break ---\n\n".join(raw_text_parts)
        full_translated_text = "\n\n--- Page Break ---\n\n".join(translated_text_parts)
        
        # Aggregate metrics
        avg_ocr_accuracy = sum(ocr_accuracies) / len(ocr_accuracies) if ocr_accuracies else 0.0
        avg_trans_accuracy = sum(translation_accuracies) / len(translation_accuracies) if translation_accuracies else 0.0
        overall_lang = "ru" if "ru" in detected_languages else "en"
        
        # 4. Structure Data
        structured_data = structurer.parse_invoice(full_translated_text)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update DB
        db_invoice.raw_text = full_raw_text
        db_invoice.translated_text = full_translated_text
        db_invoice.raw_extracted_data = structured_data  # Store initial extraction
        db_invoice.structured_data = structured_data      # Store current/editable extraction
        db_invoice.language = overall_lang
        db_invoice.ocr_accuracy = avg_ocr_accuracy
        db_invoice.translation_accuracy = avg_trans_accuracy
        db_invoice.status = "completed"
        db_invoice.processing_time_ms = processing_time_ms
        db_invoice.success = True
        
        db.commit()
        db.refresh(db_invoice)
        
        return {
            "message": "Invoice processed successfully",
            "invoice_id": db_invoice.id,
            "data": structured_data,
            "language": overall_lang,
            "ocr_accuracy": avg_ocr_accuracy,
            "translation_accuracy": avg_trans_accuracy,
            "processing_time_ms": processing_time_ms
        }
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        db_invoice.status = "failed"
        db_invoice.success = False
        db_invoice.error_log = str(e)
        db_invoice.processing_time_ms = processing_time_ms
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
