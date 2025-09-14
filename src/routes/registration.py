from flask import Blueprint, request, jsonify
#from models.user import db
import sqlite3
import os
from datetime import datetime

registration_bp = Blueprint('registration', __name__)

# 隊伍報名API
@registration_bp.route('/teams', methods=['POST'])
def register_team():
    try:
        data = request.get_json()
        
        # 驗證必要欄位
        required_fields = ['teamName', 'country', 'contactPerson', 'email', 'phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'缺少必要欄位: {field}'}), 400
        
        # 連接資料庫
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 建立隊伍報名表格（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                country TEXT NOT NULL,
                contact_person TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                players_count INTEGER,
                coach_name TEXT,
                experience_level TEXT,
                special_requirements TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # 插入報名資料
        cursor.execute('''
            INSERT INTO team_registrations 
            (team_name, country, contact_person, email, phone, players_count, 
             coach_name, experience_level, special_requirements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['teamName'],
            data['country'],
            data['contactPerson'],
            data['email'],
            data['phone'],
            data.get('playersCount', 16),
            data.get('coachName', ''),
            data.get('experienceLevel', ''),
            data.get('specialRequirements', '')
        ))
        
        team_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '隊伍報名成功！',
            'teamId': team_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'報名失敗: {str(e)}'}), 500

# 獲取所有報名隊伍
@registration_bp.route('/teams', methods=['GET'])
def get_teams():
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, team_name, country, contact_person, email, 
                   players_count, registration_date, status
            FROM team_registrations
            ORDER BY registration_date DESC
        ''')
        
        teams = []
        for row in cursor.fetchall():
            teams.append({
                'id': row[0],
                'teamName': row[1],
                'country': row[2],
                'contactPerson': row[3],
                'email': row[4],
                'playersCount': row[5],
                'registrationDate': row[6],
                'status': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'teams': teams
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'獲取隊伍資料失敗: {str(e)}'}), 500

# 更新隊伍狀態
@registration_bp.route('/teams/<int:team_id>/status', methods=['PUT'])
def update_team_status(team_id):
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['pending', 'approved', 'rejected']:
            return jsonify({'error': '無效的狀態值'}), 400
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE team_registrations 
            SET status = ? 
            WHERE id = ?
        ''', (status, team_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': '找不到指定的隊伍'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '隊伍狀態更新成功'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'更新狀態失敗: {str(e)}'}), 500

