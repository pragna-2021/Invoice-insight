from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import io
import csv
import json
from datetime import datetime
from .. import database, models, security

router = APIRouter()

@router.get("/metrics")
def get_metrics(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    invoices = db.query(models.Invoice).filter(models.Invoice.user_id == current_user.id).all()
    
    total = len(invoices)
    if total == 0:
        return {
            "total": 0,
            "success_rate": 0.0,
            "avg_processing_time_ms": 0.0,
            "avg_ocr_accuracy": 0.0,
            "avg_translation_accuracy": 0.0,
            "success_ratio": {"success": 0, "failed": 0},
            "processing_time_comparison": {"images_avg_ms": 0.0, "pdfs_avg_ms": 0.0},
            "accuracy_trends": [],
            "recent_invoices": [],
            "error_logs": []
        }
    
    successful = sum(1 for inv in invoices if inv.success)
    success_rate = (successful / total) * 100.0
    
    avg_time = sum(inv.processing_time_ms for inv in invoices) / total
    
    # Calculate OCR and translation accuracy averages
    completed_invoices = [inv for inv in invoices if inv.status == "completed" and inv.success]
    num_completed = len(completed_invoices)
    
    avg_ocr_accuracy = sum(inv.ocr_accuracy for inv in completed_invoices) / num_completed if num_completed > 0 else 0.0
    avg_translation_accuracy = sum(inv.translation_accuracy for inv in completed_invoices) / num_completed if num_completed > 0 else 0.0
    
    # Success vs failed counts
    failed = total - successful
    success_ratio = {"success": successful, "failed": failed}
    
    # Processing time comparison: Images vs PDFs
    image_times = [inv.processing_time_ms for inv in invoices if not inv.filename.lower().endswith('.pdf')]
    pdf_times = [inv.processing_time_ms for inv in invoices if inv.filename.lower().endswith('.pdf')]
    
    images_avg = sum(image_times) / len(image_times) if image_times else 0.0
    pdfs_avg = sum(pdf_times) / len(pdf_times) if pdf_times else 0.0
    
    # Accuracy trends (ordered by date)
    sorted_invoices = sorted(completed_invoices, key=lambda x: x.created_at)
    accuracy_trends = [
        {
            "date": inv.created_at.strftime("%Y-%m-%d %H:%M"),
            "ocr_accuracy": inv.ocr_accuracy,
            "translation_accuracy": inv.translation_accuracy
        }
        for inv in sorted_invoices
    ]
    
    # Recent invoices (last 10)
    recent_invoices = [
        {
            "id": inv.id,
            "filename": inv.filename,
            "status": inv.status,
            "created_at": inv.created_at.strftime("%Y-%m-%d %H:%M"),
            "success": inv.success,
            "processing_time_ms": inv.processing_time_ms,
            "ocr_accuracy": inv.ocr_accuracy,
            "language": inv.language,
            "total_amount": inv.structured_data.get("Total Amount") if inv.structured_data else None
        }
        for inv in sorted(invoices, key=lambda x: x.created_at, reverse=True)[:10]
    ]
    
    # Error logs
    error_logs = [
        {
            "id": inv.id,
            "filename": inv.filename,
            "error_log": inv.error_log,
            "created_at": inv.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for inv in invoices if not inv.success
    ]
    
    return {
        "total": total,
        "success_rate": success_rate,
        "avg_processing_time_ms": avg_time,
        "avg_ocr_accuracy": avg_ocr_accuracy,
        "avg_translation_accuracy": avg_translation_accuracy,
        "success_ratio": success_ratio,
        "processing_time_comparison": {"images_avg_ms": images_avg, "pdfs_avg_ms": pdfs_avg},
        "accuracy_trends": accuracy_trends,
        "recent_invoices": recent_invoices,
        "error_logs": error_logs
    }

@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    return {
        "id": invoice.id,
        "filename": invoice.filename,
        "status": invoice.status,
        "structured_data": invoice.structured_data,
        "raw_extracted_data": invoice.raw_extracted_data,
        "raw_text": invoice.raw_text,
        "translated_text": invoice.translated_text,
        "ocr_accuracy": invoice.ocr_accuracy,
        "translation_accuracy": invoice.translation_accuracy,
        "language": invoice.language,
        "error_log": invoice.error_log,
        "processing_time_ms": invoice.processing_time_ms,
        "created_at": invoice.created_at.strftime("%Y-%m-%d %H:%M")
    }

@router.put("/invoices/{invoice_id}/edit")
def edit_invoice(
    invoice_id: int, 
    updated_data: dict, 
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(database.get_db)
):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    raw = invoice.raw_extracted_data or {}
    
    # Calculate edit accuracy (comparison with original extraction)
    # Compare fields: Vendor Name, Invoice Date, Total Amount, Items List
    matches = 0
    total_fields = 4
    
    if str(raw.get("Vendor Name")).strip().lower() == str(updated_data.get("Vendor Name")).strip().lower():
        matches += 1
    if str(raw.get("Invoice Date")).strip().lower() == str(updated_data.get("Invoice Date")).strip().lower():
        matches += 1
    if str(raw.get("Total Amount")).strip().lower() == str(updated_data.get("Total Amount")).strip().lower():
        matches += 1
        
    # Check items list matching count
    raw_items = raw.get("Items List", [])
    upd_items = updated_data.get("Items List", [])
    if len(raw_items) == len(upd_items):
        matches += 1
    
    # Validation accuracy represents how close the initial OCR extraction matches user corrections
    validation_accuracy = (matches / total_fields) * 100.0
    
    invoice.structured_data = updated_data
    # We update the translation_accuracy to represent the post-human-review extraction accuracy
    invoice.translation_accuracy = validation_accuracy
    
    db.commit()
    db.refresh(invoice)
    
    return {"message": "Invoice updated successfully", "validation_accuracy": validation_accuracy}

@router.get("/invoices/{invoice_id}/export/{export_format}")
def export_invoice(
    invoice_id: int,
    export_format: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.user_id == current_user.id
    ).first()
    
    if not invoice or not invoice.structured_data:
        raise HTTPException(status_code=404, detail="Invoice structured data not found")
        
    data = invoice.structured_data
    
    if export_format == "json":
        json_str = json.dumps(data, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.json"}
        )
        
    elif export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write metadata
        writer.writerow(["Invoice Export", f"ID: {invoice.id}", f"File: {invoice.filename}"])
        writer.writerow(["Vendor Name", data.get("Vendor Name", "Unknown")])
        writer.writerow(["Invoice Date", data.get("Invoice Date", "Unknown")])
        writer.writerow(["Total Amount", data.get("Total Amount", "0.00")])
        writer.writerow([])
        
        # Write items list header
        writer.writerow(["Quantity", "Description", "Price"])
        for item in data.get("Items List", []):
            writer.writerow([item.get("Quantity"), item.get("Description"), item.get("Price")])
            
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.csv"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Only CSV and JSON are supported.")
