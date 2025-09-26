import sqlite3
import os
import json
from datetime import datetime
import numpy as np
import cv2
from typing import Optional, List, Dict, Tuple

class FaceDatabase:
    def __init__(self, db_path="data/face_recognition.db"):
        """Initialize database connection."""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def reset_database(self):
        """Reset database - DROP all tables and recreate."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.init_database()
        self.populate_menu()
        print("✅ Database reset and menu populated!")
    
    def init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if this is a fresh database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='menu';")
        menu_exists = cursor.fetchone() is not None

        # Menu table - NEW
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                image_url TEXT,
                is_available BOOLEAN DEFAULT 1,
                mood_tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT UNIQUE NOT NULL,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP,
                total_visits INTEGER DEFAULT 1,
                total_purchases INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0.0,
                face_image_path TEXT,
                embedding_path TEXT,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Purchases table - UPDATED with menu_id
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                menu_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                total_price REAL NOT NULL,
                purchase_time TIMESTAMP NOT NULL,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (menu_id) REFERENCES menu (id)
            )
        ''')
        
        # Face embeddings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                embedding_path TEXT NOT NULL,
                face_image_path TEXT NOT NULL,
                confidence_score REAL,
                quality_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_primary BOOLEAN DEFAULT 0,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        # Sessions table - NEW (untuk tracking face recognition → menu)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                customer_id TEXT NOT NULL,
                status TEXT DEFAULT 'face_recognized',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        # Auto-populate menu if this is a fresh database
        if not menu_exists:
            print("🍽️ Fresh database detected, populating menu...")
            self.populate_menu()
    
    def populate_menu(self):
        """Populate menu with 5 cafe drinks."""
        menu_items = [
            {
                'name': 'Americano',
                'price': 25000,
                'description': 'Rich espresso with hot water',
                'image_url': '/static/images/americano.jpg'
            },
            {
                'name': 'Cappuccino',
                'price': 30000,
                'description': 'Espresso with steamed milk foam',
                'image_url': '/static/images/cappuccino.jpg'
            },
            {
                'name': 'Latte',
                'price': 32000,
                'description': 'Smooth espresso with steamed milk',
                'image_url': '/static/images/latte.jpg'
            },
            {
                'name': 'Cold Brew',
                'price': 28000,
                'description': 'Smooth, refreshing cold coffee',
                'image_url': '/static/images/coldbrew.jpg'
            },
            {
                'name': 'Matcha Latte',
                'price': 35000,
                'description': 'Premium matcha with steamed milk',
                'image_url': '/static/images/matcha.jpg'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in menu_items:
            cursor.execute('''
                INSERT OR REPLACE INTO menu (name, price, description, image_url)
                VALUES (?, ?, ?, ?)
            ''', (item['name'], item['price'], item['description'], item['image_url']))
        
        conn.commit()
        conn.close()
    
    def get_menu(self) -> List[Dict]:
        """Get all available menu items."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, price, description, image_url, mood_tags
            FROM menu 
            WHERE is_available = 1 
            ORDER BY name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'name', 'price', 'description', 'image_url', 'mood_tags']
        return [dict(zip(columns, row)) for row in results]
    
    def create_session(self, customer_id: str) -> str:
        """Create new session for customer."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_id}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (session_id, customer_id, status)
            VALUES (?, ?, 'face_recognized')
        ''', (session_id, customer_id))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def add_purchase(self, customer_id: str, menu_id: int, quantity: int = 1) -> bool:
        """Add purchase record with menu selection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get menu item details
            cursor.execute('SELECT name, price FROM menu WHERE id = ?', (menu_id,))
            menu_item = cursor.fetchone()
            if not menu_item:
                return False
            
            menu_name, unit_price = menu_item
            total_price = unit_price * quantity
            now = datetime.now().isoformat()
            
            # Insert purchase
            cursor.execute('''
                INSERT INTO purchases 
                (customer_id, menu_id, quantity, total_price, purchase_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, menu_id, quantity, total_price, now))
            
            # Update customer stats
            cursor.execute('''
                UPDATE customers 
                SET total_purchases = total_purchases + ?,
                    total_spent = total_spent + ?,
                    last_seen = ?
                WHERE customer_id = ?
            ''', (quantity, total_price, now, customer_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding purchase: {e}")
            return False
    
    def get_customer_purchases_with_menu(self, customer_id: str) -> List[Dict]:
        """Get customer purchases with menu details."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.customer_id, m.name as menu_name, p.quantity, 
                   p.total_price, p.purchase_time, p.created_at
            FROM purchases p
            JOIN menu m ON p.menu_id = m.id
            WHERE p.customer_id = ? 
            ORDER BY p.purchase_time DESC
        ''', (customer_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'customer_id', 'menu_name', 'quantity', 
                  'total_price', 'purchase_time', 'created_at']
        return [dict(zip(columns, row)) for row in results]
    
    # Keep all other existing methods...
    def add_customer(self, customer_id: str, face_image: np.ndarray, 
                    embedding: np.ndarray, confidence: float = 0.0) -> bool:
        """Add new customer to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save face image and embedding
            face_path = f"data/faces/{customer_id}.jpg"
            embedding_path = f"data/embeddings/{customer_id}.npy"
            
            os.makedirs("data/faces", exist_ok=True)
            os.makedirs("data/embeddings", exist_ok=True)
            
            cv2.imwrite(face_path, face_image)
            np.save(embedding_path, embedding)
            
            now = datetime.now().isoformat()
            
            # Insert customer
            cursor.execute('''
                INSERT INTO customers 
                (customer_id, first_seen, last_seen, face_image_path, embedding_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, now, now, face_path, embedding_path))
            
            # Insert face embedding
            cursor.execute('''
                INSERT INTO face_embeddings 
                (customer_id, embedding_path, face_image_path, confidence_score, is_primary)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, embedding_path, face_path, confidence, 1))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding customer: {e}")
            return False
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM customers WHERE customer_id = ? AND is_active = 1
        ''', (customer_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return None
    
    def get_all_embeddings(self) -> List[Tuple[str, np.ndarray]]:
        """Get all customer embeddings for face recognition."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT customer_id, embedding_path FROM face_embeddings 
            WHERE is_primary = 1
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        embeddings = []
        for customer_id, embedding_path in results:
            if os.path.exists(embedding_path):
                embedding = np.load(embedding_path)
                embeddings.append((customer_id, embedding))
        
        return embeddings
    
    def update_visit(self, customer_id: str):
        """Update customer last visit."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE customers 
            SET last_seen = ?, total_visits = total_visits + 1
            WHERE customer_id = ?
        ''', (now, customer_id))
        
        conn.commit()
        conn.close()
    
    def get_customer_stats(self) -> Dict:
        """Get overall customer statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total customers
        cursor.execute('SELECT COUNT(*) FROM customers WHERE is_active = 1')
        stats['total_customers'] = cursor.fetchone()[0]
        
        # Total purchases
        cursor.execute('SELECT COUNT(*) FROM purchases')
        stats['total_purchases'] = cursor.fetchone()[0]
        
        # Total revenue
        cursor.execute('SELECT SUM(total_price) FROM purchases')
        result = cursor.fetchone()[0]
        stats['total_revenue'] = result if result else 0.0
        
        # Popular menu items
        cursor.execute('''
            SELECT m.name, COUNT(p.id) as order_count, SUM(p.total_price) as revenue
            FROM purchases p
            JOIN menu m ON p.menu_id = m.id
            GROUP BY m.id, m.name
            ORDER BY order_count DESC
            LIMIT 5
        ''')
        stats['popular_items'] = cursor.fetchall()
        
        conn.close()
        return stats
    
    def get_last_purchase_item(self, customer_id: str) -> Optional[Dict]:
        """Get customer's last purchased menu item."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, m.name, m.price, m.description, m.image_url,
                p.purchase_time, p.quantity
            FROM purchases p
            JOIN menu m ON p.menu_id = m.id
            WHERE p.customer_id = ? 
            ORDER BY p.purchase_time DESC
            LIMIT 1
        ''', (customer_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'name', 'price', 'description', 'image_url', 
                    'last_purchased', 'last_quantity']
            return dict(zip(columns, result))
        return None

    def get_most_popular_item(self) -> Optional[Dict]:
        """Get most popular menu item across all customers."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, m.name, m.price, m.description, m.image_url,
                COUNT(p.id) as total_orders,
                SUM(p.quantity) as total_quantity
            FROM menu m
            LEFT JOIN purchases p ON m.id = p.menu_id
            WHERE m.is_available = 1
            GROUP BY m.id, m.name, m.price, m.description, m.image_url
            ORDER BY total_orders DESC, total_quantity DESC
            LIMIT 1
        ''', ())
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'name', 'price', 'description', 'image_url', 
                    'total_orders', 'total_quantity']
            return dict(zip(columns, result))
        return None

    def get_menu_recommendations(self, customer_id: str) -> Dict:
        """Get menu recommendations for customer."""
        return {
            'last_purchase': self.get_last_purchase_item(customer_id),
            'most_popular': self.get_most_popular_item(),
            'all_menu': self.get_menu()
        }
        