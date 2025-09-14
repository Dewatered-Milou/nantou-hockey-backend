from flask import Blueprint, request, jsonify
#from models.user import db
import sqlite3
import os
from datetime import datetime
import uuid

tickets_bp = Blueprint('tickets', __name__)

# 票種資訊
TICKET_TYPES = {
    'general': {'name': '一般票', 'price': 500},
    'premium': {'name': '精緻票', 'price': 1200},
    'vip': {'name': 'VIP票', 'price': 2500},
    'family': {'name': '家庭套票', 'price': 1800}
}

# 購票API
@tickets_bp.route('/purchase', methods=['POST'])
def purchase_tickets():
    try:
        data = request.get_json()
        
        # 驗證必要欄位
        required_fields = ['firstName', 'email', 'phone', 'idNumber', 'paymentMethod', 'tickets']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'缺少必要欄位: {field}'}), 400
        
        # 驗證票種和數量
        tickets = data['tickets']
        total_amount = 0
        ticket_details = []
        
        for ticket_id, quantity in tickets.items():
            if ticket_id not in TICKET_TYPES:
                return jsonify({'error': f'無效的票種: {ticket_id}'}), 400
            
            if quantity <= 0:
                continue
                
            ticket_info = TICKET_TYPES[ticket_id]
            subtotal = ticket_info['price'] * quantity
            total_amount += subtotal
            
            ticket_details.append({
                'type': ticket_id,
                'name': ticket_info['name'],
                'price': ticket_info['price'],
                'quantity': quantity,
                'subtotal': subtotal
            })
        
        if not ticket_details:
            return jsonify({'error': '請選擇至少一張票'}), 400
        
        # 生成訂單編號
        order_id = str(uuid.uuid4())[:8].upper()
        
        # 連接資料庫
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 建立訂單表格（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                id_number TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                total_amount INTEGER NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                ticket_type TEXT NOT NULL,
                ticket_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES ticket_orders (order_id)
            )
        ''')
        
        # 插入訂單資料
        cursor.execute('''
            INSERT INTO ticket_orders 
            (order_id, first_name, email, phone, id_number, payment_method, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id,
            data['firstName'],
            data['email'],
            data['phone'],
            data['idNumber'],
            data['paymentMethod'],
            total_amount
        ))
        
        # 插入票券明細
        for ticket in ticket_details:
            cursor.execute('''
                INSERT INTO ticket_items 
                (order_id, ticket_type, ticket_name, price, quantity, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                order_id,
                ticket['type'],
                ticket['name'],
                ticket['price'],
                ticket['quantity'],
                ticket['subtotal']
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '購票成功！',
            'orderId': order_id,
            'totalAmount': total_amount,
            'tickets': ticket_details
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'購票失敗: {str(e)}'}), 500

# 查詢訂單
@tickets_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查詢訂單基本資訊
        cursor.execute('''
            SELECT order_id, first_name, email, phone, total_amount, 
                   order_date, status
            FROM ticket_orders
            WHERE order_id = ?
        ''', (order_id,))
        
        order_row = cursor.fetchone()
        if not order_row:
            conn.close()
            return jsonify({'error': '找不到指定的訂單'}), 404
        
        # 查詢票券明細
        cursor.execute('''
            SELECT ticket_type, ticket_name, price, quantity, subtotal
            FROM ticket_items
            WHERE order_id = ?
        ''', (order_id,))
        
        ticket_items = []
        for row in cursor.fetchall():
            ticket_items.append({
                'type': row[0],
                'name': row[1],
                'price': row[2],
                'quantity': row[3],
                'subtotal': row[4]
            })
        
        conn.close()
        
        order_info = {
            'orderId': order_row[0],
            'firstName': order_row[1],
            'email': order_row[2],
            'phone': order_row[3],
            'totalAmount': order_row[4],
            'orderDate': order_row[5],
            'status': order_row[6],
            'tickets': ticket_items
        }
        
        return jsonify({
            'success': True,
            'order': order_info
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'查詢訂單失敗: {str(e)}'}), 500

# 獲取所有訂單（管理用）
@tickets_bp.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT order_id, first_name, email, total_amount, 
                   order_date, status
            FROM ticket_orders
            ORDER BY order_date DESC
        ''')
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'orderId': row[0],
                'firstName': row[1],
                'email': row[2],
                'totalAmount': row[3],
                'orderDate': row[4],
                'status': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'orders': orders
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'獲取訂單列表失敗: {str(e)}'}), 500

# 更新訂單狀態
@tickets_bp.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['pending', 'paid', 'cancelled', 'refunded']:
            return jsonify({'error': '無效的狀態值'}), 400
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ticket_orders 
            SET status = ? 
            WHERE order_id = ?
        ''', (status, order_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': '找不到指定的訂單'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '訂單狀態更新成功'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'更新狀態失敗: {str(e)}'}), 500

# 獲取票種資訊
@tickets_bp.route('/types', methods=['GET'])
def get_ticket_types():
    return jsonify({
        'success': True,
        'ticketTypes': TICKET_TYPES
    }), 200

