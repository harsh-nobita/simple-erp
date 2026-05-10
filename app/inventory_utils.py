"""
Inventory Management Utilities
Handles stock alerts, batch tracking, and warehouse operations
"""
from app import db
from app.models import StockAlert, InventoryBatch, Item
from datetime import datetime

def check_and_create_stock_alerts(item_id):
    """
    Check if an item needs stock alerts and create them if necessary
    """
    item = Item.query.get(item_id)
    if not item:
        return

    # Clear old unresolved alerts for this item
    StockAlert.query.filter_by(item_id=item_id, is_resolved=False).delete()

    alerts_created = []

    # Check for low stock
    if item.is_low_stock():
        alert = StockAlert(
            item_id=item_id,
            alert_type='low_stock',
            message=f"Item '{item.name}' is below reorder point ({item.quantity}/{item.reorder_point})"
        )
        db.session.add(alert)
        alerts_created.append('low_stock')

    # Check for overstock
    if item.is_overstock():
        alert = StockAlert(
            item_id=item_id,
            alert_type='overstock',
            message=f"Item '{item.name}' has exceeded maximum stock ({item.quantity}/{item.max_stock})"
        )
        db.session.add(alert)
        alerts_created.append('overstock')

    # Check for expired batches
    expired_batches = InventoryBatch.query.filter_by(item_id=item_id, is_active=True).all()
    for batch in expired_batches:
        if batch.is_expired():
            alert = StockAlert(
                item_id=item_id,
                alert_type='expired',
                message=f"Batch '{batch.batch_number}' has expired (Expiry: {batch.expiry_date})"
            )
            db.session.add(alert)
            alerts_created.append('expired')
            batch.is_active = False

    if alerts_created:
        db.session.commit()

    return alerts_created

def get_warehouse_stock(warehouse_id, item_id=None):
    """
    Get total stock in a warehouse, optionally filtered by item
    """
    query = InventoryBatch.query.filter_by(warehouse_id=warehouse_id, is_active=True)
    
    if item_id:
        query = query.filter_by(item_id=item_id)
    
    batches = query.all()
    total_stock = sum(b.quantity for b in batches if not b.is_expired())
    
    return {
        'total': total_stock,
        'batches': batches,
        'expired': sum(b.quantity for b in batches if b.is_expired())
    }

def transfer_stock(item_id, from_warehouse_id, to_warehouse_id, quantity, batch_number=None):
    """
    Transfer stock from one warehouse to another
    """
    try:
        if batch_number:
            # Transfer specific batch
            batch = InventoryBatch.query.filter_by(
                item_id=item_id,
                warehouse_id=from_warehouse_id,
                batch_number=batch_number,
                is_active=True
            ).first()
            
            if not batch:
                return {'success': False, 'message': 'Batch not found or inactive'}
            
            if batch.quantity < quantity:
                return {'success': False, 'message': f'Insufficient quantity in batch (Available: {batch.quantity})'}
            
            # Create new batch entry in destination
            new_batch = InventoryBatch(
                item_id=item_id,
                warehouse_id=to_warehouse_id,
                batch_number=batch.batch_number,
                serial_number=batch.serial_number,
                quantity=quantity,
                received_date=datetime.utcnow(),
                expiry_date=batch.expiry_date,
                supplier_id=batch.supplier_id,
                notes=f"Transferred from Warehouse {from_warehouse_id}"
            )
            
            batch.quantity -= quantity
            if batch.quantity == 0:
                batch.is_active = False
            
            db.session.add(new_batch)
        else:
            # Transfer from any available batch
            from_batches = InventoryBatch.query.filter_by(
                item_id=item_id,
                warehouse_id=from_warehouse_id,
                is_active=True
            ).order_by(InventoryBatch.received_date).all()
            
            remaining = quantity
            for batch in from_batches:
                if batch.is_expired():
                    continue
                
                transfer_qty = min(batch.quantity, remaining)
                
                new_batch = InventoryBatch(
                    item_id=item_id,
                    warehouse_id=to_warehouse_id,
                    batch_number=batch.batch_number,
                    serial_number=batch.serial_number,
                    quantity=transfer_qty,
                    received_date=datetime.utcnow(),
                    expiry_date=batch.expiry_date,
                    supplier_id=batch.supplier_id,
                    notes=f"Transferred from Warehouse {from_warehouse_id}"
                )
                
                batch.quantity -= transfer_qty
                if batch.quantity == 0:
                    batch.is_active = False
                
                db.session.add(new_batch)
                remaining -= transfer_qty
                
                if remaining == 0:
                    break
            
            if remaining > 0:
                return {'success': False, 'message': f'Insufficient stock (Needed: {quantity}, Available: {quantity - remaining})'}
        
        db.session.commit()
        return {'success': True, 'message': f'Successfully transferred {quantity} units'}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Transfer failed: {str(e)}'}

def get_low_stock_items():
    """
    Get all items that are below reorder point
    """
    items = Item.query.all()
    return [item for item in items if item.is_low_stock()]

def get_overstock_items():
    """
    Get all items that have exceeded max stock
    """
    items = Item.query.all()
    return [item for item in items if item.is_overstock()]

def get_active_stock_alerts():
    """
    Get all unresolved stock alerts
    """
    return StockAlert.query.filter_by(is_resolved=False).all()

def resolve_stock_alert(alert_id):
    """
    Mark a stock alert as resolved
    """
    alert = StockAlert.query.get(alert_id)
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        return True
    return False
